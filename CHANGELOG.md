# Changelog

User-facing changes are recorded here. Version numbers describe changes to this Skill package and its utilities, not the capabilities of the host model.

## 1.1.0 — 2026-11-10

### Changed

- Refined translation guidance and focused reference loading, including explicit user preferences, structured content, and source-text instruction boundaries.
- Improved package validation and deterministic translation checks, with regression coverage and clearer limitations.
- Reworked Chinese documentation and added an English README, contribution guide, security policy, community guidelines, and issue/PR templates.
- Distinguished package tests, model evaluation fixtures, and actual observed translation results throughout the documentation.

### Added

- Host UI metadata for Skill discovery and invocation.
- Reproducible release packaging with SHA-256 manifests and automated repository checks.
- Inspectable Markdown and JSON source/translation examples.
- MIT license file matching the license declared by the original package.

## 1.0.0 — 2026-11-09

Original local package, as recorded in its supplied changelog; this entry does not assert that a public release existed on that date.

- Introduced the multilingual-to-Simplified-Chinese translation Skill and ten focused reference guides.
- Included manually authored evaluation examples and offline consistency-checking scripts.

Automated tool tests do not establish model translation accuracy. See [tests/EVALUATION.md](tests/EVALUATION.md) for the separate model evaluation process.
