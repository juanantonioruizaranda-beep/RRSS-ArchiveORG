# Code standards

These rules apply to **all new code** in RSS-ArchiveORG. Follow them on every change to
keep the codebase maintainable and avoid spaghetti code.

## 1. One responsibility per module

Before adding code, identify the correct layer (see `docs/ARCHITECTURE.md`):

- CLI / configuration / orchestration / HTTP / parsing / I/O stay separate.
- If a function does two unrelated things, split it.

## 2. Prefer dataclasses over loose dicts

Use typed models in `models.py` (or domain-specific modules) for structured data.
Convert to dicts only at serialization boundaries (`to_dict()` for JSON/CSV).

## 3. Keep `cli.py` thin

The CLI should:

- Parse arguments → `RunConfig`
- Validate paths exist
- Call `pipeline.run_batch()`
- Write output via `io.py`

No HTTP logic, no BeautifulSoup, no retry loops in `cli.py`.

## 4. No duplicated logic

- Shared constants live next to the module that uses them, or in a dedicated module if
  used by multiple packages.
- Do not copy-paste tests across files; one test per behavior.

## 5. Security by default

Every change that touches I/O or network code must consider:

- Are secrets logged? (must not be)
- Are secrets committed? (must not be; use `.gitignore`)
- Is user input validated before use?
- Does the HTTP client inherit unexpected env proxies? (must not; `trust_env=False`)

See `docs/SECURITY.md` for details.

## 6. Error messages

- Include context (file line numbers for parse errors, site URL for fetch errors).
- Do not include proxy passwords or full proxy URLs with credentials in errors/logs.

## 7. Tests

- Add or update unit tests for new behavior.
- Use fake credentials and example IPs (`203.0.113.x` TEST-NET) in tests.
- Run `pytest` before opening a PR.

## 8. Documentation

When adding a feature:

1. Update `README.md` if user-facing (CLI flags, setup).
2. Update `docs/ARCHITECTURE.md` if module boundaries change.
3. Update `docs/SECURITY.md` if secrets, network, or validation behavior changes.

## 9. Style

- Match existing code: type hints, docstrings on public functions/classes.
- Minimal comments; code should read clearly.
- No drive-by refactors unrelated to the task.

## Pull request checklist

- [ ] Code lives in the correct module/layer
- [ ] No secrets in git
- [ ] Tests added/updated and passing
- [ ] Relevant docs updated
- [ ] No duplicate logic introduced
