import enum


class WorkoutStatus(enum.StrEnum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    ABANDONED = "abandoned"  # started and given up - the session stays in the queue
    SKIPPED = "skipped"  # never started, closed with its week - the session leaves the queue
