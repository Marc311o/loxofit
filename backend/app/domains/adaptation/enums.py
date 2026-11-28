import enum


class AdjustmentReason(enum.StrEnum):
    FIRST_ESTIMATE = "first_estimate"  # the first workout with the exercise
    PROGRESSED = "progressed"  # the load goes up
    HELD = "held"  # the load stays
    REDUCED = "reduced"  # the load goes down
