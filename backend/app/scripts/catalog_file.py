"""
Reading and validating the catalog spreadsheet - no database access.

Shared by the catalog seed (seed_catalog.py) and the engine CLI (engine_eval.py), so
both can parse the same file. Importing this module needs no .env and no database.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, TypeVar

from openpyxl import load_workbook
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.domains.catalog.enums import EquipmentCategory, MovementPattern, MuscleGroup, MuscleRole

DATA_VERSION = 1
DATA_FILE = Path(__file__).resolve().parents[2] / "data" / f"catalog_data_v{DATA_VERSION}.xlsx"


class SeedDataError(Exception):
    """File corrupted error"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} errors found in data")


# MODELS

CODE_PATTERN = r"^[a-z0-9_]+$"
Code = Annotated[str, Field(pattern=CODE_PATTERN, max_length=40)]
MuscleCode = Annotated[str, Field(pattern=CODE_PATTERN, max_length=10)]
Name100 = Annotated[str, Field(min_length=1, max_length=100)]
Name150 = Annotated[str, Field(min_length=1, max_length=150)]


class SeedRow(BaseModel):
    """Base row model"""

    model_config = ConfigDict(str_strip_whitespace=True)
    row: int = Field(default=0, exclude=True)

    @field_validator("*", mode="before")
    @classmethod
    def _blank_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class MuscleRow(SeedRow):
    code: MuscleCode
    name_en: Name100
    name_pl: Name100
    muscle_group: MuscleGroup
    is_volume_target: bool = True
    description_en: str | None = None
    description_pl: str | None = None


class EquipmentRow(SeedRow):
    code: Code
    name_en: Name100
    name_pl: Name100
    category: EquipmentCategory
    description_en: str | None = None
    description_pl: str | None = None


class ExerciseRow(SeedRow):
    code: Code
    name_en: Name150
    name_pl: Name150
    main_group: MuscleGroup
    movement_pattern: MovementPattern
    is_compound: bool
    is_unilateral: bool
    fatigue_cost: int = Field(ge=1, le=5)
    complexity: int = Field(ge=1, le=5)
    default_tempo: str | None = Field(default=None, pattern=r"^\d{4}$")
    instructions_en: str | None = None
    instructions_pl: str | None = None

    @field_validator("default_tempo", mode="before")
    @classmethod
    def _tempo_to_text(cls, value: Any) -> Any:
        if isinstance(value, int | float):
            return str(int(value)).zfill(4)
        return value


class RoleRow(SeedRow):
    exercise: Code
    muscle: MuscleCode
    role: MuscleRole


class ExerciseEquipmentRow(SeedRow):
    exercise: Code
    equipment: Code


class SubstituteRow(SeedRow):
    exercise: Code
    substitute: Code
    priority_score: int = Field(default=0, ge=0)


@dataclass
class CatalogData:
    """Validated data model"""

    muscles: list[MuscleRow]
    equipment: list[EquipmentRow]
    exercises: list[ExerciseRow]
    roles: list[RoleRow]
    exercise_equipment: list[ExerciseEquipmentRow]
    substitutes: list[SubstituteRow]


# READ DATA

RowT = TypeVar("RowT", bound=SeedRow)


def read_sheet(ws: Worksheet) -> list[tuple[int, dict[str, Any]]]:
    """Rows as: (row_num, {header: value}). Skips empty rows."""

    rows = ws.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        return []
    names = [str(h).strip() if h is not None else None for h in header]

    result = []
    for row_no, values in enumerate(rows, start=2):
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in values):
            continue
        result.append((row_no, {n: v for n, v in zip(names, values, strict=False) if n}))
    return result


def parse_sheet(wb: Workbook, name: str, model: type[RowT], errors: list[str]) -> list[RowT]:
    """Row to pydantic model. Returns error list if some were found"""
    if name not in wb.sheetnames:
        errors.append(f"File '{name}' not found")
        return []

    parsed = []
    for row_no, raw in read_sheet(wb[name]):
        try:
            parsed.append(model.model_validate({**raw, "row": row_no}))
        except ValidationError as exc:
            for err in exc.errors():
                field = ".".join(str(part) for part in err["loc"])
                value = "" if err["type"] == "missing" else f" (jest: {err['input']!r})"
                errors.append(f"{name}!{row_no} {field}: {err['msg']}{value}")
    return parsed


# VALIDATION


def _check_unique(sheet: str, rows: list[RowT], field: str, errors: list[str]) -> None:
    first_seen: dict[Any, int] = {}
    for r in rows:
        key = getattr(r, field)
        if key in first_seen:
            errors.append(
                f"{sheet}!{r.row} {field}: Duplicate '{key}' (seen in r{first_seen[key]})"
            )
        else:
            first_seen[key] = r.row


def _check_pairs(sheet: str, rows: list[RowT], fields: tuple[str, str], errors: list[str]) -> None:
    seen: dict[tuple[Any, Any], int] = {}
    for r in rows:
        pair = (getattr(r, fields[0]), getattr(r, fields[1]))
        if pair in seen:
            errors.append(f"{sheet}!{r.row}: Pair {pair} duplicated (seen in r{seen[pair]})")
        else:
            seen[pair] = r.row


def _check_ref(
    sheet: str, row: SeedRow, field: str, allowed: set[str], target: str, errors: list[str]
) -> None:
    value = getattr(row, field)
    if value not in allowed:
        errors.append(f"{sheet}!{row.row} {field}: '{value}' does not exist in {target}")


def check_references(data: CatalogData) -> list[str]:
    """Context validation"""
    errors: list[str] = []

    # Keys and names unique
    _check_unique("muscles", data.muscles, "code", errors)
    _check_unique("equipment", data.equipment, "code", errors)
    _check_unique("equipment", data.equipment, "name_en", errors)
    _check_unique("exercises", data.exercises, "code", errors)
    _check_unique("exercises", data.exercises, "name_en", errors)

    muscle_codes = {m.code for m in data.muscles}
    equipment_codes = {e.code for e in data.equipment}
    exercise_codes = {e.code for e in data.exercises}

    for r in data.roles:
        _check_ref("exercise_muscles", r, "exercise", exercise_codes, "exercises", errors)
        _check_ref("exercise_muscles", r, "muscle", muscle_codes, "muscles", errors)
    _check_pairs("exercise_muscles", data.roles, ("exercise", "muscle"), errors)

    for r in data.exercise_equipment:
        _check_ref("exercise_equipment", r, "exercise", exercise_codes, "exercises", errors)
        _check_ref("exercise_equipment", r, "equipment", equipment_codes, "equipment", errors)
    _check_pairs("exercise_equipment", data.exercise_equipment, ("exercise", "equipment"), errors)

    for r in data.substitutes:
        _check_ref("substitutes", r, "exercise", exercise_codes, "exercises", errors)
        _check_ref("substitutes", r, "substitute", exercise_codes, "exercises", errors)
        if r.exercise == r.substitute:
            errors.append(f"substitutes!{r.row}: exercise can not substitute itself")
    _check_pairs("substitutes", data.substitutes, ("exercise", "substitute"), errors)

    # Primary muscle in every exercise check
    with_primary = {r.exercise for r in data.roles if r.role == MuscleRole.PRIMARY}
    for e in data.exercises:
        if e.code not in with_primary:
            errors.append(
                f"exercises!{e.row} code: '{e.code}' no 'primary' muscle in exercise_muscles"
            )

    return errors


def load_catalog(path: Path = DATA_FILE) -> CatalogData:
    """Phase 1: Read and validate"""
    if not path.exists():
        raise SeedDataError([f"File {path} not found"])

    wb = load_workbook(path, read_only=True, data_only=True)
    errors: list[str] = []
    try:
        data = CatalogData(
            muscles=parse_sheet(wb, "muscles", MuscleRow, errors),
            equipment=parse_sheet(wb, "equipment", EquipmentRow, errors),
            exercises=parse_sheet(wb, "exercises", ExerciseRow, errors),
            roles=parse_sheet(wb, "exercise_muscles", RoleRow, errors),
            exercise_equipment=parse_sheet(wb, "exercise_equipment", ExerciseEquipmentRow, errors),
            substitutes=parse_sheet(wb, "substitutes", SubstituteRow, errors),
        )
    finally:
        wb.close()

    if not errors:
        errors = check_references(data)
    if errors:
        raise SeedDataError(errors)
    return data
