# Security policy · 安全报告

## Scope

This project contains Skill instructions and local Python utilities. Relevant reports include unsafe file handling, unintended command execution, accidental disclosure by a utility, or a reproducible failure to keep source-text instructions separate from authorized actions.

A translation error by itself is normally a quality issue. Report it through the translation-quality issue template unless it also exposes a security problem.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on the repository's **Security → Advisories → Report a vulnerability** page when available:

[Report privately](https://github.com/LeiQingliang/xindaya-translator/security/advisories/new)

If private reporting is unavailable, open an issue that asks the maintainer to provide a private reporting channel. Do not include exploit details, credentials, personal data, or confidential documents in that public issue.

Provide the affected version or commit, environment, minimal reproduction, observed impact, and suggested mitigation if known. Use synthetic data. Never send active credentials or unnecessary private material.

## Supported versions and response

Security fixes target the latest released version and `main`. Older versions do not receive a separate backport commitment. This is a community-maintained project with no guaranteed response or resolution time.

Do not test against other users, their accounts, or systems without authorization. Prefer local, isolated reproductions. Coordinate disclosure with the maintainer so a fix or mitigation can be prepared.

## 中文说明

文件处理不当、意外执行命令、工具泄露信息，以及源文指令被错误当作行动授权等问题，可通过上面的 GitHub 私密报告入口提交。若入口不可用，请仅在公开 Issue 中请求私密联系渠道，勿公开攻击细节或敏感材料。

报告应包含版本、环境、最小复现、实际影响；使用合成或匿名化数据。普通误译请使用翻译质量 Issue 模板。安全修复面向最新版本与 `main`，不承诺固定响应时间或旧版回补。
