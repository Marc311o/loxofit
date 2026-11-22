import enum


class GenerationStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


ACTIVE_STATUSES = (GenerationStatus.QUEUED, GenerationStatus.RUNNING)


class SplitTemplate(enum.StrEnum):
    """A preset of session focuses, or CUSTOM - the user sets the focus of every session."""

    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    CUSTOM = "custom"
