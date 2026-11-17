# Code Guidelines — Runnable Listings

Governs runnable Python files under `code/chapterNN/listings/` (extracted from chapter prose by `plugins/book-judges/lib/extract_listings.py`). The doer agent and any `/apply-fixes` cycle read this. Applies to **chapter 3 and beyond**. Chapters 1-2 grandfathered.

The prose-side rules (representative code in chapter prose) live in `book/CODE_GUIDELINES_PROSE.md`.

## Rules

1. **Runnable as-is.** Every listing must `python listing.py` (or `import` cleanly) on Python 3.13.
2. **75-character line width.** Strict. Break long calls across multiple lines using parentheses; use named intermediate variables when needed.
3. **Pytest required.** Every listing has a corresponding `tests/test_NN_MM_slug.py` using the `load_listing` fixture from `code/chapterNN/conftest.py`. The doer enforces this in its pytest gate.
4. **`pyproject.toml` per chapter.** `code/chapterNN/pyproject.toml` declares deps and pytest config. uv-managed (`uv run pytest -q`).
5. **Pydantic v2 only.** Same rules as prose: `BaseModel`, `Field`, `@field_validator`, `model_dump()`, `model_dump_json()`, `model_json_schema()`. **Forbidden:** `.dict()`, `.json()`, `schema()`.
6. **Model name consistency.** `claude-sonnet-4-6` across all listings in a chapter unless explicitly varying.
7. **Type hints required** for every public function/method signature. Modern Python 3.13 syntax.
8. **`logging` not `print()`.** Listings represent application code.
9. **No silent error suppression.** No bare `except:`. `except Exception` only with justification in a comment.
10. **`pathlib.Path` for paths.** Not raw strings.
11. **No machine-specific paths, secrets, or API keys** in committed code. Use `os.getenv("ANTHROPIC_API_KEY")` etc.
12. **`if __name__ == "__main__": main()` guard** for executable scripts.
13. **No deprecated Pydantic v1 methods.**

## Directory structure per chapter

```
code/chapterNN/
├── pyproject.toml              # uv-managed, declares deps + pytest config
├── conftest.py                 # load_listing fixture
├── README.md                   # table of all listings (see below)
├── listings/
│   ├── NN-MM-slug.py
│   └── ...
└── tests/
    ├── test_NN_MM_slug.py
    └── ...
```

`code/chapter01/conftest.py` is the reference exemplar for the `load_listing` fixture.

## README.md per chapter

Every `code/chapterNN/` directory has a `README.md` with a table:

```markdown
# Chapter N listings

| File | Topic | Description | Run command |
|------|-------|-------------|-------------|
| `listings/NN-MM-slug.py` | Topic | One-line description | `uv run python listings/NN-MM-slug.py` |
```

## Banned

- Pydantic v1 methods
- `print()` for non-demo output
- Bare `except:` clauses
- Raw string paths
- Hard-coded secrets or API keys
- Machine-specific absolute paths
- Lines exceeding 75 characters
- Listings without a corresponding test
