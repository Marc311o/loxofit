import enum


class MuscleGroup(enum.StrEnum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    GLUTES = "glutes"
    THIGHS = "thighs"
    CALVES = "calves"


class MovementPattern(enum.StrEnum):
    HORIZONTAL_PUSH = "horizontal_push"
    VERTICAL_PUSH = "vertical_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PULL = "vertical_pull"
    SQUAT = "squat"
    HIP_HINGE = "hip_hinge"
    LUNGE = "lunge"
    HIP_EXTENSION = "hip_extension"
    KNEE_FLEXION = "knee_flexion"
    KNEE_EXTENSION = "knee_extension"
    ELBOW_FLEXION = "elbow_flexion"
    ELBOW_EXTENSION = "elbow_extension"
    SHOULDER_ABDUCTION = "shoulder_abduction"
    SHOULDER_HORIZONTAL_ABDUCTION = "shoulder_horizontal_abduction"
    CHEST_FLY = "chest_fly"
    CORE_FLEXION = "core_flexion"
    CORE_ANTI_EXTENSION = "core_anti_extension"
    CALF_RAISE = "calf_raise"
    SHOULDER_FLEXION = "shoulder_flexion"
    SHOULDER_EXTENSION = "shoulder_extension"
    SCAPULAR_ELEVATION = "scapular_elevation"
    HIP_ADDUCTION = "hip_adduction"
    HIP_ABDUCTION = "hip_abduction"
    CORE_ROTATION = "core_rotation"
    CORE_ANTI_ROTATION = "core_anti_rotation"


class MuscleRole(enum.StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    STABILIZER = "stabilizer"


class ExerciseSort(enum.StrEnum):
    NAME_EN = "name_en"
    NAME_PL = "name_pl"
    GROUP = "group"


class EquipmentSort(enum.StrEnum):
    CATEGORY = "category"
    NAME_EN = "name_en"
    NAME_PL = "name_pl"


class EquipmentCategory(enum.StrEnum):
    FREE_WEIGHTS = "free_weights"
    STATION = "station"
    CABLE = "cable"
    MACHINE = "machine"
