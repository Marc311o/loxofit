"""
Generates the system documentation from the code, in English and Polish.

- ERD (Mermaid) from the SQLAlchemy models: an overview and one diagram per area,
- the API map and the error codes (Markdown + LaTeX) from FastAPI's OpenAPI schema,
- the hand-written diagrams in diagrams/, with their labels filled in from i18n/<lang>.toml,
- PDFs of every diagram (Mermaid CLI), for the thesis.

    python docs/generate.py               # everything
    python docs/generate.py --no-render   # skip the PDFs (no Node needed)

Nothing connects to the database - the models and the routes are read in Python.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import tomllib

DOCS = Path(__file__).resolve().parent
BACKEND = DOCS.parent / "backend"
GENERATED = DOCS / "generated"
FIGURES = DOCS / "figures"
DIAGRAMS = DOCS / "diagrams"
LANGS = ("en", "pl")
MERMAID_CLI = "@mermaid-js/mermaid-cli@11.16.0"

sys.path.insert(0, str(BACKEND))
# Settings require these, but nothing here connects anywhere - real values (.env) win.
for name in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "JWT_SECRET"):
    os.environ.setdefault(name, "docs")

from app.core.database import Base
from app.core.errors import AppError
from app.main import app
from sqlalchemy import Column, Table
from sqlalchemy.dialects import postgresql

# Tables of the auth domain are drawn with the users - one table is not an area.
AREA_OF_DOMAIN = {"auth": "users"}
AREA_ORDER = ("users", "catalog", "model_config", "plans", "generator")
# Error codes the exception handlers produce without an AppError subclass.
HANDLER_ERRORS = (("core", 422, "VALIDATION_ERROR"),)


def load_texts() -> dict[str, dict]:
    return {
        lang: tomllib.loads((DOCS / "i18n" / f"{lang}.toml").read_text("utf-8"))
        for lang in LANGS
    }


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  {path.relative_to(DOCS)}")


# ---------------------------------------------------------------------------
# ERD
# ---------------------------------------------------------------------------


def table_areas() -> dict[str, str]:
    areas = {}
    for mapper in Base.registry.mappers:
        domain = mapper.class_.__module__.split(".")[2]  # app.domains.<domain>.models
        areas[mapper.local_table.name] = AREA_OF_DOMAIN.get(domain, domain)
    return areas


def column_type(column: Column) -> str:
    """A short, one-word type: uuid, varchar, timestamptz, enum names as they are."""
    compiled = column.type.compile(dialect=postgresql.dialect()).lower()
    compiled = compiled.replace("timestamp with time zone", "timestamptz").replace(
        "[]", "_array"
    )
    return re.sub(r"\(.*\)", "", compiled).replace(" ", "_")


def column_keys(table: Table, column: Column) -> str:
    keys = []
    if column.primary_key:
        keys.append("PK")
    if column.foreign_keys:
        keys.append("FK")
    if column.unique and not column.primary_key:
        keys.append("UK")
    return ",".join(keys)


def relationships(tables: list[Table], labels: bool = True) -> Iterator[str]:
    """parent ||--o{ child for every foreign key; one-to-one when the key is the whole PK."""
    for table in tables:
        for column in table.columns:
            for fk in column.foreign_keys:
                parent = fk.column.table.name
                one_to_one = [c.name for c in table.primary_key] == [column.name]
                parent_side = "|o" if column.nullable else "||"
                child_side = "o|" if one_to_one else "o{"
                label = column.name if labels else ""
                yield f'  {parent} {parent_side}--{child_side} {table.name} : "{label}"'


# ELK lays the entities out in layers with right-angled edges - far more compact than dagre.
ELK = "---\nconfig:\n  layout: elk\n---\n"


def erd(
    tables: list[Table],
    columns: str,
    context: set[str] = frozenset(),
    direction: str = "TB",
) -> str:
    """columns: "all", "keys" (PK/FK/UK only - the thesis figures) or "none" (the overview)."""
    lines = [ELK + "erDiagram", f"  direction {direction}"]
    for table in tables:
        shown = [
            c
            for c in table.columns
            if columns == "all" or (columns == "keys" and column_keys(table, c))
        ]
        if not shown:
            lines.append(f"  {table.name}")
            continue
        lines.append(f"  {table.name} {{")
        for column in shown:
            lines.append(
                f"    {column_type(column)} {column.name} {column_keys(table, column)}".rstrip()
            )
        lines.append("  }")
    for name in sorted(context):  # tables of other areas a key points to - name only
        lines.append(f"  {name}")
    lines.extend(sorted(set(relationships(tables, labels=columns != "none"))))
    return "\n".join(lines) + "\n"


def area_tables() -> tuple[dict[str, str], list[Table]]:
    areas = table_areas()
    return areas, [t for t in Base.metadata.sorted_tables if t.name in areas]


def area_names() -> list[str]:
    """Every area with a table: the known ones in their order, then any new one."""
    found = set(table_areas().values())
    return [a for a in AREA_ORDER if a in found] + sorted(found - set(AREA_ORDER))


def generate_erd() -> tuple[list[Path], list[Path]]:
    """(full diagrams for the Markdown page, compact ones rendered for the thesis)"""
    areas, tables = area_tables()
    overview = GENERATED / "erd-overview.mmd"
    write(overview, erd(tables, columns="none", direction="LR"))
    full, compact = [overview], [overview]
    for area in area_names():
        own = [t for t in tables if areas[t.name] == area]
        context = {
            fk.column.table.name
            for t in own
            for c in t.columns
            for fk in c.foreign_keys
            if areas[fk.column.table.name] != area
        }
        name = f"erd-{area.replace('_', '-')}"
        write(GENERATED / f"{name}.mmd", erd(own, columns="all", context=context))
        write(GENERATED / f"{name}.keys.mmd", erd(own, columns="keys", context=context))
        full.append(GENERATED / f"{name}.mmd")
        compact.append(GENERATED / f"{name}.keys.mmd")
    return full, compact


def schema_latex(t: "Texts") -> str:
    """Every column of every table - the appendix next to the compact ERD figures."""
    areas, tables = area_tables()
    head = (f"{t.get('schema.headers.column')} & {t.get('schema.headers.type')} & "
            rf"{t.get('schema.headers.keys')} & NULL \\")  # fmt: skip
    lines = [
        "% Generated by docs/generate.py - do not edit by hand.",
        r"\begin{longtable}{@{}l l l c@{}}",
        rf"\caption{{{t.get('schema.caption')}}}\label{{tab:schema}}\\",
        r"\toprule", head, r"\midrule\endfirsthead",
        r"\toprule", head, r"\midrule\endhead",
        *tex_foot(t, 4)
    ]  # fmt: skip
    for area in area_names():
        for table in (tb for tb in tables if areas[tb.name] == area):
            name = tex_escape(table.name)
            lines.append(r"\addlinespace")
            lines.append(
                rf"\multicolumn{{4}}{{@{{}}l}}{{\texttt{{\textbf{{{name}}}}}}} \\"
            )
            for column in table.columns:
                null = r"\ding{51}" if column.nullable else ""  # pifont
                col, kind = tex_escape(column.name), tex_escape(column_type(column))
                keys = column_keys(table, column)
                lines.append(
                    rf"\quad\texttt{{{col}}} & \texttt{{{kind}}} & {keys} & {null} \\"
                )
    lines.append(r"\end{longtable}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# API map and error codes
# ---------------------------------------------------------------------------


@dataclass
class Endpoint:
    name: str
    method: str
    path: str
    tag: str
    public: bool
    responses: list[str]
    summary: str


@dataclass
class Error:
    area: str
    status: int
    code: str
    detail: str


def route_name(operation_id: str, path: str, method: str) -> str:
    """The route function's name back from FastAPI's default operation id
    (`{name}{path}_{method}`, non-word characters as `_`) - the key of its description."""
    suffix = re.sub(r"\W", "_", path) + "_" + method
    return operation_id.removesuffix(suffix)


def endpoints() -> list[Endpoint]:
    spec = app.openapi()
    prefix = "/api/v1"
    found = []
    for path, operations in spec["paths"].items():
        for method, op in operations.items():
            found.append(
                Endpoint(
                    name=route_name(op["operationId"], path, method),
                    method=method.upper(),
                    path=path.removeprefix(prefix) or "/",
                    tag=op["tags"][0],
                    public="security" not in op,
                    responses=sorted(op["responses"]),
                    summary=op.get("summary", ""),
                )
            )
    return found


def errors() -> list[Error]:
    def subclasses(cls: type[AppError]) -> Iterator[type[AppError]]:
        for sub in cls.__subclasses__():
            yield sub
            yield from subclasses(sub)

    def area(cls: type) -> str:
        parts = cls.__module__.split(".")
        return parts[2] if parts[:2] == ["app", "domains"] else "core"

    found = {
        AppError.code: Error(
            "core", AppError.status_code, AppError.code, AppError.detail
        )
    }
    for cls in subclasses(AppError):
        found.setdefault(
            cls.code, Error(area(cls), cls.status_code, cls.code, cls.detail)
        )
    for err_area, status, code in HANDLER_ERRORS:
        found.setdefault(code, Error(err_area, status, code, ""))
    order = ["core", "auth", *area_names()]
    rank = {
        a: i for i, a in enumerate(order)
    }  # errors of a domain without tables go last
    return sorted(
        found.values(), key=lambda e: (rank.get(e.area, len(order)), e.status, e.code)
    )


class Texts:
    """Labels of one language; a missing translation falls back to `default` and is reported."""

    def __init__(self, lang: str, texts: dict, missing: set[str]) -> None:
        self.lang, self.texts, self.missing = lang, texts, missing

    def get(self, key: str, default: str | None = None, report: bool = True) -> str:
        node: object = self.texts
        for part in key.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, str):
            return node
        if report:
            self.missing.add(f"{self.lang}: {key}")
        return default if default is not None else key


def md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
    }  # fmt: skip
    return "".join(replacements.get(ch, ch) for ch in text)


def tex_foot(t: "Texts", columns: int) -> list[str]:
    """The bottom rule on every page; on the last one also the source line, as under the figures."""
    source = (
        rf"\multicolumn{{{columns}}}{{@{{}}l}}{{\footnotesize {t.get('source')}}} \\"
    )
    return [r"\bottomrule\endfoot", r"\bottomrule", source, r"\endlastfoot"]


def tex_path(path: str) -> str:
    # a break is allowed after every slash, so long paths wrap in a narrow column
    return (
        r"\texttt{"
        + r"/\allowbreak{}".join(tex_escape(p) for p in path.split("/"))
        + "}"
    )


def api_markdown(t: Texts, items: list[Endpoint]) -> str:
    lines = [f"# {t.get('api.title')}", "", t.get("api.intro"), ""]
    by_tag: dict[str, list[Endpoint]] = defaultdict(list)
    for e in items:
        by_tag[e.tag].append(e)
    for tag, group in by_tag.values():
        header = (
            f"| {t.get('api.headers.method')} | {t.get('api.headers.path')} "
            f"| {t.get('api.headers.description')} | {t.get('api.headers.responses')} |"
        )
        lines += [header, "|---|---|---|---|"]
        for e in group:
            desc = t.get(f"endpoints.{e.name}", e.summary, report=t.lang != "en")
            mark = " ¹" if e.public else ""
            codes = ", ".join(e.responses)
            lines.append(
                f"| `{e.method}` | `{e.path}`{mark} | {md_escape(desc)} | {codes} |"
            )
        lines.append("")
    lines += [f"¹ {t.get('api.public')}", ""]
    return "\n".join(lines)


def api_latex(t: Texts, items: list[Endpoint]) -> str:
    head = (
        f"{t.get('api.headers.method')} & {t.get('api.headers.path')} & "
        rf"{t.get('api.headers.description')} & {t.get('api.headers.responses')} \\"
    )
    columns = (
        r"@{}l >{\raggedright\arraybackslash}p{0.3\textwidth}"
        r" >{\raggedright\arraybackslash}p{0.34\textwidth} l@{}"
    )
    lines = [
        "% Generated by docs/generate.py - do not edit by hand.",
        "% Needs \\usepackage{array,longtable,booktabs}.",
        rf"\begin{{longtable}}{{{columns}}}",
        rf"\caption[{t.get('api.caption_short')}]{{{t.get('api.caption')}}}\label{{tab:api}}\\",
        r"\toprule",
        head,
        r"\midrule\endfirsthead",
        r"\toprule",
        head,
        r"\midrule\endhead",
        *tex_foot(t, 4),
    ]
    by_tag: dict[str, list[Endpoint]] = defaultdict(list)
    for e in items:
        by_tag[e.tag].append(e)
    for i, (tag, group) in enumerate(by_tag.items()):
        if i:
            lines.append(r"\addlinespace")
        title = tex_escape(t.get(f"api.tags.{tag}", tag))
        lines.append(rf"\multicolumn{{4}}{{@{{}}l}}{{\textbf{{{title}}}}} \\")
        for e in group:
            desc = tex_escape(
                t.get(f"endpoints.{e.name}", e.summary, report=t.lang != "en")
            )
            mark = r"$^{*}$" if e.public else ""
            codes = ", ".join(
                r for r in e.responses if r != "422"
            )  # validation - on almost all
            lines.append(
                rf"\texttt{{{e.method}}} & {tex_path(e.path)}{mark} & {desc} & {codes} \\"
            )
    lines.append(r"\end{longtable}")
    return "\n".join(lines) + "\n"


def errors_markdown(t: Texts, items: list[Error]) -> str:
    lines = [f"# {t.get('errors.title')}", "", t.get("errors.intro"), "",
             f"| {t.get('errors.headers.code')} | HTTP | {t.get('errors.headers.description')} |",
             "|---|---|---|"]  # fmt: skip
    for e in items:
        desc = t.get(f"errors.codes.{e.code}", e.detail, report=t.lang != "en")
        lines.append(f"| `{e.code}` | {e.status} | {md_escape(desc)} |")
    return "\n".join(lines) + "\n"


def errors_latex(t: Texts, items: list[Error]) -> str:
    lines = [
        "% Generated by docs/generate.py - do not edit by hand.",
        r"\begin{longtable}{@{}l c >{\raggedright\arraybackslash}p{0.5\textwidth}@{}}",
        rf"\caption{{{t.get('errors.caption')}}}\label{{tab:api-errors}}\\",
        r"\toprule",
        rf"{t.get('errors.headers.code')} & HTTP & {t.get('errors.headers.description')} \\",
        r"\midrule\endfirsthead",
        r"\toprule",
        rf"{t.get('errors.headers.code')} & HTTP & {t.get('errors.headers.description')} \\",
        r"\midrule\endhead",
        *tex_foot(t, 3),
    ]
    for e in items:
        desc = tex_escape(
            t.get(f"errors.codes.{e.code}", e.detail, report=t.lang != "en")
        )
        lines.append(rf"\texttt{{{tex_escape(e.code)}}} & {e.status} & {desc} \\")
    lines.append(r"\end{longtable}")
    return "\n".join(lines) + "\n"


def generate_api(texts: dict[str, dict], missing: set[str]) -> None:
    items, errs = endpoints(), errors()
    for lang in LANGS:
        t = Texts(lang, texts[lang], missing)
        write(GENERATED / f"api.{lang}.md", api_markdown(t, items))
        write(GENERATED / f"api.{lang}.tex", api_latex(t, items))
        write(GENERATED / f"errors.{lang}.md", errors_markdown(t, errs))
        write(GENERATED / f"errors.{lang}.tex", errors_latex(t, errs))
        write(GENERATED / f"schema.{lang}.tex", schema_latex(t))
    # translations that point at nothing - a renamed route or a removed error
    names = {e.name for e in items}
    codes = {e.code for e in errs}
    for lang in LANGS:
        for name in texts[lang].get("endpoints", {}):
            if name not in names:
                missing.add(f"{lang}: endpoints.{name} - no such route")
        for code in texts[lang].get("errors", {}).get("codes", {}):
            if code not in codes:
                missing.add(f"{lang}: errors.codes.{code} - no such error")


# ---------------------------------------------------------------------------
# Hand-written diagrams
# ---------------------------------------------------------------------------

PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def generate_diagrams(texts: dict[str, dict], missing: set[str]) -> list[Path]:
    paths = []
    for source in sorted(DIAGRAMS.glob("*.mmd")):
        template = source.read_text("utf-8")
        for lang in LANGS:
            labels = Texts(lang, texts[lang], missing)
            prefix = f"diagrams.{source.stem}"
            text = PLACEHOLDER.sub(
                lambda m, labels=labels, prefix=prefix: labels.get(
                    f"{prefix}.{m.group(1)}"
                ),
                template,
            )
            path = GENERATED / f"{source.stem}.{lang}.mmd"
            write(path, text)
            paths.append(path)
    return paths


def diagrams_page(
    texts: dict[str, dict], erds: list[Path], diagrams: list[Path]
) -> None:
    """All English diagrams on one Markdown page - GitHub renders Mermaid blocks."""
    t = Texts("en", texts["en"], set())
    lines = ["# " + t.get("page.title"), "", t.get("page.intro"), ""]
    for path in [p for p in diagrams if p.name.endswith(".en.mmd")] + erds:
        key = path.name.removesuffix(".mmd").removesuffix(".en")
        lines += [f"## {t.get(f'page.sections.{key}', key)}", "", "```mermaid",
                  path.read_text("utf-8").rstrip(), "```", ""]  # fmt: skip
    write(GENERATED / "diagrams.en.md", "\n".join(lines))


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def mermaid_command() -> list[str] | None:
    if exe := shutil.which("mmdc"):
        return [exe]
    if npx := shutil.which("npx"):
        return [npx, "--yes", MERMAID_CLI]
    return None


def render(paths: list[Path]) -> None:
    command = mermaid_command()
    if command is None:
        print("! Mermaid CLI not found (needs Node: npx) - PDFs skipped")
        return
    config = DOCS / "mermaid.json"
    for path in paths:
        if path.name.endswith(".en.mmd"):
            continue  # the thesis is in Polish; English diagrams live on the Markdown page
        out = FIGURES / (path.name.split(".")[0] + ".pdf")
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                *command,
                "-i",
                str(path),
                "-o",
                str(out),
                "--pdfFit",
                "-c",
                str(config),
                "-q",
            ],
            check=True,
        )
        print(f"  {out.relative_to(DOCS)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--no-render", action="store_true", help="skip the PDFs")
    args = parser.parse_args()

    texts, missing = load_texts(), set()
    print("ERD")
    erds, compact_erds = generate_erd()
    print("API")
    generate_api(texts, missing)
    print("Diagrams")
    diagrams = generate_diagrams(texts, missing)
    diagrams_page(texts, erds, diagrams)
    if not args.no_render:
        print("PDF")
        render(compact_erds + diagrams)
    if missing:
        print(f"\n! {len(missing)} missing or stale translation(s):")
        for item in sorted(missing):
            print(f"  {item}")


if __name__ == "__main__":
    main()
