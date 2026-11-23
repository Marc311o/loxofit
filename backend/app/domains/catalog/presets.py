"""
Ready-made sets of equipment, so a new user ticks one card instead of twenty tiles.

Codes, not ids - ids differ between databases. A code missing from the catalog is
skipped; tests check that every code exists in the catalog file.
"""

from enum import StrEnum


class EquipmentPreset(StrEnum):
    GYM = "gym"
    HOME_BARBELL = "home_barbell"
    HOME_DUMBBELLS = "home_dumbbells"


ALL = None  # every piece of equipment in the catalog

PRESET_EQUIPMENT: dict[EquipmentPreset, tuple[str, ...] | None] = {
    EquipmentPreset.GYM: ALL,
    EquipmentPreset.HOME_BARBELL: (
        "barbell", "dumbbells", "flat_bench", "adj_bench", "squat_rack", "pullup_bar",
    ),
    EquipmentPreset.HOME_DUMBBELLS: ("dumbbells", "flat_bench", "adj_bench", "pullup_bar"),
}  # fmt: skip
