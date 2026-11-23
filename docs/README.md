# Documentation

System documentation generated from the code - the database schema, the API and the
error codes can't drift from what the application actually does.

| What | Where |
|---|---|
| All diagrams (architecture, generation, database) | [generated/diagrams.en.md](generated/diagrams.en.md) |
| API map | [generated/api.en.md](generated/api.en.md) |
| Error codes | [generated/errors.en.md](generated/errors.en.md) |

## Regenerating

```sh
just docs              # from the repository root
```

or directly, with the backend virtual environment:

```sh
python docs/generate.py              # everything, PDFs included
python docs/generate.py --no-render  # skip the PDFs (no Node needed)
```

Run it after changing a model, an endpoint or an error. Nothing connects to the
database - the models and the routes are read in Python. PDFs are rendered with
the Mermaid CLI through `npx`, so Node is needed for them.

## How it works

`generate.py` reads:

- **SQLAlchemy metadata** - every table, column and foreign key, drawn as Mermaid ER
  diagrams: an overview and one diagram per area (users, catalog, model configuration,
  plans, generation runs),
- **FastAPI's OpenAPI schema** - every endpoint with its method, path, auth and responses,
- **`AppError` subclasses** - every error code with its HTTP status,
- **`diagrams/*.mmd`** - hand-written Mermaid diagrams with `{{ key }}` placeholders.

Labels and descriptions come from `i18n/en.toml` and `i18n/pl.toml`. A missing translation falls back to English and is listed at the end of the run,
as is a translation of a route or an error that no longer exists.

## Layout

```
docs/
  generate.py      # the generator
  mermaid.json     # Mermaid theme and layout settings
  diagrams/        # hand-written diagram sources
  i18n/            # en.toml, pl.toml
  generated/       # output: .mmd, .md, .tex - committed, do not edit by hand
  figures/         # output: PDFs - not committed
```