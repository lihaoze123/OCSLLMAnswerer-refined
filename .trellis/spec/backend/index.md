# Backend Development Guidelines

> Best practices for backend development in this project.

---

## Overview

This directory contains guidelines for backend development. Fill in each file with your project's specific conventions.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Filled from current codebase |
| [Database Guidelines](./database-guidelines.md) | Current no-database state and future persistence constraints | Filled from current codebase |
| [Error Handling](./error-handling.md) | Error types, handling strategies | Filled from current codebase |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Filled from current codebase |
| [Logging Guidelines](./logging-guidelines.md) | Console logging helpers and sensitive-data rules | Filled from current codebase |

---

## Pre-Development Checklist

Before editing backend code in this project:

1. Read [Directory Structure](./directory-structure.md) to confirm where the
   existing single-file Flask app owns the behavior you are changing.
2. Read [Quality Guidelines](./quality-guidelines.md) for the OCS response
   contract and verification expectations.
3. Read [Error Handling](./error-handling.md) before changing request parsing,
   LLM calls, JSON parsing, or route responses.
4. Read [Logging Guidelines](./logging-guidelines.md) before adding console
   output or changing request/answer logging.
5. Read [Database Guidelines](./database-guidelines.md) before adding any
   persistence, caching, or data-retention behavior.

---

## Maintenance Notes

When updating these guidelines:

1. Document this project's **actual conventions** rather than ideals.
2. Include real file references or code examples from the codebase.
3. List forbidden patterns only when they protect an existing contract.
4. Update this index when a guideline file's scope changes.

The goal is to help AI assistants and new team members understand how this
project works today.

---

**Language**: All documentation should be written in **English**.
