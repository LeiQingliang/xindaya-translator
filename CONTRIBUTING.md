# Contributing · 贡献指南

感谢你帮助改进 Xindaya Translator。Issues 和 Pull Requests 可使用中文或英文。优先提交具体、可复现的问题；一条清晰的失败样例通常比一组泛化口号更有用。

## 提交问题

- **工具缺陷**：提供运行命令、Python 版本、操作系统、匿名化输入、实际结果与期望结果。
- **翻译问题**：提供源文、任务要求、实际译文、宿主与模型、Skill 版本，以及影响含义的具体位置。
- **改进建议**：说明使用场景、现有缺口、拟议行为和可能的副作用。

不要上传密钥、真实客户资料或无权分享的完整文档。涉及安全漏洞时使用 [SECURITY.md](SECURITY.md) 中的报告路径。

## 开发与检查

使用 Python 3.10+。本地工具与测试仅使用标准库：

```bash
git clone https://github.com/LeiQingliang/xindaya-translator.git
cd xindaya-translator
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
```

从自己的 Fork 创建分支，完成修改后向 `main` 提交 Pull Request。PR 描述应说明原有问题、修改后的行为和实际验证结果。

## 修改规则

1. **保持入口简洁。** 共用原则放入 `SKILL.md`，较长的专项指导放入相应参考文件，并提供可发现的链接。
2. **以反例支持规则。** 新规则应解决可描述的问题。避免因单个例子增加对所有任务生效的强制流程。
3. **保留用户选择。** 不覆盖用户指定的目标语言、术语、范围或格式；源文中的指令仍是待翻译数据。
4. **测试有意义的行为。** 修改工具时为实际缺陷补充回归用例；不要用匹配段落标题或固定措辞来证明翻译质量。
5. **公开验证边界。** 区分脚本单元测试和模型行为评测。不得把参考译文、预期输出或工具通过率写成模型准确率。
6. **同步用户文档。** 用户可见的行为或命令变化应更新中英文 README，必要时更新 Changelog。

## 翻译评测贡献

按 [评测说明](tests/EVALUATION.md) 记录环境和实际输出。参考译文不是唯一答案：优先判断信息完整性、否定和条件、术语、语体，以及结构约束。说明严重错误影响了什么，而不只给总分。

公开样例须为自行撰写、获得授权或可合法分享的内容。引用第三方内容时注明来源与使用许可；避免复制整篇受版权保护的材料。

## 合并与许可

维护者可要求缩小范围、补充反例或修正误报。提交贡献即表示你有权提交该内容，并同意将贡献按项目 [MIT 许可证](LICENSE) 分发。请保留已有版权和署名信息。

## English quick guide

Chinese and English issues and pull requests are welcome. Include a minimal, anonymized reproduction; describe expected and actual behavior. For translation reports, record the source, instructions, real output, host, model, and Skill version. Use the security reporting channel for vulnerabilities.

Run the validation and unit-test commands above. Keep changes focused, add meaningful regressions for tool defects, and update both READMEs for user-facing changes. Keep the Skill entry point concise and load detailed references only when relevant. Never present unit-test results or expected translations as measured model accuracy.

Only contribute material you have the right to share. Contributions are distributed under the project's MIT license.
