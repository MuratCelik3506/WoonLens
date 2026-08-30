# ADR 0008: Issue-Driven Pull Request Workflow

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens is initially maintained by one developer, but its data, security, and
architectural decisions require traceability. Direct work on the default branch
would make it difficult to connect a change to its problem, acceptance criteria,
and verification evidence.

The workflow must preserve that traceability without introducing approval
rituals that provide no value to a solo maintainer.

## Decision

WoonLens will use an Issue-driven, one-branch, one-pull-request workflow.

```text
Backlog -> Ready -> In Progress -> In Review -> Done
```

An Issue is the unit of planned work. A pull request is the unit of reviewed and
merged change.

## Issue Contract

Implementation begins only when an Issue contains:

- Problem
- Goal
- Scope
- Out of scope
- Verifiable acceptance criteria
- Verification plan
- Dependencies or blockers
- Data, privacy, licensing, and security impact where applicable

An Issue should describe the required outcome rather than prescribe incidental
implementation details unless those details are an accepted architectural
constraint.

Large outcomes are split into independently verifiable child Issues. No more
than two Issues should normally be in progress for one maintainer.

Sensitive vulnerabilities are handled through the private security-reporting
process and are not opened as public Issues.

## Issue Types

Initial Issue templates cover:

- Feature
- Bug
- Data-source integration
- Architecture decision
- Documentation or maintenance

Labels describe type, area, priority, status exceptions, and contribution
suitability. Milestones describe delivery outcomes rather than departments or
technical layers.

## Branches

Each Issue receives one branch created from the current default branch:

```text
feat/12-pdok-client
fix/27-label-selection
docs/31-data-provenance
chore/1-repository-foundation
```

The structure is `<type>/<issue-number>-<short-description>`. Common types are
`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, and `security` when the branch
name itself does not disclose a sensitive vulnerability.

Unrelated changes are moved to another Issue and branch. Branches are deleted
after merge.

## Commits

Commit subjects use an imperative conventional prefix:

```text
feat: add PDOK lookup adapter
fix: preserve missing CBS observations
test: cover EP-Online rate limiting
docs: explain station-level measurements
```

Commits remain focused and buildable where practical. A commit must not include
credentials, restricted data, generated local artifacts, or unrelated cleanup.

## Pull Request Contract

Every pull request:

- Solves one primary Issue.
- Links it with `Closes #<issue-number>` when merge should close it.
- Explains the problem and resulting behaviour.
- Summarizes the implementation approach.
- Records automated and manual verification.
- Identifies risks, limitations, and follow-up work.
- Discloses data, privacy, licensing, security, migration, and operational
  impact.
- Includes documentation changes when public or contributor behaviour changes.
- Receives a full self-review before being marked ready.

Draft pull requests may be used for early CI or design visibility but are not
mergeable.

## Merge Policy

- All required CI checks pass.
- Acceptance criteria are satisfied or explicitly moved to follow-up Issues
  without misrepresenting the original outcome.
- Review conversations are resolved.
- The branch is current with the required merge base policy.
- `Squash and merge` is the normal merge strategy.
- The squash title follows the repository commit-message convention.
- The source branch is deleted after merge.

Emergency bypass requires a written reason and a follow-up Issue restoring any
skipped verification. Convenience is not an emergency.

## Default Branch Protection

The default branch will enforce:

- Pull requests for changes
- Required CI status checks
- Conversation resolution
- Protection from force pushes
- Protection from branch deletion
- Required up-to-date branch state where supported without unsafe merge races

While the project has one maintainer, an approval is not required because the
author cannot provide an independent review. The pull request and self-review
remain mandatory. When another active contributor joins, protection is updated
to require at least one independent approval for application and infrastructure
changes.

Direct pushes are reserved for GitHub or recovery conditions that cannot use a
pull request and must be documented.

## Milestones

Initial milestones are:

1. `v0.1 — Repository Foundation`
2. `v0.2 — CLI Live Property View`
3. `v0.3 — Comparison Engine`
4. `v0.4 — Comparison Downloads`
5. `v0.5 — Web Application`
6. `v1.0 — First Public Release`

An Issue belongs to the milestone whose exit criteria it advances. A milestone
is complete only when its documented outcome is demonstrable, not merely when
all original Issues are closed.

## Consequences

### Positive

- Every merged change has problem, scope, and verification history.
- Solo work remains reviewable without fake approval ceremony.
- Milestones connect technical tasks to product outcomes.
- Future contributors inherit an established workflow.

### Costs

- Even small changes require an Issue and pull request unless covered by a
  narrowly documented exception.
- The maintainer must keep Issue state and acceptance criteria current.
- Squashing removes intermediate commits from the default branch, though they
  remain visible in pull-request history.

## Rejected Alternatives

### Direct commits to the default branch

Rejected because they bypass scope, CI, review context, and automatic Issue
closure.

### Mandatory self-approval

Rejected because it is not independent review and may be impossible under
GitHub's review rules.

### One long-lived development branch

Rejected because unrelated work becomes coupled and difficult to review or
release independently.

## Revisit Conditions

Approval count, ownership rules, merge queues, and release branches should be
revisited when the contributor count, merge frequency, or release model changes.
