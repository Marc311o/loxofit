"""Small catalog shared by engine tests."""

from app.engine.types import EngineConfig, ExerciseSpec, Role

P, S, X = Role.PRIMARY, Role.SECONDARY, Role.STABILIZER

BENCH = ExerciseSpec("bb_bench", True, {"pec_major": P, "delt_ant": S, "triceps": S}, tempo="3010")
ROW = ExerciseSpec(
    "cable_row_seated", True, {"lats": P, "trapezius": P, "delt_post": S, "biceps": S}
)
FLY = ExerciseSpec("pec_deck_fly", False, {"pec_major": P, "delt_ant": S})
CURL = ExerciseSpec("db_curl", False, {"biceps": P})
PLANK_LIKE = ExerciseSpec("ball_rollout", False, {"rect_abd": P, "erectors": X})
SHOULDER_PRESS = ExerciseSpec(
    "db_shoulder_press", True, {"delt_ant": P, "delt_mid": S, "triceps": S}
)
CLOSE_GRIP = ExerciseSpec("bb_bench_close", True, {"triceps": P, "pec_major": P, "delt_ant": S})
LEG_EXT_UNI = ExerciseSpec("leg_ext_uni", False, {"quads": P}, is_unilateral=True)

CONFIG = EngineConfig(role_weights={P: 1.0, S: 0.5})
