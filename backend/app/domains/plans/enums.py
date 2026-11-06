import enum


class PlanStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class VolumeZone(enum.StrEnum):
    BELOW_MEV = "below_mev"
    MEV_MAV = "mev_mav"
    MAV_MRV = "mav_mrv"
    ABOVE_MRV = "above_mrv"


class AnalysisSource(enum.StrEnum):
    STORED = "stored"  # all weeks exist - the saved plan, including manual edits
    PROJECTED = "projected"  # only the base week - progression computed on the fly
