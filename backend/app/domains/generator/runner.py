"""
Runs generations in the background, in worker processes.

The search is CPU-bound, so it runs in a process pool - the server keeps answering
requests and several users can generate at once. The worker reports its progress
into a shared dictionary (a multiprocessing manager), which GET requests read while
the run is in progress; the outcome goes to the database when the worker finishes.

In tests the runner gets a thread pool, a plain dict and the test's session.
"""

import asyncio
import logging
import multiprocessing
import uuid
from collections.abc import Callable, MutableMapping, Sequence
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from multiprocessing.managers import SyncManager
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.generator.enums import GenerationStatus
from app.domains.generator.repository import GenerationRepository
from app.domains.generator.schemas import GenerationProgress
from app.engine.generator import GenerationResult, GenerationTask, generate
from app.engine.optimizers import Progress

logger = logging.getLogger(__name__)

ProgressStore = MutableMapping[str, tuple[int, int, float | None]]
SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]

HISTORY_POINTS = 300  # improvements kept for the convergence chart


def work(task: GenerationTask, progress: ProgressStore, key: str) -> GenerationResult:
    """The generation itself - runs in a worker process."""

    def report(p: Progress) -> None:
        progress[key] = (p.evaluations, p.budget, p.best_score)

    return generate(task, report)


def thin(history: Sequence[tuple[int, float]], limit: int = HISTORY_POINTS) -> list[list[float]]:
    """At most `limit` evenly spread points, always with the first and the last one."""
    if len(history) <= limit:
        picked = list(history)
    else:
        step = (len(history) - 1) / (limit - 1)
        picked = [history[round(i * step)] for i in range(limit)]
    return [[evaluations, score] for evaluations, score in picked]


def _now() -> datetime:
    return datetime.now(UTC)


class GenerationRunner:
    def __init__(
        self,
        executor: Executor,
        progress: ProgressStore,
        session_factory: SessionFactory,
        manager: SyncManager | None = None,
    ) -> None:
        self._executor = executor
        self._progress = progress
        self._session = session_factory
        self._manager = manager
        self._tasks: set[asyncio.Task[None]] = set()

    @classmethod
    def in_processes(cls, workers: int, session_factory: SessionFactory) -> "GenerationRunner":
        # spawn - a clean interpreter on every OS, nothing inherited from the server
        context = multiprocessing.get_context("spawn")
        manager = context.Manager()
        executor = ProcessPoolExecutor(max_workers=workers, mp_context=context)
        return cls(executor, manager.dict(), session_factory, manager)

    def start(self, run_id: uuid.UUID, task: GenerationTask, exercise_ids: Sequence[int]) -> None:
        """Runs the task in the background; `exercise_ids[i]` is the exercise at index i."""
        self._progress[str(run_id)] = (0, task.budget, None)
        background = asyncio.create_task(self._run(run_id, task, tuple(exercise_ids)))
        self._tasks.add(background)  # keep a reference until it is done
        background.add_done_callback(self._tasks.discard)

    def progress(self, run_id: uuid.UUID) -> GenerationProgress | None:
        value = self._progress.get(str(run_id))
        if value is None:
            return None
        evaluations, budget, best = value
        return GenerationProgress(evaluations=evaluations, budget=budget, best_score=best)

    async def join(self) -> None:
        """Waits for every run started so far (tests, shutdown)."""
        await asyncio.gather(*list(self._tasks), return_exceptions=True)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        if self._manager is not None:
            self._manager.shutdown()

    async def _run(self, run_id: uuid.UUID, task: GenerationTask, ids: tuple[int, ...]) -> None:
        key = str(run_id)
        try:
            await self._set(run_id, status=GenerationStatus.RUNNING, started_at=_now())
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(self._executor, work, task, self._progress, key)
            await self._set(
                run_id,
                status=GenerationStatus.DONE,
                finished_at=_now(),
                evaluations=result.evaluations,
                score=result.score,
                max_score=result.max_score,
                result=[[[ids[i], sets] for i, sets in session] for session in result.sessions],
                history=thin(result.history),
            )
        except Exception as exc:
            logger.exception("Generation %s failed", run_id)
            await self._set(
                run_id,
                status=GenerationStatus.FAILED,
                finished_at=_now(),
                error=str(exc) or type(exc).__name__,
            )
        finally:
            self._progress.pop(key, None)

    async def _set(self, run_id: uuid.UUID, **values: Any) -> None:
        async with self._session() as db:
            await GenerationRepository(db).set(run_id, **values)
            await db.commit()


def get_runner(request: Request) -> GenerationRunner:
    return request.app.state.generator


RunnerDep = Annotated[GenerationRunner, Depends(get_runner)]
