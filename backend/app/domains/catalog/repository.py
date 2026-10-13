from collections.abc import Sequence

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.catalog.enums import EquipmentSort, ExerciseSort
from app.domains.catalog.models import Equipment, Exercise, ExerciseMuscleRole, Muscle
from app.domains.catalog.schemas import EquipmentFilters, ExerciseFilters


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _search(text: str, *columns: ColumnElement[str]) -> ColumnElement[bool]:
    term = f"%{_escape_like(text.strip())}%"
    return or_(*(column.ilike(term, escape="\\") for column in columns))


class CatalogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_muscles(self) -> Sequence[Muscle]:
        stmt = select(Muscle).order_by(Muscle.muscle_group, Muscle.name_en)
        return (await self.db.execute(stmt)).scalars().all()

    async def list_equipment(self, filters: EquipmentFilters) -> Sequence[Equipment]:
        stmt = select(Equipment)
        if filters.category is not None:
            stmt = stmt.where(Equipment.category == filters.category)
        if filters.search:
            stmt = stmt.where(_search(filters.search, Equipment.name_en, Equipment.name_pl))

        order_by = {
            EquipmentSort.CATEGORY: (Equipment.category, Equipment.name_en),
            EquipmentSort.NAME_EN: (Equipment.name_en,),
            EquipmentSort.NAME_PL: (Equipment.name_pl,),
        }[filters.sort]
        result = await self.db.execute(stmt.order_by(*order_by, Equipment.id))
        return result.scalars().all()

    async def list_exercises(self, filters: ExerciseFilters) -> tuple[Sequence[Exercise], int]:

        stmt = self._apply_filters(select(Exercise), filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self.db.execute(count_stmt)).scalar_one())

        page_stmt = (
            self._apply_sort(stmt, filters.sort)
            .offset(filters.offset)
            .limit(filters.size)
            .options(selectinload(Exercise.equipment))
        )
        items = (await self.db.execute(page_stmt)).scalars().all()
        return items, total

    async def get_exercise_detail(self, exercise_id: int) -> Exercise | None:
        stmt = (
            select(Exercise)
            .where(Exercise.id == exercise_id)
            .options(
                selectinload(Exercise.muscle_roles).joinedload(ExerciseMuscleRole.muscle),
                selectinload(Exercise.equipment),
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    def _apply_filters(
        stmt: Select[tuple[Exercise]], filters: ExerciseFilters
    ) -> Select[tuple[Exercise]]:
        if filters.muscle_group is not None:
            stmt = stmt.where(Exercise.main_group == filters.muscle_group)
        if filters.pattern is not None:
            stmt = stmt.where(Exercise.movement_pattern == filters.pattern)
        if filters.muscle_id is not None:
            stmt = stmt.where(
                Exercise.muscle_roles.any(ExerciseMuscleRole.muscle_id == filters.muscle_id)
            )
        if filters.equipment_id is not None:
            stmt = stmt.where(Exercise.equipment.any(Equipment.id == filters.equipment_id))
        if filters.search:
            stmt = stmt.where(_search(filters.search, Exercise.name_en, Exercise.name_pl))
        return stmt

    @staticmethod
    def _apply_sort(stmt: Select[tuple[Exercise]], sort: ExerciseSort) -> Select[tuple[Exercise]]:
        order_by = {
            ExerciseSort.NAME_EN: (Exercise.name_en,),
            ExerciseSort.NAME_PL: (Exercise.name_pl,),
            ExerciseSort.GROUP: (Exercise.main_group, Exercise.name_en),
        }[sort]
        return stmt.order_by(*order_by, Exercise.id)
