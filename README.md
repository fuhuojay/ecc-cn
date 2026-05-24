# Everything Claude Code 中文命令中心

这是一个静态版的 Everything Claude Code 中文速查页面，可以直接部署到 GitHub Pages 在线访问。

## 功能亮点

- 按中文开发任务查找 Skill：代码审查、修复构建、测试质量、功能规划、文档资料、安全合规等。
- 按应用场景选择 Skill：新功能开发、构建失败、提交前检查、测试补齐、代码重构、安全发布、文档维护、复杂协作。
- 每个应用场景都包含问题描述、推荐命令组合、示范提问和预期产出，方便直接复制使用。
- 顶部提供大号快速导航区，优先突出“场景案例”和高频入口。
- 提供推荐工作流，帮助开发者把多个命令组合起来使用。
- 每条命令都有白话解释、适用场景、不适用场景、标签和推荐用法。
- 已整合旧版 `ecc-reference.html` 中的详细中文说明、英文原文、表格和步骤，支持在卡片内展开查看。
- 提供“原参考”视图，可以浏览旧版网页端的命令、技能和智能体说明。
- 支持中文场景搜索，例如“编译不过”“提交前”“写测试”“安全”“文档”。
- 数据和页面分离，页面优先从 `data.json` 与 `reference-data.json` 加载内容；直接用 `file://` 打开时会自动使用内置兜底数据。

## 在线部署

推荐使用 GitHub Pages：

1. 将本目录推送到 GitHub 仓库。
2. 打开仓库的 `Settings` -> `Pages`。
3. 在 `Build and deployment` 中选择 `GitHub Actions`。
4. 推送到 `main` 分支后，工作流会自动发布站点。

发布后，根地址会自动跳转到 `ecc_cn_command_center/` 页面。

## 更新数据

当前页面不是实时同步数据库，而是静态生成的 HTML。仓库已包含自动更新工作流，默认每 6 小时检查一次上游内容；如果有变化，会自动提交更新并触发 GitHub Pages 重新部署。

如果上游 `everything-claude-code` 有新条目，可以运行：

```bash
python3 ecc_cn_command_center.py --update
```

脚本会重新生成 `ecc_cn_command_center/index.html` 和 `ecc_cn_command_center/data.json`，然后提交并推送到 GitHub，GitHub Pages 会自动更新线上页面。

页面右上角的“检查更新”按钮只会检查上游是否有新文件，并提示你本地运行更新命令；它不会直接修改线上页面。

也可以在 GitHub 仓库的 `Actions` 页面手动运行 `Update ECC Data` 工作流，立即检查并更新。

## 本地重建页面

如果只是修改页面模板或中文增强逻辑，不想访问 GitHub，可以使用现有数据本地重建：

```bash
python3 ecc_cn_command_center.py --local
```

由于页面会通过 `fetch('./data.json')` 加载数据，本地预览建议启动静态服务器后访问：

```bash
python3 -m http.server 8000
```
