# Contributing to WoonLens

Thank you for your interest in WoonLens. The project is in its foundation
phase, so contributions should remain small, reviewable, and linked to a clear
problem.

## Workflow

1. Search the existing issues before proposing new work.
2. Open or select one issue with a defined goal and acceptance criteria.
3. Create one branch for that issue.
4. Make focused commits and add tests or verification evidence.
5. Open a pull request that links the issue and explains the result.
6. Merge only after the documented acceptance criteria are satisfied.

An Issue is closed as completed only when the repository
[Definition of Done](docs/SOFTWARE_ENGINEERING.md#10-definition-of-done) is
satisfied. Code completion alone is not sufficient: required evidence, tests,
documentation, data provenance, security checks, and operational impact must be
addressed before merge.

## Branch naming

Use the issue number and a short description:

```text
feat/12-bag-client
fix/27-energy-label-selection
chore/1-repository-foundation
docs/31-data-provenance
```

## Commit messages

Use an imperative, scoped message where possible:

```text
feat: add BAG residential-unit lookup
fix: preserve missing EP-Online values
test: cover conflicting area definitions
docs: explain CBS attribution requirements
```

## Pull requests

A pull request should include:

- The problem being solved
- The implementation or documentation approach
- Tests and manual verification performed
- Known limitations and follow-up work
- A closing reference such as `Closes #12`

Before marking a pull request ready, review the complete diff and the Definition
of Done. Unfinished work must be represented by linked follow-up Issues; it must
not be hidden in prose or silently deferred.

## Data and privacy rules

Do not commit or post:

- API keys, access tokens, cookies, or signed URLs
- `.env` files containing real values
- Bulk exports from EP-Online or other restricted sources
- Personal information about owners, residents, or users
- Address-search logs from real users
- Third-party data without confirmed reuse terms

Use synthetic, redacted, or explicitly redistributable fixtures in tests. A
public address may be used in documentation only when necessary, with source
and purpose clearly stated.

## Source and transformation rules

Every normalized field should document:

- Original dataset and source field
- Retrieval or dataset timestamp
- Transformation and validation rules
- Missing-value behavior
- License or usage constraints

A difference between two registers must not automatically be described as an
error. Confirm whether the fields use different definitions, scopes, reference
dates, or geometries.

## Development quality

New implementation work should include automated tests appropriate to its risk.
Network clients should be tested with deterministic fixtures and a small,
explicit set of optional live integration tests. Documentation and examples
must not expose personal credentials.

## License

By contributing, you agree that your contribution may be distributed under the
repository's MIT License. Third-party datasets remain subject to their own
terms and are not relicensed by this repository.
