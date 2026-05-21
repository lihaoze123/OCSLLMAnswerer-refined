# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

This project currently has no database, ORM, migrations, persistent storage, or
repository layer. Requests are handled statelessly: `/search` receives the OCS
payload, calls an OpenAI-compatible chat completions API, cleans/parses the
model output, and returns JSON.

Do not introduce persistence as an incidental implementation detail. Any future
database/cache addition should be designed explicitly because it changes privacy,
deployment, error handling, and test expectations.

---

## Query Patterns

No query patterns exist yet.

If persistence is added later:

- Keep data-access code out of Flask route functions.
- Treat request payloads, model prompts, model responses, and API keys as
  sensitive by default.
- Avoid storing raw question/answer traffic unless the feature explicitly needs
  it and the README/disclaimer are updated accordingly.
- Define cache keys and invalidation rules before adding answer caching.

---

## Migrations

No migration tooling exists. `pyproject.toml` has runtime dependencies for Flask,
OpenAI-compatible API access, dotenv loading, regex support, and colorized
console output, but no database driver or migration library.

If a database is introduced, add the migration tool and the first migration in
the same task, and document the command to create/apply migrations here.

---

## Naming Conventions

No table or column naming conventions exist because there is no schema.

Future schema names should be chosen after the domain model is clear. Preserve
the existing external OCS field names (`title`, `options`, `type`, `answer`,
`analysis`) at the API boundary even if internal table/column names differ.

---

## Common Mistakes

- Do not add hidden local files such as SQLite databases to the runtime path
  without documenting backup, cleanup, and `.gitignore` behavior.
- Do not log or persist `OPENAI_API_KEY`, raw Authorization headers, or full
  environment dumps.
- Do not let persistence failures break the basic stateless answer flow unless
  persistence is required for the requested feature.
