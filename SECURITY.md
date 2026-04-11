# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | Yes       |

## Reporting a Vulnerability

Please do **not** open a public issue for security vulnerabilities.

Report them by opening a [GitHub Security Advisory](../../security/advisories/new) or by contacting the maintainer directly via the GitHub profile.

Include: description, steps to reproduce, and potential impact. Expect a response within 72 hours.

## Token Security

This project uses a `GITHUB_TOKEN` (provided automatically by GitHub Actions) and optionally a `PERSONAL_GITHUB_TOKEN` for committing results back to the repository.

- Never hardcode tokens in source files or config
- Store secrets as GitHub Actions repository secrets only
- The token scope needed is `contents: write` for committing updated paper data
