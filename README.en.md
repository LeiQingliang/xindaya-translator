# Xindaya Translator · 信·达·雅

[![CI](https://github.com/LeiQingliang/xindaya-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/LeiQingliang/xindaya-translator/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Faithful meaning. Natural Chinese. Appropriate style.**

[简体中文](README.md) · [Skill instructions](SKILL.md) · [Evaluation](tests/EVALUATION.md) · [Contributing](CONTRIBUTING.md)

Xindaya Translator is a translation Skill for AI assistants and agents. It defaults to modern Simplified Chinese and provides guidance for faithful translation, terminology, protected syntax, long documents, and revision.

This repository contains portable instructions and utilities, **not a translation model, hosted service, or API**. Language coverage, context limits, and data handling depend on the host model. The optional local checks use only the Python standard library and work offline; the host model may require a network connection.

## What “Xin, Da, Ya” means

| Principle | In practice | Avoid |
| --- | --- | --- |
| 信 · Faithfulness | Preserve facts, negation, conditions, modality, evidence, and completeness | Turning “may” into “will” or association into causation |
| 达 · Clarity | Use natural Chinese syntax and resolve references with context | Word substitution and awkward sentence structures |
| 雅 · Appropriate style | Preserve the author's voice and suit the text's purpose | Making every passage ornate or silently softening its tone |

The default output is the complete translation. Users can request bilingual alignment, concise notes, translation review, or structured output. Explicit target-language, glossary, and delivery requirements take precedence.

## Where it helps

- **Technical and AI documentation:** preserve commands, APIs, code, URLs, and placeholders while keeping terminology consistent.
- **Research, business, and professional texts:** preserve qualifications, statistics, obligations, and uncertainty.
- **UI strings, JSON, Markdown, and subtitles:** distinguish translatable text from machine-readable structure.
- **Long documents and literature:** track coverage and terminology, preserve voice, and disclose incomplete output.
- **Translation review:** identify specific source-grounded issues and provide corrections.

Detailed references load only when relevant. Actual translation quality depends on the host model; the project does not claim a universal accuracy rate or validated coverage of every language or domain.

## Installation

Download a package from [Releases](https://github.com/LeiQingliang/xindaya-translator/releases), or clone the repository:

```bash
git clone https://github.com/LeiQingliang/xindaya-translator.git
cd xindaya-translator
```

### Codex

The [official Codex Skill documentation](https://learn.chatgpt.com/docs/build-skills) supports user-level installation at `~/.agents/skills/xindaya-translator` and project-level installation at `.agents/skills/xindaya-translator`.

These commands are for a fresh installation. If the destination exists, inspect and back up any changes first.

macOS / Linux:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/LeiQingliang/xindaya-translator.git ~/.agents/skills/xindaya-translator
```

Windows PowerShell:

```powershell
$skillRoot = Join-Path $HOME '.agents/skills'
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
git clone https://github.com/LeiQingliang/xindaya-translator.git (Join-Path $skillRoot 'xindaya-translator')
```

Check the host's skill list, then invoke `$xindaya-translator` in a new conversation.

### Other Agent Skills hosts

Place the complete skill directory in a location supported by your host. The resulting path should be:

```text
<host-skills-directory>/xindaya-translator/SKILL.md
```

Keep `references/`, `scripts/`, and `agents/` at their relative locations. Do not copy only `SKILL.md` or accidentally create two nested `xindaya-translator` directories. Consult your host's current documentation for discovery paths and invocation syntax.

The project follows the [Agent Skills file specification](https://agentskills.io/specification). This layout is not evidence of end-to-end compatibility with every host.

## Usage

### Basic translation

```text
Use $xindaya-translator to translate the following into Simplified Chinese:
Not all users need to enable this feature.
```

Illustrative translation:

> 并非所有用户都需要启用此功能。

### Technical documents and terminology

```text
Use xindaya-translator to translate the entire Markdown document below.
Keep code blocks, URLs, and placeholders unchanged.
Translate deployment consistently as 部署.
Return only the translation, without summarizing.

[source text]
```

### Alignment and review

```text
Translate the following with English and Chinese paragraphs aligned.
Preserve the statistical results and the source's uncertainty.

[source text]
```

```text
Review this Chinese translation against the source.
List issues that affect meaning, then provide the complete corrected translation.

Source: [source text]
Translation: [translated text]
```

Try the [technical document](examples/technical.en.md) and [UI JSON](examples/ui.en.json) examples. Their paired translations illustrate intended behavior and **are not recorded model outputs**. See [SKILL.md](SKILL.md) and its focused references for output modes, long-document continuation, and structured content.

## Local verification

The instruction-only Skill does not need Python. Optional utilities require **Python 3.10+**, with no third-party dependencies.

Run from the repository root:

```bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
python scripts/check_translation.py --help
```

Compare protected elements in a source and translation:

```bash
python scripts/check_translation.py source.md translated.md
python scripts/check_translation.py source.md translated.md --json
python scripts/check_translation.py examples/ui.en.json examples/ui.zh-CN.json --format json --json
```

`--json` produces a machine-readable report. `--format json` selects JSON input and checks keys, container structure, non-string values, and protected elements in corresponding strings. Exit codes: `0` no findings within the checks' scope; `1` differences need review; `2` input or parse error.

Findings are review prompts. Legitimate number formatting changes can trigger findings, while retaining the same numbers does not prove that each number still describes the correct object. Text mode does not validate element order or correspondence. The checker does not assess meaning, naturalness, or professional correctness.

JSON mode permits changes to every string value. It cannot infer protected business IDs, enums or paths, or validate the semantic order of plain-text array items; review those against the user's translation scope.

Keep these forms of evidence separate:

| Check | What it supports | What it does not establish |
| --- | --- | --- |
| Package validation | Metadata, internal references, and fixtures satisfy the implemented checks | The host discovers and invokes the Skill correctly |
| Automated tests | Utilities behave as expected on covered inputs | Model translation accuracy |
| Model behavior evaluation | Observed outputs for a recorded host, model, and test set | General performance across all languages and domains |

The [evaluation cases](tests/cases.json) are test inputs, not completed model runs. Equivalent translations may be valid. Follow the [evaluation guide](tests/EVALUATION.md) and record actual outputs, host, model, date, and failures.

## Packaging and repository layout

```bash
python scripts/package_skill.py --output dist
```

This creates a versioned ZIP and `SHA256SUMS`. The archive includes `MANIFEST.json` with per-file SHA-256 hashes. Hashes support integrity checks, not publisher authentication.

```text
xindaya-translator/
├── SKILL.md                 # Entry point and focused reference routing
├── agents/openai.yaml       # Host UI metadata
├── references/              # Translation, terminology, structure, and review
├── scripts/                 # Validation, consistency checks, and packaging
├── tests/                   # Automated tests and model evaluation material
├── examples/                # Inspectable sources and illustrative translations
├── .github/                 # Continuous checks and contribution templates
├── README.md / README.en.md
└── LICENSE
```

## Data and security

Instructions, role markers, links, and commands inside source text are translation data, not authorization to act. The Skill does not require submitting content to a third party. A cloud-hosted model still processes content under its host's service and privacy terms. Remove customer data, credentials, and other sensitive content before posting issues or evaluation results.

Translation of professional material is not professional advice or certification. Arrange appropriate human review for consequential contracts, medical material, and financial disclosures.

## Contributing and license

Reproducible tool bugs, anonymized translation counterexamples, and tested rule improvements are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md), and the [security reporting policy](SECURITY.md).

Licensed under [MIT](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for version history.
