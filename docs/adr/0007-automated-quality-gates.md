# ADR 0007: Automated Quality Gates

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens requires consistent formatting, strict typing, enforced architecture,
deterministic tests, secure dependency handling, secret protection, and a
reproducible container build. Relying on manual review for all of these concerns
would be inconsistent and would make a solo maintainer repeatedly check routine
properties by hand.

Local tools and CI must enforce the same rules so a pull request does not reveal
avoidable failures only after code is pushed.

## Decision

WoonLens will use automated local and continuous-integration quality gates.

| Concern | Tool |
| --- | --- |
| Python formatting and linting | Ruff |
| Static type checking | mypy in strict mode |
| Architecture boundaries | import-linter |
| Tests and coverage | pytest, pytest-cov, coverage.py |
| Dependency vulnerability audit | pip-audit |
| Secret detection | gitleaks |
| Dockerfile linting | hadolint |
| GitHub Actions linting | actionlint |
| Markdown consistency | markdownlint |
| Local staged-file checks | pre-commit |
| Dependency update proposals | Dependabot |

## Required Pull-Request Pipeline

The required CI path is:

```text
lock-file validation
  -> formatting
  -> lint
  -> strict type check
  -> architecture contracts
  -> unit and source-contract tests
  -> integration tests
  -> coverage threshold
  -> dependency audit
  -> secret scan
  -> Docker build and smoke test
```

Independent jobs may execute concurrently, but all required results must pass
before merge.

Documentation, workflow, and Docker-specific checks run only when relevant
files change where path filtering is safe. Security and secret checks must not
be skipped merely because a change appears documentation-only.

## Python Quality Rules

- Ruff is the single Python formatter and primary linter.
- Formatter output is authoritative; manual formatting preferences do not
  override it.
- mypy runs in strict mode for first-party application code.
- Dynamically typed provider payloads are validated at adapter boundaries before
  entering typed application code.
- `import-linter` encodes the dependency rules established by ADR 0001.
- Generated files, migrations, or integration shims may receive scoped rules
  only when the exception is documented.

## Suppression Policy

Suppressions such as `# noqa`, `# type: ignore`, per-file ignores, coverage
exclusions, skipped tests, or audit ignores must be:

- As narrow as possible
- Accompanied by a reason when the tool syntax permits
- Linked to an Issue when temporary
- Reviewed like executable code
- Removed when the underlying limitation is resolved

Broad directory exclusions and global weakening of a rule require a documented
engineering decision. A quality threshold is not lowered solely to make a pull
request pass.

## Security Gates

- `gitleaks` scans the repository and pull-request changes for credential
  patterns.
- `pip-audit` evaluates the locked Python dependency set against known
  vulnerability advisories.
- Audit exceptions require the advisory identifier, exposure analysis,
  mitigation, owner, and expiry or review date.
- Personal credentials are not supplied to required pull-request jobs.
- GitHub Actions dependencies are pinned to immutable commit SHAs where
  practical, with a comment identifying the human-readable release.
- CI job permissions use least privilege and are declared explicitly.
- Untrusted pull-request code must not receive repository secrets.

## Container Gate

CI builds the supported Docker target and verifies at least:

- The image builds from the committed lock file.
- The runtime process uses a non-root user.
- The container starts with safe test configuration.
- The health endpoint or command reaches the expected ready state.
- Startup with invalid required configuration fails safely.
- Build context does not include `.env`, local data, caches, or credentials.

Hadolint supplements this gate by finding common Dockerfile mistakes; it does
not replace runtime verification.

## Local Workflow

Pre-commit runs fast checks on staged files, including formatting, linting,
secret detection, and basic file hygiene. Slower integration and container
checks remain available through the same documented project commands and run in
CI.

Skipping a local hook does not bypass CI. CI is the merge authority.

## Dependency Updates

Dependabot proposes grouped and scheduled dependency updates. Update pull
requests pass through the same tests, audits, and build checks as application
changes. Automatic creation of a PR does not imply automatic approval or merge.

## Supported Runtime Matrix

The initial project supports Python 3.13 only. CI does not run speculative
multi-version matrices. Additional Python versions require an explicit support
decision and corresponding test matrix.

## Reproducible Commands

CI must invoke repository-owned commands that developers can run locally. CI
workflow files must not contain unique test or lint logic unavailable through
the normal project tooling.

The eventual command interface should provide cohesive targets equivalent to:

```text
format
lint
typecheck
test
test-integration
security
check
```

The exact runner is selected during project scaffolding; the behaviour is the
contract.

## Consequences

### Positive

- Routine quality properties are consistent and repeatable.
- Review can focus on correctness, product behaviour, and data meaning.
- Architecture and secret rules remain enforceable as the project grows.
- Container failures are detected before merge.

### Costs

- The initial toolchain and CI require configuration and maintenance.
- Strict typing and architecture gates may expose friction at third-party
  boundaries.
- Security advisories and automated updates require timely triage.

## Rejected Alternatives

### Manual review only

Rejected because formatting, typing, import boundaries, secrets, and known
advisories are more consistently checked by automation.

### A single all-purpose lint command without distinct gates

Rejected because separate results make failures easier to diagnose and permit
safe parallel execution.

### Automatic dependency update merges

Rejected for the initial project because provider, report, and persistence
behaviour must be verified before accepting changes.

## Revisit Conditions

Tools may be consolidated when one tool fully replaces another without reducing
coverage. Required gates and suppression discipline remain unless a documented
risk assessment changes them.
