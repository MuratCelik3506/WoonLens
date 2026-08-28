# Security Policy

## Project status

WoonLens is currently in early development and has no supported production
release. Security-sensitive findings are still important, especially those
involving credentials, data redistribution, request logging, or generated
reports.

## Reporting a vulnerability

Do not open a public GitHub issue for a vulnerability that could expose:

- API keys, tokens, cookies, or signed URLs
- Personal or user-submitted address data
- Private infrastructure details
- Restricted bulk source data
- A practical method for abusing an upstream public-data service

Use GitHub's private vulnerability reporting feature when it is available for
this repository. If it is not available, contact the repository maintainer
privately through their GitHub profile and establish a private reporting
channel before sharing sensitive details.

For non-sensitive bugs, open a normal GitHub issue with reproducible steps and
redacted examples.

## Credential exposure

If a real credential is committed or posted:

1. Revoke or rotate it immediately at the issuing service.
2. Remove it from the current repository state.
3. Review logs and usage for unauthorized access.
4. Treat Git history cleanup as secondary; deletion from a branch does not make
   an exposed credential safe again.

Never include a real secret in an issue, pull request, screenshot, fixture,
example response, or generated report.

## Supported versions

There are no supported releases yet. This section will be updated when the
first tagged version is published.
