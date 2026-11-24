"""Equipment presets refer to equipment by code - every code must exist in the catalog."""

from app.domains.catalog.presets import PRESET_EQUIPMENT
from app.seeds.catalog_file import load_catalog


def test_preset_codes_exist_in_the_catalog_file():
    codes = {row.code for row in load_catalog().equipment}
    for preset, preset_codes in PRESET_EQUIPMENT.items():
        assert set(preset_codes or ()) <= codes, preset
