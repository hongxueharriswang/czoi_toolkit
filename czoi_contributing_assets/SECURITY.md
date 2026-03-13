# Security Policy

We take the security of **CZOI Toolkit** seriously. If you discover a vulnerability, please follow the steps below **instead of** filing a public issue.

## Reporting a Vulnerability

- **Private Advisory (preferred):** Submit a report using GitHub’s private Security Advisory workflow for this repository:
  - https://github.com/hongxueharriswang/czoi_toolkit/security/advisories/new
- **Email (fallback):** If the advisory flow is unavailable, contact the maintainer privately at: **security@czoi.dev** (placeholder). Do not include exploit details in public channels.

Please include:
- A description of the vulnerability and its impact
- Steps to reproduce or a proof of concept
- Affected versions/commit(s) if known
- Any possible mitigations or workarounds

We will acknowledge your report within **3 business days** and provide a timeline for remediation after initial triage.

## Supported Versions
Until 1.0.0, we support the **latest released minor** (e.g., 0.1.x). After 1.0.0, we will support the latest **two** minor versions.

## Coordinated Disclosure
Once a fix is available, we will coordinate a disclosure date with you. Please do not disclose the issue publicly until an advisory and a patched release are published.

## Areas of Special Care
Contributions that touch the following areas must include a security review in the PR description and negative tests:
- `czoi.utils.safe_eval`
- Permission calculus in `czoi.permission`
- Access constraints and enforcement in `czoi.constraint`
- Daemon actions that allow/deny or block activity (`czoi.daemon`)
- Storage adapters and migrations (`czoi.storage`)
