import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

OUTPUT_DIR = Path("./ecc_cn_command_center")
DATA_FILE = OUTPUT_DIR / "data.json"
REFERENCE_DATA_FILE = OUTPUT_DIR / "reference-data.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# category / sub / zh_name / zh_desc / simple
TRANSLATIONS = {
    # ===== Agents - 代码审查 =====
    "code-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "通用代码审查员",
        "zh_desc": "通用代码审查专家。在编写或修改代码后自动触发，对代码质量、最佳实践、可维护性进行全面审查，发现潜在问题并给出改进建议。",
        "simple": "写完代码后帮你检查有没有毛病，像一个严格的老师批改作业。"
    },
    "typescript-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "TypeScript 代码审查员",
        "zh_desc": "TypeScript/JavaScript 代码审查专家。专注于类型安全、异步正确性、Node/Web 安全和惯用模式，检查 TypeScript 特有的类型问题。",
        "simple": "专门检查 TypeScript 代码的类型有没有写对，防止运行时报错。"
    },
    "python-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "Python 代码审查员",
        "zh_desc": "Python 代码审查专家。检查 PEP 8 规范、Pythonic 惯用写法、类型提示、安全性和性能问题。",
        "simple": "检查 Python 代码是否符合规范，写法是否地道。"
    },
    "go-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "Go 代码审查员",
        "zh_desc": "Go 代码审查专家。检查惯用 Go 模式、并发安全、错误处理、性能优化和最佳实践。",
        "simple": "检查 Go 代码有没有正确处理并发和错误，是否符合 Go 的习惯写法。"
    },
    "rust-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "Rust 代码审查员",
        "zh_desc": "Rust 代码审查专家。检查所有权、生命周期、错误处理、unsafe 使用和惯用 Rust 模式。",
        "simple": "检查 Rust 代码的所有权和生命周期有没有搞对，内存是否安全。"
    },
    "cpp-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "C++ 代码审查员",
        "zh_desc": "C++ 代码审查专家。专注于内存安全、现代 C++ 惯用写法、并发正确性和性能优化。",
        "simple": "检查 C++ 代码有没有内存泄漏、越界访问等常见问题。"
    },
    "java-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "Java 代码审查员",
        "zh_desc": "Java/Spring Boot 代码审查专家。检查分层架构、JPA 模式、安全性和并发问题。",
        "simple": "检查 Java/Spring Boot 代码的架构设计和并发安全。"
    },
    "kotlin-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "Kotlin 代码审查员",
        "zh_desc": "Kotlin/Android/KMP 代码审查专家。检查惯用模式、协程安全、Compose 最佳实践和常见 Android 陷阱。",
        "simple": "检查 Kotlin 和 Android 代码，确保协程和 Compose 用法正确。"
    },
    "csharp-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "C# 代码审查员",
        "zh_desc": "C# 代码审查专家。检查 .NET 惯例、异步模式、安全性和性能问题。",
        "simple": "检查 C# 代码是否符合 .NET 规范，异步写法有没有问题。"
    },
    "flutter-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "Flutter 代码审查员",
        "zh_desc": "Flutter/Dart 代码审查专家。检查 Widget 最佳实践、状态管理模式、Dart 惯用写法和性能陷阱。",
        "simple": "检查 Flutter 界面代码，确保组件和状态管理写法正确。"
    },
    "database-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "数据库审查员",
        "zh_desc": "PostgreSQL 数据库专家。审查查询优化、Schema 设计、安全性和性能问题，集成 Supabase 最佳实践。",
        "simple": "检查 SQL 查询写得好不好，数据库表结构设计合不合理。"
    },
    "healthcare-reviewer": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "医疗健康代码审查员",
        "zh_desc": "医疗应用代码审查专家。检查临床安全性、CDSS 准确性、PHI 合规性和医疗数据完整性，适用于 EMR/EHR 系统。",
        "simple": "专门审查医疗系统的代码，确保患者数据安全和合规。"
    },

    # ===== Agents - 构建修复 =====
    "build-error-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "构建错误修复器",
        "zh_desc": "构建和 TypeScript 错误修复专家。当构建失败或类型错误时自动触发，以最小改动修复构建/类型错误，不做架构调整。",
        "simple": "项目跑不起来了？它帮你找到报错原因并修好，只改必要的地方。"
    },
    "cpp-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "C++ 构建修复器",
        "zh_desc": "C++ 构建、CMake 和编译错误修复专家。修复构建错误、链接问题和模板错误，改动最小化。",
        "simple": "C++ 编译报错了？它帮你修 CMake 配置和编译错误。"
    },
    "dart-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "Dart 构建修复器",
        "zh_desc": "Dart/Flutter 构建、分析和依赖错误修复专家。修复 dart analyze 错误、Flutter 编译失败和 pub 依赖冲突。",
        "simple": "Flutter 项目编译失败？它帮你修依赖冲突和分析错误。"
    },
    "go-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "Go 构建修复器",
        "zh_desc": "Go 构建、vet 和编译错误修复专家。修复构建错误、go vet 问题和 linter 警告。",
        "simple": "Go 代码编译不过？它帮你修构建错误和代码检查警告。"
    },
    "java-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "Java 构建修复器",
        "zh_desc": "Java/Maven/Gradle 构建和编译错误修复专家。修复构建错误、编译器错误和依赖管理问题。",
        "simple": "Java 项目 Maven/Gradle 构建失败？它帮你修依赖和编译问题。"
    },
    "kotlin-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "Kotlin 构建修复器",
        "zh_desc": "Kotlin/Gradle 构建、编译和依赖错误修复专家。修复构建错误、Kotlin 编译器错误和 Gradle 问题。",
        "simple": "Kotlin 项目 Gradle 构建报错？它帮你定位并修复。"
    },
    "pytorch-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "PyTorch 构建修复器",
        "zh_desc": "PyTorch 运行时、CUDA 和训练错误修复专家。修复张量形状不匹配、设备错误、梯度问题和混合精度失败。",
        "simple": "深度学习训练报错了？它帮你修张量形状不匹配、GPU 错误等问题。"
    },
    "rust-build-resolver": {
        "category": "Agents", "sub": "构建修复",
        "zh_name": "Rust 构建修复器",
        "zh_desc": "Rust 构建、编译和依赖错误修复专家。修复 cargo 构建错误、借用检查器问题和 Cargo.toml 配置。",
        "simple": "Rust 编译不过？它帮你修 cargo 构建错误和借用检查器报错。"
    },

    # ===== Agents - 架构规划 =====
    "architect": {
        "category": "Agents", "sub": "架构规划",
        "zh_name": "软件架构师",
        "zh_desc": "软件架构专家。用于系统设计、可扩展性和技术决策，在规划新功能、重构大型系统或做架构决策时主动使用。",
        "simple": "帮你设计软件的整体蓝图，决定用什么技术、怎么组织代码。"
    },
    "planner": {
        "category": "Agents", "sub": "架构规划",
        "zh_name": "实现规划师",
        "zh_desc": "实现规划专家。用于复杂功能和重构任务，自动为规划任务激活，创建分步实现计划。",
        "simple": "面对复杂需求时，帮你把大任务拆成一步一步的小任务来做。"
    },
    "code-architect": {
        "category": "Agents", "sub": "架构规划",
        "zh_name": "功能架构师",
        "zh_desc": "功能架构设计专家。通过分析现有代码库模式和惯例，提供实现蓝图，包含具体文件、接口、数据流和构建顺序。",
        "simple": "分析现有代码结构，告诉你新功能应该写在哪些文件里、怎么组织。"
    },

    # ===== Agents - 测试 =====
    "tdd-guide": {
        "category": "Agents", "sub": "测试",
        "zh_name": "TDD 指南",
        "zh_desc": "测试驱动开发专家。强制执行先写测试的方法论，编写失败测试 -> 实现代码 -> 重构，确保 80%+ 测试覆盖率。",
        "simple": "教你「先写测试再写代码」的开发方式，确保代码质量。"
    },
    "e2e-runner": {
        "category": "Agents", "sub": "测试",
        "zh_name": "端到端测试运行器",
        "zh_desc": "端到端测试专家。使用 Playwright 生成、维护和运行 E2E 测试，管理测试流程，上传测试产物。",
        "simple": "模拟真实用户操作，自动点击按钮、填写表单，测试整个流程能不能跑通。"
    },
    "pr-test-analyzer": {
        "category": "Agents", "sub": "测试",
        "zh_name": "PR 测试分析器",
        "zh_desc": "PR 测试覆盖率审查专家。审查 Pull Request 的测试覆盖质量和完整性，重点关注行为覆盖和真实 bug 防护。",
        "simple": "检查你提交的代码改动有没有被测试覆盖到，哪里还缺测试。"
    },

    # ===== Agents - 安全 =====
    "security-reviewer": {
        "category": "Agents", "sub": "安全",
        "zh_name": "安全审查员",
        "zh_desc": "安全漏洞检测和修复专家。在处理用户输入、认证、API 端点或敏感数据的代码编写后主动使用，检测 OWASP Top 10 漏洞。",
        "simple": "检查代码有没有安全漏洞，比如密码泄露、SQL 注入、被黑客攻击的风险。"
    },
    "opensource-forker": {
        "category": "Agents", "sub": "安全",
        "zh_name": "开源分叉器",
        "zh_desc": "开源项目分叉专家。复制文件、剥离密钥和凭据（20+ 种模式）、替换内部引用为占位符，是开源流水线的第一阶段。",
        "simple": "把内部项目变成开源项目的第一步：帮你清理掉所有密码和密钥。"
    },
    "opensource-packager": {
        "category": "Agents", "sub": "安全",
        "zh_name": "开源打包器",
        "zh_desc": "开源打包专家。为清理后的项目生成完整的开源包装：CLAUDE.md、README.md、LICENSE、CONTRIBUTING.md 等，是第三阶段。",
        "simple": "帮开源项目生成 README、许可证、贡献指南等标准文件。"
    },
    "opensource-sanitizer": {
        "category": "Agents", "sub": "安全",
        "zh_name": "开源清理器",
        "zh_desc": "开源发布前安全验证专家。扫描泄露的密钥、PII、内部引用和危险文件，生成 PASS/FAIL 报告，是第二阶段。",
        "simple": "开源发布前的安全检查：扫描有没有泄露密码、个人信息或内部链接。"
    },

    # ===== Agents - 文档 =====
    "doc-updater": {
        "category": "Agents", "sub": "文档",
        "zh_name": "文档更新器",
        "zh_desc": "文档和代码地图专家。主动用于更新代码地图和文档，运行 /update-codemaps 和 /update-docs，生成架构文档。",
        "simple": "代码改了之后，自动帮你更新配套的文档，保持文档和代码同步。"
    },
    "docs-lookup": {
        "category": "Agents", "sub": "文档",
        "zh_name": "文档查询器",
        "zh_desc": "文档查询专家。当用户询问库、框架或 API 的用法时使用，通过 Context7 获取最新文档并返回带代码示例的答案。",
        "simple": "不知道某个库怎么用？它帮你查最新文档并给出代码示例。"
    },

    # ===== Agents - 性能优化 =====
    "performance-optimizer": {
        "category": "Agents", "sub": "性能优化",
        "zh_name": "性能优化器",
        "zh_desc": "性能分析和优化专家。主动识别瓶颈、优化慢代码、减小包体积、改善运行时性能，包括内存泄漏和渲染优化。",
        "simple": "程序跑得慢？它帮你找到瓶颈在哪里，教你怎么加速。"
    },
    "harness-optimizer": {
        "category": "Agents", "sub": "性能优化",
        "zh_name": "测试工具优化器",
        "zh_desc": "测试工具配置优化专家。分析并改进本地代理工具配置，提升可靠性、降低成本和提高吞吐量。",
        "simple": "帮你优化 Claude Code 自身的工具配置，让它跑得更快更省。"
    },

    # ===== Agents - 代码质量 =====
    "code-simplifier": {
        "category": "Agents", "sub": "代码质量",
        "zh_name": "代码简化器",
        "zh_desc": "代码简化和精炼专家。专注于最近修改的代码，提升清晰度、一致性和可维护性，同时保留原有行为。",
        "simple": "把复杂冗长的代码简化成更清晰易读的版本，功能不变。"
    },
    "refactor-cleaner": {
        "category": "Agents", "sub": "代码质量",
        "zh_name": "重构清理器",
        "zh_desc": "死代码清理和合并专家。主动用于移除未使用的代码、重复代码和重构，运行分析工具识别死代码并安全移除。",
        "simple": "帮你找到项目里没人用的「死代码」，然后安全地删掉。"
    },
    "comment-analyzer": {
        "category": "Agents", "sub": "代码质量",
        "zh_name": "注释分析器",
        "zh_desc": "代码注释分析专家。检查注释的准确性、完整性、可维护性和注释腐化风险。",
        "simple": "检查代码注释是否准确、有没有过时，避免注释误导人。"
    },
    "silent-failure-hunter": {
        "category": "Agents", "sub": "代码质量",
        "zh_name": "静默故障猎手",
        "zh_desc": "静默故障检测专家。审查代码中的静默失败、被吞掉的错误、糟糕的回退和缺失的错误传播。",
        "simple": "帮你找到代码里「出错了但没人知道」的情况，避免 bug 被悄悄吞掉。"
    },
    "type-design-analyzer": {
        "category": "Agents", "sub": "代码质量",
        "zh_name": "类型设计分析器",
        "zh_desc": "类型设计分析专家。分析类型的封装性、不变量表达、实用性和强制约束。",
        "simple": "检查代码里的数据类型设计得好不好，有没有用对。"
    },

    # ===== Agents - AI/辅助 =====
    "gan-evaluator": {
        "category": "Agents", "sub": "AI 辅助",
        "zh_name": "GAN 评估器",
        "zh_desc": "GAN 测试工具的评估器代理。通过 Playwright 测试运行中的应用，按评分标准打分，并向生成器提供可操作的反馈。",
        "simple": "像一个质检员，自动测试生成的界面好不好用，然后告诉 AI 哪里需要改进。"
    },
    "gan-generator": {
        "category": "Agents", "sub": "AI 辅助",
        "zh_name": "GAN 生成器",
        "zh_desc": "GAN 测试工具的生成器代理。根据规格实现功能，读取评估器反馈并迭代，直到达到质量阈值。",
        "simple": "像一个程序员，根据需求写代码，收到反馈后不断修改直到满意。"
    },
    "gan-planner": {
        "category": "Agents", "sub": "AI 辅助",
        "zh_name": "GAN 规划器",
        "zh_desc": "GAN 测试工具的规划器代理。将一句话提示扩展为完整的产品规格，包含功能、迭代计划、评估标准和设计方向。",
        "simple": "你说一句「我想要什么」，它帮你把需求细化成完整的产品方案。"
    },

    # ===== Agents - 运维辅助 =====
    "loop-operator": {
        "category": "Agents", "sub": "运维辅助",
        "zh_name": "循环操作器",
        "zh_desc": "自主循环操作专家。运行自主代理循环，监控进度，在循环停滞时安全介入。",
        "simple": "让 AI 自动重复执行某个任务，它会自己监控进度，卡住了会自动处理。"
    },
    "chief-of-staff": {
        "category": "Agents", "sub": "运维辅助",
        "zh_name": "参谋长",
        "zh_desc": "个人通信参谋长。分类处理邮件、Slack、LINE 和 Messenger 消息，分为四级（跳过/仅信息/会议信息/需行动），生成回复草稿。",
        "simple": "帮你处理各种消息，自动分类重要程度，还能帮你写回复草稿。"
    },
    "conversation-analyzer": {
        "category": "Agents", "sub": "运维辅助",
        "zh_name": "对话分析器",
        "zh_desc": "对话记录分析专家。分析对话记录以发现值得用钩子防止的行为，由 /hookify 触发。",
        "simple": "分析你和 AI 的对话记录，找出哪些操作应该设为自动规则。"
    },
    "code-explorer": {
        "category": "Agents", "sub": "运维辅助",
        "zh_name": "代码探索器",
        "zh_desc": "代码库深度分析专家。通过追踪执行路径、映射架构层和记录依赖关系来深入了解现有功能。",
        "simple": "帮你快速了解一个陌生项目的代码结构，追踪代码是怎么运行的。"
    },
    "seo-specialist": {
        "category": "Agents", "sub": "运维辅助",
        "zh_name": "SEO 专家",
        "zh_desc": "SEO 技术审计专家。处理技术 SEO 审计、页面优化、结构化数据、Core Web Vitals 和内容/关键词映射。",
        "simple": "帮你优化网站，让搜索引擎更容易找到你的网页，提升排名。"
    },

    # ===== Commands - 代码审查 =====
    "Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "代码审查",
        "zh_desc": "多维度代码审查命令。在合并前对代码质量、安全性、可维护性进行全面审查，支持本地未提交更改或 GitHub PR 审查。",
        "simple": "一条命令启动全面代码审查，帮你找出代码里的问题。"
    },
    "C++ Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "C++ 代码审查",
        "zh_desc": "C++ 代码综合审查命令。专注于内存安全、现代 C++ 惯用写法、并发和性能问题。",
        "simple": "专门审查 C++ 代码，检查内存安全和性能问题。"
    },
    "Go Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "Go 代码审查",
        "zh_desc": "Go 代码综合审查命令。检查惯用模式、并发模式、错误处理和性能。",
        "simple": "专门审查 Go 代码，检查并发和错误处理是否正确。"
    },
    "Python Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "Python 代码审查",
        "zh_desc": "Python 代码综合审查命令。检查 PEP 8 规范、Pythonic 惯用写法、类型提示和安全问题。",
        "simple": "专门审查 Python 代码，检查规范和安全问题。"
    },
    "Rust Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "Rust 代码审查",
        "zh_desc": "Rust 代码综合审查命令。检查所有权、生命周期、错误处理和 unsafe 使用。",
        "simple": "专门审查 Rust 代码，检查内存安全和所有权问题。"
    },
    "Kotlin Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "Kotlin 代码审查",
        "zh_desc": "Kotlin 代码综合审查命令。检查惯用模式、协程安全、Compose 最佳实践和常见陷阱。",
        "simple": "专门审查 Kotlin 代码，检查协程和 Compose 用法。"
    },
    "Flutter Code Review": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "Flutter 代码审查",
        "zh_desc": "Flutter/Dart 代码审查命令。检查 Widget 最佳实践、状态管理和 Dart 惯用写法。",
        "simple": "专门审查 Flutter 代码，检查组件和状态管理。"
    },
    "review-pr": {
        "category": "Commands", "sub": "代码审查",
        "zh_name": "PR 综合审查",
        "zh_desc": "使用专门的代理对 Pull Request 进行全面审查，涵盖代码质量、安全性和可维护性。",
        "simple": "对 GitHub 上的 Pull Request 进行全面审查，告诉你哪里有问题。"
    },

    # ===== Commands - 构建修复 =====
    "Build and Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "构建并修复",
        "zh_desc": "检测项目构建系统并增量修复构建错误，专注于让构建快速通过。",
        "simple": "项目编译失败了？一条命令自动检测并修复构建错误。"
    },
    "C++ Build and Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "C++ 构建修复",
        "zh_desc": "修复 C++ 构建错误、CMake 问题和链接器错误，以最小改动解决问题。",
        "simple": "C++ 编译报错？自动修复 CMake 和链接器问题。"
    },
    "Flutter Build and Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "Flutter 构建修复",
        "zh_desc": "修复 Dart 分析器错误和 Flutter 构建失败，增量修复。",
        "simple": "Flutter 编译失败？自动修复 Dart 分析器报的错。"
    },
    "Go Build and Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "Go 构建修复",
        "zh_desc": "修复 Go 构建错误、go vet 警告和 linter 问题。",
        "simple": "Go 编译不过？自动修复构建错误和代码检查警告。"
    },
    "Gradle Build Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "Gradle 构建修复",
        "zh_desc": "修复 Android 和 KMP 项目的 Gradle 构建错误。",
        "simple": "Android 项目 Gradle 构建失败？自动帮你修。"
    },
    "Rust Build and Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "Rust 构建修复",
        "zh_desc": "修复 Rust 构建错误、借用检查器问题和依赖管理。",
        "simple": "Rust 编译不过？自动修复借用检查和依赖问题。"
    },
    "Kotlin Build and Fix": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "Kotlin 构建修复",
        "zh_desc": "修复 Kotlin/Gradle 构建错误、编译器警告和依赖问题，以最小改动解决问题。",
        "simple": "Kotlin 项目 Gradle 构建报错？自动帮你修。"
    },
    "Package Manager Setup": {
        "category": "Commands", "sub": "构建修复",
        "zh_name": "包管理器配置",
        "zh_desc": "分析项目并生成 PM2 服务命令，配置包管理器环境。",
        "simple": "帮你配置项目的包管理器和进程管理工具。"
    },

    # ===== Commands - 测试 =====
    "C++ TDD Command": {
        "category": "Commands", "sub": "测试",
        "zh_name": "C++ TDD 命令",
        "zh_desc": "C++ 测试驱动开发命令。强制先写 GoogleTest 测试，再实现代码。",
        "simple": "用「先写测试再写代码」的方式开发 C++ 程序。"
    },
    "Go TDD Command": {
        "category": "Commands", "sub": "测试",
        "zh_name": "Go TDD 命令",
        "zh_desc": "Go 测试驱动开发命令。先写表驱动测试，再实现代码。",
        "simple": "用「先写测试再写代码」的方式开发 Go 程序。"
    },
    "Kotlin TDD Command": {
        "category": "Commands", "sub": "测试",
        "zh_name": "Kotlin TDD 命令",
        "zh_desc": "Kotlin 测试驱动开发命令。先写 Kotest 测试，再实现代码。",
        "simple": "用「先写测试再写代码」的方式开发 Kotlin 程序。"
    },
    "Rust TDD Command": {
        "category": "Commands", "sub": "测试",
        "zh_name": "Rust TDD 命令",
        "zh_desc": "Rust 测试驱动开发命令。先写测试，再实现代码。",
        "simple": "用「先写测试再写代码」的方式开发 Rust 程序。"
    },
    "Flutter Test": {
        "category": "Commands", "sub": "测试",
        "zh_name": "Flutter 测试",
        "zh_desc": "运行 Flutter/Dart 测试，报告失败并增量修复。",
        "simple": "运行 Flutter 测试，失败了自动帮你修。"
    },
    "Test Coverage": {
        "category": "Commands", "sub": "测试",
        "zh_name": "测试覆盖率",
        "zh_desc": "分析测试覆盖率，识别覆盖缺口并生成缺失的测试用例。",
        "simple": "检查你的测试覆盖了多少代码，哪里还没测到，自动补上。"
    },

    # ===== Commands - 规划 =====
    "Plan Command": {
        "category": "Commands", "sub": "规划",
        "zh_name": "规划命令",
        "zh_desc": "重述需求、评估风险并创建分步实现计划，用于复杂功能的前期规划。",
        "simple": "开始做大功能之前，先帮你梳理需求、评估风险、制定计划。"
    },
    "PRP Plan": {
        "category": "Commands", "sub": "规划",
        "zh_name": "PRP 规划",
        "zh_desc": "创建全面的功能实现计划，包含详细的验证步骤。",
        "simple": "为一个功能创建详细的实现计划，每一步都有验证方法。"
    },
    "PRP Implement": {
        "category": "Commands", "sub": "规划",
        "zh_name": "PRP 实现",
        "zh_desc": "执行实现计划，进行严格的验证，确保每个步骤正确完成。",
        "simple": "按照计划一步步实现功能，每一步都严格验证。"
    },
    "Product Requirements Document Generator": {
        "category": "Commands", "sub": "规划",
        "zh_name": "PRD 生成器",
        "zh_desc": "交互式 PRD 生成器，以问题为驱动、假设为导向，生成产品需求文档。",
        "simple": "通过问答的方式帮你写出一份完整的产品需求文档。"
    },
    "Phases": {
        "category": "Commands", "sub": "规划",
        "zh_name": "阶段划分",
        "zh_desc": "将工作分解为有序任务，用于有明确目标的复杂功能开发。",
        "simple": "把一个大项目分成几个阶段，按顺序一步步来做。"
    },
    "Steps": {
        "category": "Commands", "sub": "规划",
        "zh_name": "步骤分解",
        "zh_desc": "细粒度任务步骤分解，将复杂任务拆解为可执行的小步骤。",
        "simple": "把一个复杂任务拆成一个个具体的小步骤。"
    },

    # ===== Commands - 版本控制 =====
    "Smart Commit": {
        "category": "Commands", "sub": "版本控制",
        "zh_name": "智能提交",
        "zh_desc": "智能提交命令，用自然语言描述即可自动定位文件并生成规范的提交信息。",
        "simple": "用大白话告诉它你改了什么，它自动帮你生成规范的 git 提交信息。"
    },
    "Create Pull Request": {
        "category": "Commands", "sub": "版本控制",
        "zh_name": "创建 PR",
        "zh_desc": "从当前分支创建 GitHub Pull Request，自动生成 PR 摘要和测试计划。",
        "simple": "一键创建 GitHub Pull Request，自动写好标题、摘要和测试计划。"
    },
    "Checkpoint Command": {
        "category": "Commands", "sub": "版本控制",
        "zh_name": "检查点命令",
        "zh_desc": "在运行后创建、验证或列出工作流检查点，用于保存工作进度。",
        "simple": "在工作过程中设一个「存档点」，方便以后回到这个状态。"
    },

    # ===== Commands - 代码质量 =====
    "Refactor Clean": {
        "category": "Commands", "sub": "代码质量",
        "zh_name": "重构清理",
        "zh_desc": "安全识别和移除死代码，运行分析工具（knip、depcheck、ts-prune）识别未使用的代码并安全删除。",
        "simple": "自动找到项目里没人用的代码，然后安全地删掉。"
    },
    "Quality Gate Command": {
        "category": "Commands", "sub": "代码质量",
        "zh_name": "质量门禁",
        "zh_desc": "运行 ECC 质量流水线，对文件或项目范围进行质量检查，确保代码达到发布标准。",
        "simple": "对代码做一次全面体检，确保质量达标才能发布。"
    },

    # ===== Commands - 文档 =====
    "Update Documentation": {
        "category": "Commands", "sub": "文档",
        "zh_name": "更新文档",
        "zh_desc": "从源文件同步文档，更新 README 和使用指南，保持文档与代码一致。",
        "simple": "代码改了之后，自动更新 README 等文档，保持一致。"
    },
    "Update Codemaps": {
        "category": "Commands", "sub": "文档",
        "zh_name": "更新代码地图",
        "zh_desc": "扫描项目结构并生成精简的架构代码地图，帮助快速理解代码库。",
        "simple": "扫描整个项目，生成一张「代码地图」，帮你快速了解项目结构。"
    },

    # ===== Commands - AI/GAN =====
    "GAN-Style Harness Build": {
        "category": "Commands", "sub": "AI 辅助",
        "zh_name": "GAN 风格构建",
        "zh_desc": "运行生成器/评估器构建循环，实现功能并通过迭代反馈提升质量。",
        "simple": "让两个 AI 互相配合：一个写代码，一个测试评分，反复迭代直到满意。"
    },
    "GAN-Style Design Harness": {
        "category": "Commands", "sub": "AI 辅助",
        "zh_name": "GAN 风格设计",
        "zh_desc": "运行生成器/评估器设计循环，用于前端或后端功能的设计迭代。",
        "simple": "让两个 AI 互相配合做设计：一个出方案，一个评价，反复优化。"
    },

    # ===== Commands - 多模型协作 =====
    "Backend - Backend-Focused Development": {
        "category": "Commands", "sub": "多模型协作",
        "zh_name": "后端开发",
        "zh_desc": "后端专注的多模型开发工作流，针对 API、数据库和服务器端逻辑优化。",
        "simple": "多个 AI 协作帮你写后端代码，专门优化 API 和数据库部分。"
    },
    "Frontend - Frontend-Focused Development": {
        "category": "Commands", "sub": "多模型协作",
        "zh_name": "前端开发",
        "zh_desc": "前端专注的多模型开发工作流，针对组件、样式和用户体验优化。",
        "simple": "多个 AI 协作帮你写前端代码，专门优化界面和用户体验。"
    },
    "Execute - Multi-Model Collaborative Execution": {
        "category": "Commands", "sub": "多模型协作",
        "zh_name": "多模型执行",
        "zh_desc": "执行多模型协作计划，同时保持代码质量和一致性。",
        "simple": "多个 AI 一起动手写代码，分工合作，保持风格统一。"
    },
    "Plan - Multi-Model Collaborative Planning": {
        "category": "Commands", "sub": "多模型协作",
        "zh_name": "多模型规划",
        "zh_desc": "创建多模型协作实现计划，不修改代码，仅做规划。",
        "simple": "多个 AI 一起讨论怎么做，先出方案不动手写代码。"
    },
    "Workflow - Multi-Model Collaborative Development": {
        "category": "Commands", "sub": "多模型协作",
        "zh_name": "多模型工作流",
        "zh_desc": "运行完整的多模型开发工作流，包含研究、规划和实现阶段。",
        "simple": "多个 AI 走完整个开发流程：调研 -> 规划 -> 写代码。"
    },

    # ===== Commands - 循环/自动化 =====
    "Loop Start Command": {
        "category": "Commands", "sub": "自动化",
        "zh_name": "循环启动",
        "zh_desc": "启动托管的自主循环模式，带有安全防护，可定期执行重复任务。",
        "simple": "让 AI 自动重复执行某个任务，比如每 5 分钟检查一次部署状态。"
    },
    "Loop Status Command": {
        "category": "Commands", "sub": "自动化",
        "zh_name": "循环状态",
        "zh_desc": "检查活跃循环的状态、进度和失败信号。",
        "simple": "查看正在运行的自动任务进行到哪了，有没有出错。"
    },
    "Santa Loop": {
        "category": "Commands", "sub": "自动化",
        "zh_name": "对抗性双审循环",
        "zh_desc": "对抗性双审查收敛循环，两个独立审查者交替审查直到达成共识。",
        "simple": "两个 AI 互相挑刺、反复审查，直到双方都觉得没问题。"
    },
    "Model Route Command": {
        "category": "Commands", "sub": "自动化",
        "zh_name": "模型路由",
        "zh_desc": "根据当前任务推荐最佳模型层级（Haiku/Sonnet/Opus），优化成本和效果。",
        "simple": "根据任务难度自动选最合适的 AI 模型，省钱又高效。"
    },

    # ===== Commands - 会话管理 =====
    "Save Session Command": {
        "category": "Commands", "sub": "会话管理",
        "zh_name": "保存会话",
        "zh_desc": "将会话状态保存到 ~/.claude/sessions/ 目录下的日期文件中。",
        "simple": "把当前和 AI 的对话存档，下次可以接着聊。"
    },
    "Resume Session Command": {
        "category": "Commands", "sub": "会话管理",
        "zh_name": "恢复会话",
        "zh_desc": "从 ~/.claude/sessions/ 加载最近的会话文件，恢复之前的工作状态。",
        "simple": "加载上次保存的对话，接着之前的工作继续做。"
    },
    "Sessions Command": {
        "category": "Commands", "sub": "会话管理",
        "zh_name": "会话管理",
        "zh_desc": "管理 Claude Code 会话历史、别名和会话文件。",
        "simple": "管理所有保存过的对话记录，查看、删除或重命名。"
    },

    # ===== Commands - 学习/进化 =====
    "/learn - Extract Reusable Patterns": {
        "category": "Commands", "sub": "学习进化",
        "zh_name": "学习提取",
        "zh_desc": "从当前会话中提取可重用的模式和经验，保存为项目知识。",
        "simple": "从这次对话中总结经验教训，下次遇到类似问题可以直接用。"
    },
    "/learn-eval - Extract, Evaluate, then Save": {
        "category": "Commands", "sub": "学习进化",
        "zh_name": "学习评估",
        "zh_desc": "从会话中提取模式，自我评估质量后再保存，确保知识的准确性。",
        "simple": "总结经验后先自我检查质量，确认靠谱了再保存。"
    },
    "evolve": {
        "category": "Commands", "sub": "学习进化",
        "zh_name": "进化",
        "zh_desc": "分析本能（instincts）并建议或生成进化后的结构，持续改进工作流。",
        "simple": "分析 AI 学到的经验，提出改进建议，让它越来越聪明。"
    },

    # ===== Commands - 直觉系统 =====
    "instinct-status": {
        "category": "Commands", "sub": "直觉系统",
        "zh_name": "直觉状态",
        "zh_desc": "显示已学习的直觉（项目级和全局级）及其置信度分数。",
        "simple": "查看 AI 学到了哪些经验，每条经验的可信度是多少。"
    },
    "instinct-import": {
        "category": "Commands", "sub": "直觉系统",
        "zh_name": "直觉导入",
        "zh_desc": "从文件或 URL 导入直觉到项目或全局范围。",
        "simple": "把别人总结好的经验导入给 AI，让它快速学习。"
    },
    "instinct-export": {
        "category": "Commands", "sub": "直觉系统",
        "zh_name": "直觉导出",
        "zh_desc": "将项目或全局范围的直觉导出到文件。",
        "simple": "把 AI 学到的经验导出成文件，可以分享给别人。"
    },
    "promote": {
        "category": "Commands", "sub": "直觉系统",
        "zh_name": "直觉提升",
        "zh_desc": "将项目级直觉提升为全局级，使其在所有项目中生效。",
        "simple": "把某个项目的经验提升为通用经验，所有项目都能用。"
    },
    "prune": {
        "category": "Commands", "sub": "直觉系统",
        "zh_name": "直觉修剪",
        "zh_desc": "删除超过 30 天的待定直觉，清理过期的学习数据。",
        "simple": "清理过期的经验数据，删掉超过 30 天没确认的。"
    },
    "projects": {
        "category": "Commands", "sub": "直觉系统",
        "zh_name": "项目列表",
        "zh_desc": "列出已知项目及其直觉统计信息。",
        "simple": "列出所有项目，看看每个项目 AI 学到了多少经验。"
    },

    # ===== Commands - 钩子系统 =====
    "Hook System Overview": {
        "category": "Commands", "sub": "钩子系统",
        "zh_name": "钩子系统概览",
        "zh_desc": "钩子系统总览，介绍 PreToolUse、PostToolUse 和 Stop 钩子的配置和使用方法。",
        "simple": "了解钩子系统是什么，怎么设置自动执行的操作。"
    },
    "Harness Audit Command": {
        "category": "Commands", "sub": "钩子系统",
        "zh_name": "工具审计",
        "zh_desc": "运行确定性的仓库工具审计，返回审计报告和改进建议。",
        "simple": "对项目的工具配置做一次审计，告诉你哪里可以改进。"
    },
    "hookify": {
        "category": "Commands", "sub": "钩子系统",
        "zh_name": "钩子生成",
        "zh_desc": "从对话分析或明确指令中创建钩子，防止 unwanted 行为重复发生。",
        "simple": "把你不希望 AI 再犯的错误设为自动规则，下次就不会再犯。"
    },
    "hookify-configure": {
        "category": "Commands", "sub": "钩子系统",
        "zh_name": "钩子配置",
        "zh_desc": "交互式启用或禁用 hookify 规则，管理钩子的行为配置。",
        "simple": "开启或关闭已有的自动规则，调整 AI 的行为。"
    },
    "hookify-list": {
        "category": "Commands", "sub": "钩子系统",
        "zh_name": "钩子列表",
        "zh_desc": "列出所有已配置的 hookify 规则，查看当前钩子配置状态。",
        "simple": "看看目前设了哪些自动规则。"
    },

    # ===== Commands - 集成 =====
    "Jira Command": {
        "category": "Commands", "sub": "集成",
        "zh_name": "Jira 命令",
        "zh_desc": "检索 Jira 工单、分析需求、更新状态，与 Jira 项目管理系统集成。",
        "simple": "直接在 Claude Code 里查看和管理 Jira 工单。"
    },
    "PM2 Init": {
        "category": "Commands", "sub": "集成",
        "zh_name": "PM2 初始化",
        "zh_desc": "分析项目并生成 PM2 进程管理命令，用于生产环境部署。",
        "simple": "帮你配置 PM2 进程管理，方便把项目部署到服务器上运行。"
    },

    # ===== Commands - 其他 =====
    "Aside Command": {
        "category": "Commands", "sub": "其他",
        "zh_name": "旁问命令",
        "zh_desc": "快速回答侧面问题，不中断当前主要工作流程。",
        "simple": "在 AI 忙的时候快速问个小问题，不影响它正在做的事。"
    },
    "Auto Update": {
        "category": "Commands", "sub": "其他",
        "zh_name": "自动更新",
        "zh_desc": "自动检查并更新 Claude Code 的配置和工具到最新版本。",
        "simple": "自动检查 Claude Code 有没有新版本，有的话帮你更新。"
    },
    "skill-create": {
        "category": "Commands", "sub": "其他",
        "zh_name": "技能创建",
        "zh_desc": "分析本地 git 历史以提取编码模式，创建可复用的技能定义。",
        "simple": "从你的代码提交记录中总结编码习惯，做成可复用的技能。"
    },
    "skill-health": {
        "category": "Commands", "sub": "其他",
        "zh_name": "技能健康",
        "zh_desc": "显示技能组合健康仪表板，包含图表和使用统计。",
        "simple": "看看你安装的技能（插件）运行状态好不好。"
    },

    # ===== Agents - 无障碍 =====
    "a11y-architect": {
        "category": "Agents", "sub": "代码审查",
        "zh_name": "无障碍架构师",
        "zh_desc": "无障碍架构专家。专注于 WCAG 2.2 合规性，在设计 UI 组件、建立设计系统或审计包容性用户体验时主动使用。",
        "simple": "确保你的网站/APP 让残障人士也能正常使用，比如屏幕阅读器兼容。"
    },

    # ===== Legacy =====
    "Legacy Command Shims": {
        "category": "Legacy Commands", "sub": "兼容",
        "zh_name": "旧版命令兼容层",
        "zh_desc": "旧版命令的兼容性垫片，确保已弃用的命令仍可使用，提供平滑迁移路径。",
        "simple": "让老版本的命令还能继续用，不会因为升级就用不了。"
    },
}

SUB_ORDER = {
    "Agents": ["代码审查", "构建修复", "架构规划", "测试", "安全", "文档", "性能优化", "代码质量", "AI 辅助", "运维辅助"],
    "Commands": ["代码审查", "构建修复", "测试", "规划", "版本控制", "代码质量", "文档", "AI 辅助", "多模型协作", "自动化", "会话管理", "学习进化", "直觉系统", "钩子系统", "集成", "其他"],
    "Legacy Commands": ["兼容"],
}

def fetch_md_files(dir_name):
    if requests is None:
        raise RuntimeError("缺少 requests 依赖，请先运行 python3 -m pip install requests")
    api_url = f"https://api.github.com/repos/affaan-m/everything-claude-code/contents/{dir_name}"
    r = requests.get(api_url)
    r.raise_for_status()
    return [f for f in r.json() if f['name'].endswith(".md")]

def parse_md_file(file_url):
    if requests is None:
        raise RuntimeError("缺少 requests 依赖，请先运行 python3 -m pip install requests")
    r = requests.get(file_url)
    r.raise_for_status()
    content = r.text
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    name, description = None, ""
    body = content
    if fm_match:
        fm_text = fm_match.group(1)
        body = content[fm_match.end():]
        for line in fm_text.splitlines():
            line = line.strip()
            if line.startswith("name:") and not name:
                name = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("description:") and not description:
                description = line.split(":", 1)[1].strip().strip('"').strip("'")
    if not name:
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("#"):
                name = line.lstrip("# ").strip()
                break
    if not name:
        name = "未命名"
    if not description:
        for line in body.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("```"):
                description = line
                break
    if len(description) > 200:
        description = description[:200] + "..."
    return name, description

DIRECTORIES = {
    "Agents": "agents",
    "Commands": "commands",
    "Legacy Commands": "legacy-command-shims"
}

TASK_RULES = [
    ("代码审查", ["review", "code-review", "reviewer"], ["代码审查", "提交前", "质量检查", "看看代码有没有问题"], ["高频", "提交前", "会读代码"]),
    ("修复构建", ["build", "resolver", "gradle"], ["构建失败", "编译不过", "报错", "依赖冲突", "跑不起来"], ["高频", "会修改代码", "故障处理"]),
    ("测试质量", ["test", "tdd", "coverage", "e2e"], ["测试", "覆盖率", "端到端", "回归测试", "先写测试"], ["提交前", "质量保障"]),
    ("功能规划", ["planner", "architect", "plan", "prd", "feature"], ["规划", "架构", "需求拆解", "技术方案", "功能开发"], ["入门推荐", "只读分析"]),
    ("文档资料", ["doc", "docs", "codemap"], ["文档", "README", "代码地图", "查资料", "同步文档"], ["高频", "文档"]),
    ("安全合规", ["security", "opensource", "healthcare"], ["安全", "开源", "合规", "密钥", "隐私", "漏洞"], ["发布前", "需要谨慎"]),
    ("多模型协作", ["multi", "gan", "santa"], ["多模型", "协作", "反复迭代", "复杂任务"], ["进阶", "适合复杂任务"]),
    ("会话与学习", ["session", "learn", "instinct", "evolve", "checkpoint"], ["会话", "经验", "学习", "检查点", "恢复上下文"], ["效率提升", "长期项目"]),
]

BEGINNER_KEYS = {
    "planner", "architect", "code-reviewer", "build-error-resolver", "docs-lookup",
    "doc-updater", "security-reviewer", "refactor-cleaner", "test-coverage",
    "prp-commit", "multi-plan", "feature-dev", "update-docs", "quality-gate"
}

FREQUENT_KEYS = {
    "code-reviewer", "typescript-reviewer", "python-reviewer", "build-error-resolver",
    "planner", "docs-lookup", "doc-updater", "security-reviewer", "quality-gate",
    "test-coverage", "prp-commit", "refactor-cleaner", "update-docs", "build-fix"
}

READ_ONLY_HINTS = ["review", "docs", "lookup", "plan", "architect", "status", "list", "coverage", "audit"]
CODE_CHANGE_HINTS = ["fix", "build", "resolver", "clean", "update", "implement", "packager", "forker", "sanitizer"]

def enrich_entry(entry):
    """补充中文开发者更容易使用的场景化字段"""
    key = entry.get("original", "")
    key_lower = key.lower()
    task_groups = []
    keywords = []
    tags = []
    for task, needles, words, task_tags in TASK_RULES:
        if entry.get("sub") == task or any(n in key_lower for n in needles):
            task_groups.append(task)
            keywords.extend(words)
            tags.extend(task_tags)
    if not task_groups:
        task_groups.append(entry.get("sub", "其他"))
        keywords.extend([entry.get("sub", ""), entry.get("category", "")])
    if key_lower in BEGINNER_KEYS:
        tags.append("入门推荐")
    if key_lower in FREQUENT_KEYS:
        tags.append("高频")
    if any(h in key_lower for h in CODE_CHANGE_HINTS):
        tags.append("可能改代码")
    elif any(h in key_lower for h in READ_ONLY_HINTS):
        tags.append("偏分析")

    primary_task = task_groups[0]
    use_case = {
        "代码审查": "写完或修改代码后，用它从规范、风险和可维护性角度做一次复查。",
        "修复构建": "项目编译、构建、类型检查或依赖安装失败时，用它定位并修复必要问题。",
        "测试质量": "需要补测试、跑端到端流程、检查覆盖率或防止回归时使用。",
        "功能规划": "需求还不够清楚、要拆任务或设计实现路径时，先用它做方案。",
        "文档资料": "需要查 API、同步 README、生成代码地图或解释项目结构时使用。",
        "安全合规": "涉及登录、权限、敏感数据、开源发布或合规检查时使用。",
        "多模型协作": "任务较复杂、需要多轮规划/实现/评审收敛时使用。",
        "会话与学习": "需要保存上下文、沉淀经验、恢复工作或管理长期项目记忆时使用。",
    }.get(primary_task, "不确定该命令是否合适时，可以先读说明，再用更具体的中文目标调用它。")
    avoid_case = {
        "修复构建": "只是想了解概念或讨论方案时，不必优先使用修复类命令。",
        "安全合规": "没有安全、隐私或发布风险时，可以先用普通代码审查。",
        "多模型协作": "小改动和单文件问题通常不需要启动复杂协作流程。",
    }.get(primary_task, "如果只是闲聊或问一个概念，直接提问通常比调用命令更快。")
    recommended_prompt = f'{entry["slash_command"]} 请结合当前项目，说明适用范围、关键风险，并给出可执行建议。'

    entry["task_groups"] = sorted(set(task_groups))
    entry["keywords"] = sorted(set([k for k in keywords if k]))
    entry["tags"] = sorted(set(tags))
    entry["use_case"] = use_case
    entry["avoid_case"] = avoid_case
    entry["recommended_prompt"] = recommended_prompt
    return entry

def build_entry(name, description, category, file_key):
    """从翻译数据或原始数据构建一个条目"""
    original = name
    if name in ("Usage", "Steps", "---", "未命名", "Overview"):
        name = file_key
        original = file_key
    tr = TRANSLATIONS.get(name) or TRANSLATIONS.get(file_key)
    if tr:
        return {
            "category": tr["category"], "sub": tr["sub"],
            "name": tr["zh_name"], "original": original,
            "description": tr["zh_desc"], "simple": tr["simple"],
            "slash_command": f'/plan "{original}"'
        }
    return {
        "category": category, "sub": "其他",
        "name": original, "original": original,
        "description": description or "暂无中文描述",
        "simple": "暂无简介，待补充",
        "slash_command": f'/plan "{original}"'
    }

def fetch_all_entries():
    """全量抓取所有条目"""
    all_entries = []
    for category, dir_path in DIRECTORIES.items():
        try:
            md_files = fetch_md_files(dir_path)
        except Exception as e:
            print(f"获取目录 {dir_path} 失败: {e}")
            continue
        for f in md_files:
            download_url = f['download_url']
            try:
                name, description = parse_md_file(download_url)
            except Exception as e:
                print(f"解析文件 {f['name']} 失败: {e}")
                continue
            file_key = f['name'].replace(".md", "")
            all_entries.append(build_entry(name, description, category, file_key))
    return all_entries

def fetch_repo_file_keys():
    """从 GitHub API 获取每个目录的最新文件列表，返回 {dir_name: [file_key, ...]}"""
    repo_files = {}
    for category, dir_path in DIRECTORIES.items():
        try:
            md_files = fetch_md_files(dir_path)
            repo_files[dir_path] = [f['name'].replace(".md", "") for f in md_files]
        except Exception as e:
            print(f"获取目录 {dir_path} 失败: {e}")
            repo_files[dir_path] = []
    return repo_files

def update_entries(existing_entries, existing_meta):
    """增量更新：对比 GitHub 最新文件与已有数据，新增/删除/保留"""
    existing_map = {e["original"]: e for e in existing_entries}
    old_files = existing_meta.get("repo_files", {})

    print("正在从 GitHub 获取最新文件列表...")
    new_files = fetch_repo_file_keys()

    added, removed = [], []

    for dir_path, file_keys in new_files.items():
        category = [k for k, v in DIRECTORIES.items() if v == dir_path][0]
        old_keys = set(old_files.get(dir_path, []))
        new_keys = set(file_keys)

        # 新增的文件
        for fk in new_keys - old_keys:
            print(f"  发现新增: {fk}")
            try:
                api_url = f"https://api.github.com/repos/affaan-m/everything-claude-code/contents/{dir_path}/{fk}.md"
                r = requests.get(api_url)
                r.raise_for_status()
                name, description = parse_md_file(r.json()['download_url'])
                entry = build_entry(name, description, category, fk)
                existing_map[fk] = entry
                added.append(fk)
            except Exception as e:
                print(f"  解析新增文件 {fk} 失败: {e}")

        # 删除的文件
        for fk in old_keys - new_keys:
            if fk in existing_map:
                print(f"  移除已删除: {fk}")
                del existing_map[fk]
                removed.append(fk)

    entries = list(existing_map.values())
    new_meta = {
        "last_updated": datetime.now().isoformat(),
        "repo_files": new_files
    }
    return entries, new_meta, added, removed

def sort_key(e):
    cat = e["category"]
    sub = e["sub"]
    sub_list = SUB_ORDER.get(cat, [])
    idx = sub_list.index(sub) if sub in sub_list else 999
    return (cat, idx, e["name"])

def save_data(entries, meta=None):
    """保存数据到 JSON，_meta 作为第一条元素"""
    payload = entries
    if meta:
        payload = [{"_meta": meta}] + entries
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_data():
    """从 JSON 读取数据，分离 _meta 和条目"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    meta, entries = {}, []
    for item in raw:
        if isinstance(item, dict) and "_meta" in item:
            meta = item["_meta"]
        else:
            entries.append(item)
    return entries, meta

# -----------------------------
# 主流程
# -----------------------------
parser = argparse.ArgumentParser(description="ECC 中文命令中心生成器")
parser.add_argument("--local", action="store_true", help="本地重建：使用现有 data.json 重新生成网页，不访问 GitHub")
parser.add_argument("--update", action="store_true", help="增量更新：从 GitHub 拉取最新文件，保留已有翻译")
args = parser.parse_args()

if args.local:
    if not DATA_FILE.exists():
        print("data.json 不存在，无法本地重建")
        sys.exit(1)
    all_entries, meta = load_data()
    print(f"本地重建模式，读取 {len(all_entries)} 条记录")
elif args.update:
    if not DATA_FILE.exists():
        print("data.json 不存在，将执行全量抓取...")
        all_entries = fetch_all_entries()
        meta = {"last_updated": datetime.now().isoformat(), "repo_files": fetch_repo_file_keys()}
    else:
        existing_entries, existing_meta = load_data()
        print(f"已有 {len(existing_entries)} 条记录，正在检查更新...")
        all_entries, meta, added, removed = update_entries(existing_entries, existing_meta)
        print(f"新增 {len(added)} 条，移除 {len(removed)} 条")
else:
    print("全量抓取模式...")
    all_entries = fetch_all_entries()
    meta = {"last_updated": datetime.now().isoformat(), "repo_files": fetch_repo_file_keys()}

all_entries = [enrich_entry(e) for e in all_entries]
all_entries.sort(key=sort_key)
save_data(all_entries, meta)
print(f"已生成数据，共 {len(all_entries)} 条记录 -> {DATA_FILE}")

# ----------------------------- HTML -----------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ECC 中文命令中心</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#172033;--muted:#607086;--line:#dfe7ee;--teal:#0e7484;--green:#2e8b68;--amber:#c98716;--paper:#fffdf8;--soft:#f5f8fa}
body{font-family:"Microsoft YaHei","PingFang SC","Helvetica Neue",sans-serif;background:linear-gradient(180deg,#f7f2e8 0,#f4f7f8 360px,#eef3f6 100%);color:var(--ink)}
.hero{position:relative;min-height:330px;background-image:linear-gradient(90deg,rgba(255,253,248,.96) 0%,rgba(255,253,248,.9) 34%,rgba(255,253,248,.54) 58%,rgba(255,253,248,.18) 100%),url("./assets/hero-command-center.png");background-size:cover;background-position:center;color:var(--ink);overflow:hidden}
.hero-inner{max-width:1180px;margin:0 auto;padding:54px 20px 34px}
.eyebrow{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid rgba(14,116,132,.28);border-radius:999px;background:rgba(255,255,255,.72);color:#0d6675;font-size:12px;font-weight:700}
.hero h1{max-width:560px;font-size:42px;line-height:1.12;margin:18px 0 12px;letter-spacing:0}
.hero p{max-width:560px;font-size:15px;line-height:1.8;color:#3b4b5f}
.hero-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}
.hero-chip{border:1px solid rgba(14,116,132,.22);background:rgba(255,255,255,.76);border-radius:999px;padding:7px 12px;color:#244154;font-size:12px}
.toolbar{background:rgba(255,255,255,.95);backdrop-filter:blur(14px);padding:16px 20px;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:100;box-shadow:0 12px 28px rgba(23,32,51,.08)}
.toolbar-inner{max-width:1180px;margin:0 auto}
.toolbar-top{display:grid;grid-template-columns:minmax(260px,1fr) auto;gap:14px;align-items:center}
.nav-label{font-size:13px;font-weight:800;color:#123c49;margin:14px 0 9px;display:flex;align-items:center;gap:8px}
.nav-label::before{content:"";width:4px;height:16px;border-radius:999px;background:linear-gradient(180deg,var(--teal),var(--green))}
.nav-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:10px}
#search{width:100%;padding:13px 15px;font-size:15px;border:1px solid #cbd6df;border-radius:10px;outline:none;background:#fff;box-shadow:inset 0 1px 0 rgba(255,255,255,.8)}
#search:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(14,116,132,.13)}
.filter-btn,.copy-btn,.update-btn{padding:11px 14px;font-size:14px;font-weight:700;border:1px solid #cbd6df;border-radius:10px;background:#fff;cursor:pointer;transition:all .15s;color:#263445;min-height:44px}
.filter-btn:hover,.update-btn:hover{border-color:var(--teal);color:var(--teal);background:#f4fbfc}
.filter-btn.active{background:var(--teal);color:#fff;border-color:var(--teal);box-shadow:0 6px 16px rgba(14,116,132,.2)}
.container{max-width:1180px;margin:0 auto;padding:18px}
.panel{background:rgba(255,255,255,.86);border:1px solid var(--line);border-radius:8px;padding:17px;margin-bottom:14px;box-shadow:0 10px 28px rgba(23,32,51,.05)}
.panel h2{font-size:17px;margin-bottom:11px;color:#123c49}
.task-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:11px}
.task-card{position:relative;border:1px solid var(--line);border-radius:8px;padding:13px 13px 13px 16px;background:#fff;cursor:pointer;overflow:hidden;transition:transform .15s,border-color .15s,box-shadow .15s}
.task-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,var(--teal),var(--green))}
.task-card:hover{transform:translateY(-1px);border-color:#9bc7cf;box-shadow:0 10px 22px rgba(14,116,132,.11)}
.task-title{font-weight:700;font-size:14px;color:#162233}
.task-desc{font-size:12px;color:var(--muted);line-height:1.55;margin-top:5px}
.workflow-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:11px}
.workflow{border:1px solid #d7e6df;background:linear-gradient(180deg,#fbfefb,#f3faf5);border-radius:8px;padding:13px}
.workflow-name{font-weight:700;font-size:14px;color:#173b31}
.workflow-steps{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.step-pill{font-size:12px;color:#275343;background:#fff;border:1px solid #d8eadf;border-radius:999px;padding:4px 8px}
.scenario-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:12px}
.scenario-card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px;box-shadow:0 8px 20px rgba(23,32,51,.04)}
.scenario-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:8px}
.scenario-title{font-size:15px;font-weight:800;color:#172033}
.scenario-kind{font-size:11px;color:#80530f;background:#fff7e6;border:1px solid #f1d8a4;border-radius:999px;padding:3px 8px;white-space:nowrap}
.scenario-problem{font-size:13px;color:#4b5a6d;line-height:1.65;margin-bottom:9px}
.scenario-row{font-size:12px;color:#526276;line-height:1.65;margin-top:7px}
.scenario-row strong{color:#203246}
.scenario-prompt{margin-top:10px;background:#f4f7f8;border:1px solid #dfe8ee;border-radius:7px;padding:9px;font-size:12px;color:#243348;line-height:1.6}
.scenario-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.mini-btn{border:1px solid #cbd6df;background:#fff;border-radius:7px;padding:6px 10px;font-size:12px;color:#263445;cursor:pointer}
.mini-btn:hover{border-color:var(--teal);color:var(--teal);background:#f4fbfc}
.stats{display:flex;gap:10px;margin:-34px 0 16px;flex-wrap:wrap;position:relative;z-index:2}
.stat{background:rgba(255,255,255,.92);border-radius:8px;padding:12px 17px;border:1px solid var(--line);text-align:center;min-width:96px;box-shadow:0 12px 30px rgba(23,32,51,.06)}
.stat-num{font-size:24px;font-weight:700;color:var(--teal)}
.stat-label{font-size:12px;color:var(--muted);margin-top:2px}
.cat-header{font-size:18px;font-weight:700;color:#123c49;margin:25px 0 10px;padding-bottom:7px;border-bottom:2px solid var(--teal);display:flex;align-items:center;gap:8px}
.cat-header .badge{font-size:12px;background:var(--teal);color:#fff;padding:2px 8px;border-radius:10px}
.sub-header{font-size:14px;font-weight:700;color:#49586b;margin:16px 0 8px;padding-left:4px}
.card{background:rgba(255,255,255,.94);border-radius:8px;padding:16px;margin-bottom:10px;border:1px solid var(--line);transition:box-shadow .15s,border-color .15s,transform .15s}
.card:hover{transform:translateY(-1px);box-shadow:0 12px 28px rgba(23,32,51,.08);border-color:#bfd5df}
.card-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.card-name{font-size:15px;font-weight:700;color:#111827}
.card-original{font-size:11px;color:#8492a6;font-family:monospace;margin-top:2px}
.tags{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.tag{font-size:11px;color:#0d5461;background:#e9f6f7;border:1px solid #cce8ec;border-radius:999px;padding:3px 8px;white-space:nowrap}
.card-simple{font-size:14px;color:#0d5c6a;background:linear-gradient(90deg,#edf8fa,#f7fbf7);border-radius:7px;padding:9px 12px;margin-top:11px;line-height:1.5;border:1px solid #dceff1}
.card-desc,.guide{font-size:13px;color:#4b5563;line-height:1.6;margin-top:8px}
.guide strong{color:#263445}
.card-cmd{display:flex;align-items:center;gap:8px;margin-top:10px}
.card-cmd code{background:#f3f6f8;padding:7px 10px;border-radius:6px;font-size:12px;color:#253040;font-family:"Cascadia Code","Fira Code",monospace;flex:1;overflow:auto;border:1px solid #e1e8ee}
.copy-btn{background:var(--teal);color:#fff;border-color:var(--teal);white-space:nowrap}
.copy-btn:hover{background:#0b5d69}
.reference-box{margin-top:11px;border:1px solid #d9e6ec;border-radius:8px;background:#fbfdfd;overflow:hidden}
.reference-box summary{cursor:pointer;padding:9px 12px;font-size:13px;font-weight:700;color:#174957;list-style:none}
.reference-box summary::-webkit-details-marker{display:none}
.reference-box summary::after{content:"展开";float:right;color:var(--teal);font-size:12px;font-weight:600}
.reference-box[open] summary::after{content:"收起"}
.reference-detail{border-top:1px solid #d9e6ec;padding:12px;color:#405064;font-size:13px;line-height:1.75}
.reference-detail h3{font-size:14px;color:#21624f;margin:10px 0 5px}
.reference-detail h4{font-size:13px;color:#8a5a12;margin:9px 0 4px}
.reference-detail p,.reference-detail li{margin-bottom:4px}
.reference-detail ul,.reference-detail ol{padding-left:20px;margin:5px 0 8px}
.reference-detail table{width:100%;border-collapse:collapse;margin:8px 0;font-size:12px;background:#fff}
.reference-detail th,.reference-detail td{border:1px solid #dfe7ee;padding:6px;text-align:left}
.reference-detail th{background:#f0f6f7;color:#0d5461}
.reference-detail code{background:#eef4f6;border:1px solid #dce8ec;border-radius:4px;padding:1px 5px;color:#0d6675}
.reference-en{margin-top:8px;padding-left:10px;border-left:3px solid #d8e4ea;color:#6b7b8f;font-size:12px}
.ref-library{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}
.ref-item{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px}
.ref-meta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
.ref-kind{font-size:11px;background:#edf8fa;color:#0d5c6a;border:1px solid #d3ebef;border-radius:999px;padding:2px 7px}
.ref-name{font-weight:700;color:#172033;font-family:"Cascadia Code","Fira Code",monospace;font-size:13px}
.ref-brief{font-size:12px;color:var(--muted);line-height:1.55}
.empty{text-align:center;color:var(--muted);padding:36px;font-size:14px;background:#fff;border:1px solid var(--line);border-radius:8px}
.update-bar{display:flex;align-items:center;gap:10px;white-space:nowrap;justify-content:flex-end}
.last-updated{font-size:11px;color:#64748b}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;z-index:999;opacity:0;transition:opacity .3s;pointer-events:none}
.toast.show{opacity:1}.toast.ok{background:var(--green)}.toast.warn{background:var(--amber)}.toast.info{background:var(--teal)}
@media(max-width:760px){.hero{min-height:300px;background-position:62% center}.hero-inner{padding:38px 18px 30px}.hero h1{font-size:31px}.stats{margin:0 0 14px}.toolbar{position:static}.toolbar-top{grid-template-columns:1fr}.update-bar{justify-content:flex-start}.nav-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.card-head{display:block}.tags{justify-content:flex-start;margin-top:8px}.card-cmd{align-items:stretch;flex-direction:column}.update-bar{margin-left:0}.hero-actions{gap:8px}}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <div class="eyebrow">Everything Claude Code 中文导航</div>
    <h1>把 Skill 变成中文开发者的高效工作台</h1>
    <p>按任务找命令，按工作流组合使用。从代码审查、构建修复、测试质量到文档与安全，把每个命令该怎么用讲清楚。</p>
    <div class="hero-actions">
      <span class="hero-chip">任务导航</span>
      <span class="hero-chip">推荐工作流</span>
      <span class="hero-chip">中文场景搜索</span>
      <span class="hero-chip">一键复制用法</span>
    </div>
  </div>
</header>
<div class="toolbar">
  <div class="toolbar-inner">
    <div class="toolbar-top">
      <input type="text" id="search" placeholder="搜索：编译不过、提交前、安全、写测试、规划、文档..." oninput="render()">
      <div class="update-bar">
        <span class="last-updated" id="lastUpdated"></span>
        <button class="update-btn" id="updateBtn" onclick="checkUpdate()">检查更新</button>
      </div>
    </div>
    <div class="nav-label">快速导航</div>
    <div class="nav-grid">
      <button class="filter-btn active" data-filter="all" onclick="setFilter('all',this)">全部</button>
      <button class="filter-btn" data-filter="scenarios" onclick="setFilter('scenarios',this)">场景案例</button>
      <button class="filter-btn" data-filter="入门推荐" onclick="setFilter('tag:入门推荐',this)">新手推荐</button>
      <button class="filter-btn" data-filter="高频" onclick="setFilter('tag:高频',this)">高频命令</button>
      <button class="filter-btn" data-filter="代码审查" onclick="setFilter('task:代码审查',this)">代码审查</button>
      <button class="filter-btn" data-filter="修复构建" onclick="setFilter('task:修复构建',this)">修复构建</button>
      <button class="filter-btn" data-filter="功能规划" onclick="setFilter('task:功能规划',this)">功能规划</button>
      <button class="filter-btn" data-filter="文档资料" onclick="setFilter('task:文档资料',this)">文档资料</button>
      <button class="filter-btn" data-filter="reference" onclick="setFilter('reference',this)">原参考库</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<div class="container" id="app"></div>
<script>
const TASKS=[
  {name:'代码审查',desc:'改完代码后检查类型、安全、性能和可维护性'},
  {name:'修复构建',desc:'编译不过、依赖冲突、类型检查失败时快速定位'},
  {name:'测试质量',desc:'补测试、跑端到端流程、检查覆盖率'},
  {name:'功能规划',desc:'需求拆解、架构设计、实现路线'},
  {name:'文档资料',desc:'查资料、更新 README、生成代码地图'},
  {name:'安全合规',desc:'登录权限、敏感数据、开源发布前检查'},
  {name:'多模型协作',desc:'复杂任务用规划、执行、评审组合推进'},
  {name:'会话与学习',desc:'保存上下文、沉淀经验、恢复长期工作'}
];
const WORKFLOWS=[
  {name:'新功能开发',steps:['multi-plan','feature-dev','code-reviewer','test-coverage','prp-commit']},
  {name:'构建失败修复',steps:['build-error-resolver','quality-gate','code-reviewer']},
  {name:'提交前检查',steps:['code-reviewer','security-reviewer','test-coverage','prp-commit']},
  {name:'开源发布准备',steps:['opensource-forker','opensource-sanitizer','opensource-packager']},
  {name:'文档同步',steps:['update-codemaps','update-docs','docs-lookup']}
];
const SCENARIOS=[
  {
    kind:'从 0 到 1',
    title:'我要做一个新功能，但需求还比较模糊',
    problem:'适合需求只有一句话、边界不清楚、担心直接开写返工的情况。',
    steps:['planner','code-architect','feature-dev','test-coverage','code-reviewer'],
    prompt:'/plan "planner" 我想做一个用户邀请功能，请先帮我拆需求、识别风险、规划实现步骤，不要直接改代码。',
    output:'一份可执行计划：任务拆分、涉及文件、风险点、验收标准。'
  },
  {
    kind:'故障处理',
    title:'项目突然编译不过或测试红了',
    problem:'适合构建失败、类型错误、依赖冲突、CI 红灯，但还不知道根因在哪里。',
    steps:['build-error-resolver','quality-gate','code-reviewer'],
    prompt:'/plan "build-error-resolver" 当前项目构建失败，请先定位根因，再用最小改动修复，最后说明验证命令。',
    output:'根因说明、最小修复、验证结果和后续风险。'
  },
  {
    kind:'提交前',
    title:'我要提交代码，想做一次靠谱的自查',
    problem:'适合 PR 前、上线前、或改动涉及多个文件时，避免低级问题进入仓库。',
    steps:['code-reviewer','security-reviewer','test-coverage','prp-commit'],
    prompt:'/plan "code-reviewer" 请审查我当前改动，重点看正确性、可维护性、安全风险和缺失测试。',
    output:'按严重程度排序的问题清单、建议修复、提交建议。'
  },
  {
    kind:'测试补齐',
    title:'我不确定哪些地方该补测试',
    problem:'适合业务逻辑变复杂、修 bug 后想防回归、或者覆盖率只看数字不看行为的情况。',
    steps:['pr-test-analyzer','tdd-guide','e2e-runner','test-coverage'],
    prompt:'/plan "pr-test-analyzer" 请分析当前改动缺少哪些行为测试，优先给出能防真实 bug 的测试用例。',
    output:'测试缺口、测试优先级、具体用例和执行方式。'
  },
  {
    kind:'代码变乱',
    title:'功能能跑，但代码已经不好维护',
    problem:'适合长函数、重复逻辑、命名不清、注释过时、类型设计混乱等问题。',
    steps:['code-simplifier','type-design-analyzer','comment-analyzer','refactor-cleaner'],
    prompt:'/plan "code-simplifier" 请只针对最近修改的代码做简化建议，保持行为不变，避免大范围重构。',
    output:'可控范围内的简化建议、风险说明、验证方式。'
  },
  {
    kind:'安全发布',
    title:'涉及登录、权限、密钥或开源发布',
    problem:'适合认证授权、用户输入、敏感数据、环境变量、开源前清理等高风险场景。',
    steps:['security-reviewer','opensource-sanitizer','opensource-packager'],
    prompt:'/plan "security-reviewer" 请检查当前项目是否存在密钥泄露、输入校验、权限绕过和 OWASP 常见风险。',
    output:'安全风险分级、修复建议、发布前检查清单。'
  },
  {
    kind:'文档维护',
    title:'代码改了，文档和项目理解跟不上',
    problem:'适合新成员接手、项目结构变化、README 过时、需要快速理解架构。',
    steps:['code-explorer','update-codemaps','update-docs','docs-lookup'],
    prompt:'/plan "doc-updater" 请根据当前代码同步 README 和代码地图，重点说明入口、模块职责和常用命令。',
    output:'更新后的文档结构、代码地图、关键入口说明。'
  },
  {
    kind:'复杂协作',
    title:'任务太大，想让多个模型分工推进',
    problem:'适合跨前后端、需要调研+规划+实现+评审的复杂需求。',
    steps:['multi-plan','multi-execute','santa-loop','quality-gate'],
    prompt:'/plan "Plan - Multi-Model Collaborative Planning" 请为这个跨前后端需求制定多模型协作计划，明确每一步产出和验收标准。',
    output:'多阶段协作计划、角色分工、执行顺序和质量门禁。'
  }
];
let entries=[];
let references=[];
let meta={};
const EMBEDDED_ENTRIES=__EMBEDDED_ENTRIES__;
const EMBEDDED_META=__EMBEDDED_META__;
const EMBEDDED_REFERENCES=__EMBEDDED_REFERENCES__;
let currentFilter='all';
function setFilter(f,btn){currentFilter=f;document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));if(btn)btn.classList.add('active');render()}
function setTaskFilter(name){currentFilter='task:'+name;document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.dataset.filter===name));render()}
function showToast(msg,type){const t=document.getElementById('toast');t.textContent=msg;t.className='toast show '+type;setTimeout(()=>t.classList.remove('show'),3000)}
function escapeHtml(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function copyCommand(cmd){navigator.clipboard.writeText(cmd).then(()=>showToast('已复制推荐用法','ok'))}
function renderUpdatedTime(){
  if(!meta.last_updated)return;
  const d=new Date(meta.last_updated);
  document.getElementById('lastUpdated').textContent='数据更新: '+d.toLocaleDateString('zh-CN')+' '+d.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});
}
// 检查 GitHub 更新
const REPO_DIRS={Agents:'agents',Commands:'commands','Legacy Commands':'legacy-command-shims'};
async function checkUpdate(){
  const btn=document.getElementById('updateBtn');
  btn.disabled=true;btn.textContent='检查中...';
  try {
    const existing=new Set(entries.map(e=>e.original));
    let newFiles=[];
    for(const[cat,dir]of Object.entries(REPO_DIRS)){
      const resp=await fetch(`https://api.github.com/repos/affaan-m/everything-claude-code/contents/${dir}`);
      if(resp.status===403){
        throw new Error('GitHub 匿名 API 被限流或拒绝。线上数据会通过 GitHub Actions 自动同步，也可以稍后再试。');
      }
      if(!resp.ok)throw new Error('GitHub API 请求失败: '+resp.status);
      const files=await resp.json();
      for(const f of files){
        if(f.name.endsWith('.md')){
          const key=f.name.replace('.md','');
          if(!existing.has(key))newFiles.push({name:key,category:cat,dir});
        }
      }
    }
    if(newFiles.length){
      let detail=newFiles.map(f=>`  [${f.category}] ${f.name}`).join('\\n');
      showToast(`发现 ${newFiles.length} 个新条目！`,'warn');
      alert(`发现 ${newFiles.length} 个新条目。线上仓库会由 Update ECC Data 工作流定时同步，也可以手动运行：\\n\\npython3 ecc_cn_command_center.py --update\\n\\n新增文件：\\n${detail}`);
    } else {
      showToast('已是最新，没有发现新条目','ok');
    }
  } catch(e) {
    showToast(e.message,'info');
  } finally {
    btn.disabled=false;btn.textContent='检查更新';
  }
}
async function loadData(){
  try{
    const [resp,refResp]=await Promise.all([fetch('./data.json'),fetch('./reference-data.json')]);
    const raw=await resp.json();
    references=await refResp.json();
    meta=(raw.find(x=>x._meta)||{})._meta||{};
    entries=raw.filter(x=>!x._meta);
  }catch(e){
    entries=EMBEDDED_ENTRIES;
    references=EMBEDDED_REFERENCES;
    meta=EMBEDDED_META;
    showToast('已使用内置数据，建议用静态服务器或 GitHub Pages 访问','info');
  }
  renderUpdatedTime();
  render();
}
function normKey(s){return String(s||'').toLowerCase().replace(/^\\//,'').replace(/[^a-z0-9]+/g,'')}
const REF_ALIASES={
  'Build and Fix':'build-fix','Code Review':'code-review','C++ Code Review':'cpp-review','Flutter Code Review':'flutter-review','Go Code Review':'go-review','Kotlin Code Review':'kotlin-review','Python Code Review':'python-review','Rust Code Review':'rust-review',
  'C++ Build and Fix':'cpp-build','Flutter Build and Fix':'flutter-build','Go Build and Fix':'go-build','Gradle Build Fix':'gradle-build','Kotlin Build and Fix':'kotlin-build','Rust Build and Fix':'rust-build',
  'C++ TDD Command':'cpp-test','Go TDD Command':'go-test','Kotlin TDD Command':'kotlin-test','Rust TDD Command':'rust-test','Flutter Test':'flutter-test','Test Coverage':'test-coverage',
  'Plan Command':'plan','Product Requirements Document Generator':'prp-prd','PRP Implement':'prp-implement','PRP Plan':'prp-plan','Create Pull Request':'prp-pr','Smart Commit':'prp-commit',
  'Checkpoint Command':'checkpoint','Quality Gate Command':'quality-gate','Refactor Clean':'refactor-clean','Update Codemaps':'update-codemaps','Update Documentation':'update-docs',
  'GAN-Style Harness Build':'gan-build','GAN-Style Design Harness':'gan-design','Frontend - Frontend-Focused Development':'multi-frontend','Backend - Backend-Focused Development':'multi-backend',
  'Workflow - Multi-Model Collaborative Development':'multi-workflow','Execute - Multi-Model Collaborative Execution':'multi-execute','Plan - Multi-Model Collaborative Planning':'multi-plan',
  'Santa Loop':'santa-loop','Loop Start Command':'loop-start','Loop Status Command':'loop-status','Model Route Command':'model-route','Sessions Command':'sessions','Save Session Command':'save-session','Resume Session Command':'resume-session',
  'Harness Audit Command':'harness-audit','Hook System Overview':'hookify-help','Jira Command':'jira','PM2 Init':'pm2','Aside Command':'aside','Auto Update':'auto-update','Package Manager Setup':'setup-pm'
};
function referenceIndex(){
  const m=new Map();
  references.forEach(r=>{
    m.set(normKey(r.n),r);
    if(r.n&&r.n.startsWith('/'))m.set(normKey(r.n.slice(1)),r);
  });
  return m;
}
function findReference(e){
  const idx=referenceIndex();
  const candidates=[e.original,e.name,e.slash_command,REF_ALIASES[e.original],REF_ALIASES[e.name]].filter(Boolean);
  for(const c of candidates){
    const r=idx.get(normKey(c));
    if(r)return r;
  }
  return null;
}
function matchesFilter(e){
  if(currentFilter==='reference')return false;
  if(currentFilter==='scenarios')return false;
  if(currentFilter==='all')return true;
  if(currentFilter.startsWith('tag:'))return (e.tags||[]).includes(currentFilter.slice(4));
  if(currentFilter.startsWith('task:'))return (e.task_groups||[]).includes(currentFilter.slice(5));
  return e.category===currentFilter;
}
function matchesSearch(e,q){
  if(!q)return true;
  const ref=findReference(e);
  const hay=[e.name,e.original,e.description,e.simple,e.use_case,e.avoid_case,e.recommended_prompt,ref?.n,ref?.brief,ref?.zh,ref?.en,...(e.keywords||[]),...(e.tags||[]),...(e.task_groups||[])].join(' ').toLowerCase();
  return hay.includes(q);
}
function matchesReferenceSearch(r,q){
  if(!q)return true;
  return [r.t,r.cat,r.n,r.brief,r.zh,r.en].join(' ').toLowerCase().includes(q);
}
function matchesScenarioSearch(s,q){
  if(!q)return true;
  return [s.kind,s.title,s.problem,s.prompt,s.output,...s.steps].join(' ').toLowerCase().includes(q);
}
function renderScenarios(q=''){
  const byOriginal=new Map(entries.map(e=>[String(e.original).toLowerCase(),e]));
  const list=SCENARIOS.filter(s=>matchesScenarioSearch(s,q));
  const cards=list.map(s=>{
    const stepHtml=s.steps.map(step=>`<span class="step-pill">${escapeHtml(byOriginal.get(step.toLowerCase())?.name||step)}</span>`).join('');
    const related=s.steps.find(step=>byOriginal.has(step.toLowerCase()));
    return `<div class="scenario-card">
      <div class="scenario-top"><div class="scenario-title">${escapeHtml(s.title)}</div><span class="scenario-kind">${escapeHtml(s.kind)}</span></div>
      <div class="scenario-problem">${escapeHtml(s.problem)}</div>
      <div class="scenario-row"><strong>推荐组合：</strong><div class="workflow-steps">${stepHtml}</div></div>
      <div class="scenario-row"><strong>预期产出：</strong>${escapeHtml(s.output)}</div>
      <div class="scenario-prompt">${escapeHtml(s.prompt)}</div>
      <div class="scenario-actions">
        <button class="mini-btn" onclick="copyCommand(this.closest('.scenario-card').querySelector('.scenario-prompt').textContent)">复制示范提问</button>
        ${related?`<button class="mini-btn" onclick="document.getElementById('search').value='${escapeHtml(related)}';setFilter('all',document.querySelector('[data-filter=all]'))">查看相关命令</button>`:''}
      </div>
    </div>`;
  }).join('');
  return `<section class="panel"><h2>按应用场景选 Skill</h2><div class="scenario-grid">${cards}</div></section>`;
}
function renderReferenceLibrary(q=''){
  const list=references.filter(r=>matchesReferenceSearch(r,q));
  const shown=q?list:list.slice(0,24);
  const cards=shown.map(r=>`<div class="ref-item">
    <div class="ref-meta"><span class="ref-kind">${r.t==='cmd'?'命令':r.t==='skill'?'技能':'智能体'}</span><span class="ref-kind">${escapeHtml(r.cat)}</span></div>
    <div class="ref-name">${escapeHtml(r.n)}</div>
    <div class="ref-brief">${escapeHtml(r.brief)}</div>
    <details class="reference-box"><summary>查看原网页说明</summary><div class="reference-detail">${r.zh||''}${r.en?`<div class="reference-en">${escapeHtml(r.en)}</div>`:''}</div></details>
  </div>`).join('');
  const more=!q&&list.length>shown.length?`<div class="empty">原网页参考库共 ${list.length} 条，当前展示前 ${shown.length} 条。搜索关键词或点击“原参考”可查看全部。</div>`:'';
  return `<section class="panel"><h2>原网页参考库</h2><div class="ref-library">${cards}</div>${more}</section>`;
}
function renderHome(){
  const taskHtml=TASKS.map(t=>`<div class="task-card" onclick="setTaskFilter('${t.name}')"><div class="task-title">${t.name}</div><div class="task-desc">${t.desc}</div></div>`).join('');
  const byOriginal=new Map(entries.map(e=>[String(e.original).toLowerCase(),e]));
  const workflowHtml=WORKFLOWS.map(w=>{
    const steps=w.steps.map(s=>`<span class="step-pill">${escapeHtml(byOriginal.get(s.toLowerCase())?.name||s)}</span>`).join('');
    return `<div class="workflow"><div class="workflow-name">${w.name}</div><div class="workflow-steps">${steps}</div></div>`;
  }).join('');
  return `${renderScenarios()}<section class="panel"><h2>按任务找 Skill</h2><div class="task-grid">${taskHtml}</div></section><section class="panel"><h2>推荐工作流</h2><div class="workflow-grid">${workflowHtml}</div></section><section class="panel"><h2>原网页参考库</h2><div class="empty">旧版网页的详细说明已整合进命令卡片，也可以点击上方“原参考库”单独浏览。</div></section>`;
}
function render(){
  const q=document.getElementById('search').value.toLowerCase();
  if(currentFilter==='scenarios'){
    document.getElementById('app').innerHTML=renderScenarios(q);
    return;
  }
  if(currentFilter==='reference'){
    document.getElementById('app').innerHTML=renderReferenceLibrary(q);
    return;
  }
  let filtered=entries.filter(e=>matchesFilter(e)&&matchesSearch(e,q));
  const app=document.getElementById('app');
  if(!entries.length){app.innerHTML='<div class="empty">正在加载数据...</div>';return}
  if(!filtered.length){app.innerHTML=(q?renderReferenceLibrary(q):renderHome())+'<div class="empty">没有找到匹配的命令卡片，已继续搜索原网页参考库</div>';return}
  const counts={};
  entries.forEach(e=>{counts[e.category]=(counts[e.category]||0)+1});
  let html='<div class="stats">';
  html+=`<div class="stat"><div class="stat-num">${entries.length}</div><div class="stat-label">总计</div></div>`;
  for(const[k,v]of Object.entries(counts))html+=`<div class="stat"><div class="stat-num">${v}</div><div class="stat-label">${k}</div></div>`;
  html+=`<div class="stat"><div class="stat-num">${references.length}</div><div class="stat-label">原参考</div></div>`;
  html+='</div>';
  if(currentFilter==='all'&&!q)html+=renderHome();
  let curCat='',curSub='';
  filtered.forEach(e=>{
    if(e.category!==curCat){curCat=e.category;curSub='';const n=filtered.filter(x=>x.category===curCat).length;html+=`<div class="cat-header">${curCat} <span class="badge">${n}</span></div>`}
    if(e.sub!==curSub){curSub=e.sub;html+=`<div class="sub-header">${curSub}</div>`}
    const prompt=escapeHtml(e.recommended_prompt||e.slash_command);
    const tags=(e.tags||[]).slice(0,4).map(t=>`<span class="tag">${escapeHtml(t)}</span>`).join('');
    const ref=findReference(e);
    const refHtml=ref?`<details class="reference-box"><summary>原网页详细说明：${escapeHtml(ref.brief)}</summary><div class="reference-detail">${ref.zh||''}${ref.en?`<div class="reference-en">${escapeHtml(ref.en)}</div>`:''}</div></details>`:'';
    html+=`<div class="card">
      <div class="card-head"><div><div class="card-name">${escapeHtml(e.name)}</div>${e.original?`<div class="card-original">${escapeHtml(e.original)}</div>`:''}</div><div class="tags">${tags}</div></div>
      <div class="card-simple">${escapeHtml(e.simple)}</div>
      <div class="card-desc">${escapeHtml(e.description)}</div>
      <div class="guide"><strong>什么时候用：</strong>${escapeHtml(e.use_case)}</div>
      <div class="guide"><strong>不适合：</strong>${escapeHtml(e.avoid_case)}</div>
      <div class="card-cmd"><code>${prompt}</code><button class="copy-btn" onclick="copyCommand(this.previousElementSibling.textContent)">复制推荐用法</button></div>
      ${refHtml}
    </div>`;
  });
  if(q)html+=renderReferenceLibrary(q);
  app.innerHTML=html;
}
loadData().catch(e=>{document.getElementById('app').innerHTML='<div class="empty">数据加载失败，请通过本地静态服务器或 GitHub Pages 打开页面。</div>';showToast(e.message,'info')});
</script>
</body>
</html>"""

with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8-sig") as f:
    reference_entries = []
    if REFERENCE_DATA_FILE.exists():
        with open(REFERENCE_DATA_FILE, "r", encoding="utf-8") as ref_file:
            reference_entries = json.load(ref_file)
    html_output = (
        HTML_TEMPLATE
        .replace("__EMBEDDED_ENTRIES__", json.dumps(all_entries, ensure_ascii=False))
        .replace("__EMBEDDED_META__", json.dumps(meta, ensure_ascii=False))
        .replace("__EMBEDDED_REFERENCES__", json.dumps(reference_entries, ensure_ascii=False))
    )
    f.write(html_output)
print(f"静态网页生成完成 -> {OUTPUT_DIR / 'index.html'}")
