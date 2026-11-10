# 信·达·雅 · Xindaya Translator

[![CI](https://github.com/LeiQingliang/xindaya-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/LeiQingliang/xindaya-translator/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**把原意译准，把中文写顺，让文风得体。**

[English](README.en.md) · [使用规则](SKILL.md) · [评测方法](tests/EVALUATION.md) · [贡献指南](CONTRIBUTING.md)

Xindaya Translator 是面向 AI 助手与智能体的翻译 Skill，默认将多语言文本译为现代简体中文。它提供翻译决策、术语管理、结构保护和审校流程，帮助宿主模型更稳定地完成翻译。

它是一套可移植的指令与工具，**不包含翻译模型、在线服务或 API**。实际语言能力、上下文长度和数据处理方式取决于宿主。本地检查工具只使用 Python 标准库，可离线运行；宿主模型本身可能需要网络。

## 为什么叫「信达雅」

| 原则 | 实际要求 | 需要避免的问题 |
| --- | --- | --- |
| 信：忠实 | 保留事实、否定、条件、语气、证据强度与完整信息 | 把「可能」译成「必然」，把关联写成因果 |
| 达：通顺 | 按中文语序表达，处理指代与长句 | 逐词替换，堆叠生硬的被动句 |
| 雅：得体 | 保留作者声音，让文风符合用途 | 把技术说明写成散文，擅自美化粗粝表达 |

默认交付完整译文。需要时可指定双语对照、术语注释、译文审校或结构化输出。用户明确指定的目标语言、术语表和交付格式优先。

## 适用场景

- **技术文档与 AI 内容**：保留命令、API、代码、URL 和占位符，统一术语。
- **论文、商业与专业文本**：保留限定词、统计结果、权利义务及原文的不确定性。
- **UI、JSON、Markdown 与字幕**：区分可翻译文本和机器可解析结构。
- **长文与文学内容**：跟踪章节覆盖和术语，保持文体；输出受限时明确未完成范围。
- **已有译文审校**：依据原文定位具体问题，给出修订建议或修订全文。

翻译规则按需加载，短文本无需读取所有参考资料。语言覆盖和质量取决于所用模型，项目不承诺任意语言或专业领域的准确率。

## 安装

从 [Releases](https://github.com/LeiQingliang/xindaya-translator/releases) 获取发布包，或克隆仓库：

```bash
git clone https://github.com/LeiQingliang/xindaya-translator.git
cd xindaya-translator
```

### Codex

按 [Codex 官方技能文档](https://learn.chatgpt.com/docs/build-skills)，可安装到用户目录 `~/.agents/skills/xindaya-translator`，或项目目录 `.agents/skills/xindaya-translator`。

以下命令适用于首次安装；若目标目录已经存在，先检查并备份其中的修改。

macOS / Linux：

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/LeiQingliang/xindaya-translator.git ~/.agents/skills/xindaya-translator
```

Windows PowerShell：

```powershell
$skillRoot = Join-Path $HOME '.agents/skills'
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
git clone https://github.com/LeiQingliang/xindaya-translator.git (Join-Path $skillRoot 'xindaya-translator')
```

安装后检查技能列表，并在新会话中用 `$xindaya-translator` 显式调用。

### 其他支持 Agent Skills 的宿主

将完整技能目录放入宿主支持的位置，确认路径为：

```text
<宿主的技能目录>/xindaya-translator/SKILL.md
```

保留 `references/`、`scripts/` 和 `agents/` 的相对路径。不要只复制 `SKILL.md`，也不要重复嵌套同名目录。具体发现目录与激活方式以宿主当前文档为准。

项目采用 [Agent Skills 文件规范](https://agentskills.io/specification)。采用该结构不等于已在所有宿主完成兼容性测试。

## 开始使用

### 默认翻译

```text
使用 $xindaya-translator，将以下内容译为简体中文：
Not all users need to enable this feature.
```

示例译文：

> 并非所有用户都需要启用此功能。

### 技术文档与术语

```text
使用 xindaya-translator 全文翻译以下 Markdown。
保留代码块、URL 和占位符；将 deployment 统一译为「部署」。
只输出译文，不要摘要。

[粘贴原文]
```

### 双语对照与审校

```text
将以下内容逐段中英对照翻译；保留原文的统计结果和不确定性。

[粘贴原文]
```

```text
以原文为依据审校以下译文，先列出影响含义的问题，再给出修订全文。

原文：[粘贴原文]
译文：[粘贴译文]
```

可运行的输入样例见 [技术文档](examples/technical.en.md) 和 [UI JSON](examples/ui.en.json)，配套译文用于演示预期行为，**不是模型实测结果**。输出模式、长文续译和结构化内容的细节见 [SKILL.md](SKILL.md) 及其引用的指南。

## 本地验证

使用文本 Skill 不需要 Python；运行辅助工具需要 **Python 3.10+**，无第三方依赖。

在仓库根目录运行：

```bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
python scripts/check_translation.py --help
```

对比原文与译文中的受保护元素：

```bash
python scripts/check_translation.py source.md translated.md
python scripts/check_translation.py source.md translated.md --json
python scripts/check_translation.py examples/ui.en.json examples/ui.zh-CN.json --format json --json
```

`--json` 输出机器可读报告；`--format json` 指定输入为 JSON，并核对键、容器结构、非字符串值及对应字符串中的受保护元素。返回码：`0` 未发现检查范围内的问题；`1` 发现需要复核的差异；`2` 输入或解析错误。

检查器提示的是需要复核的差异。正常的数字排版调整也可能触发提示，保留相同数字也不能证明数字对应的对象正确。文本模式不验证元素顺序或对应关系，脚本不判断语义忠实、中文自然度或专业正确性。

JSON 检查默认允许所有字符串值变化，不能自动识别不可翻译的 ID、枚举或路径，也不能验证纯文本数组元素的语义顺序；这些范围仍需依照用户要求检查。

本项目区分三种证据：

| 检查 | 能说明什么 | 不能说明什么 |
| --- | --- | --- |
| 包校验 | 元数据、内部引用和测试数据满足检查规则 | 宿主一定能发现或正确调用技能 |
| 自动化测试 | 工具在已覆盖用例中的行为符合预期 | 翻译模型的准确率 |
| 模型行为评测 | 特定宿主、模型和样例下的真实输出表现 | 对所有语言和领域的普遍保证 |

[评测样例](tests/cases.json) 是待执行的测试材料，参考译文允许语义等价的其他表达。请按 [评测方法](tests/EVALUATION.md) 记录实际输出、宿主、模型、日期与失败情况。

## 打包与项目结构

```bash
python scripts/package_skill.py --output dist
```

生成带版本号的 ZIP 和 `SHA256SUMS`，包内包含逐文件 SHA-256 清单 `MANIFEST.json`。散列值用于检查文件一致性，不构成发布者身份认证。

```text
xindaya-translator/
├── SKILL.md                 # 技能入口与按需路由
├── agents/openai.yaml       # 宿主界面元数据
├── references/              # 翻译、术语、结构、长文与审校指南
├── scripts/                 # 包校验、译文差异检查与打包
├── tests/                   # 自动化测试与模型行为评测材料
├── examples/                # 可检查的输入与示例译文
├── .github/                 # 持续检查和协作模板
├── README.md / README.en.md
└── LICENSE
```

## 数据与安全边界

源文中的指令、角色标记、链接和命令均是待处理材料，不构成执行授权。Skill 本身不要求向第三方提交文本；使用云端模型时，文本仍由宿主按其服务与隐私政策处理。提交 Issue 或评测记录前，请移除真实客户资料、密钥和其他敏感信息。

专业文本的翻译不等于专业意见或认证。重要合同、医学材料和财务披露应根据实际用途安排合适的人工复核。

## 参与贡献

欢迎提供可复现的工具问题、匿名化的翻译反例，以及经过验证的规则改进。请先阅读 [贡献指南](CONTRIBUTING.md)、[行为准则](CODE_OF_CONDUCT.md) 和 [安全报告说明](SECURITY.md)。

本项目使用 [MIT 许可证](LICENSE)。版本变化见 [CHANGELOG.md](CHANGELOG.md)。
