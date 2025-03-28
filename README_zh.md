# End of Life Checker (依赖生命周期检查工具)

[English](README.md) | 中文

一个命令行工具，通过与 [endoflife.date](https://endoflife.date/) 数据比对，检查项目中软件依赖的生命周期（EOL）状态。

> **特别说明**：本工具完全在 Amazon Q CLI 的协助下开发，展示了 AI 辅助开发的能力。

## 概述

End of Life Checker 帮助开发者识别项目中可能带来安全风险或兼容性问题的过时依赖。该工具扫描项目文件以检测依赖及其版本，然后与 EOL 数据进行比对，提供警报和建议。

## 系统要求

- Python 3.8 或更高版本
- 所需包（自动安装）：
  - requests>=2.25.0
  - toml>=0.10.2

## 功能特点

- 支持多种编程语言和框架：
  - Java (Maven, Gradle)
    - 完整的依赖树分析，包括传递性依赖
    - 父 POM 继承支持
    - 依赖管理解析
  - Node.js (npm, yarn)
  - Python (pip, poetry, pipenv)
- 命令行界面，易于集成到 CI/CD 流水线
- 详细的报告显示：
  - 接近 EOL 的依赖
  - 已达到 EOL 的依赖
  - 推荐的升级路径，带有破坏性变更警告 (⚠️)
  - 美观的基于表情符号的状态指示器 (🔴 🟠 🟢 ❓)
  - 执行时间和进度跟踪
  - 项目名称和完整路径信息
- 可配置的警告阈值（例如，在 EOL 前 90 天开始警告）
- 支持多种格式导出报告（JSON, CSV, HTML）
- 离线模式，使用缓存的 EOL 数据

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install eol-check
```

### 从源代码安装

对于最新的开发版本或想要为项目做贡献：

```bash
# 克隆仓库
git clone https://github.com/yourlin/eol-check.git
cd eol-check

# 以开发模式安装
pip install -e .
```

从源代码安装允许你修改代码并立即看到效果，无需重新安装。

## 使用方法

基本用法：

```bash
eol-check /path/to/project
```

带选项的用法：

```bash
eol-check /path/to/project --format json --output report.json --threshold 180
```

## 选项

- `--format`：输出格式（text, json, csv, html）。默认：text
- `--output`：将报告保存到文件而不是标准输出
- `--threshold`：EOL 前多少天开始警告。默认：90
- `--offline`：使用缓存的 EOL 数据而不是从 endoflife.date 获取
- `--update`：强制更新缓存的 EOL 数据
- `--cache-ttl`：缓存生存时间。默认：1d。格式：'1d'（1天），'12h'（12小时），'30m'（30分钟）
- `--verbose`：显示有关检查过程的详细信息，包括 API 可用性消息和调试输出
- `--ignore-file`：包含要忽略的依赖项的文件路径（每行一个依赖项名称）
- `--max-workers`：API 请求的最大并行工作线程数（默认：CPU 核心数 * 2）

### 忽略文件格式

忽略文件应该每行包含一个依赖项名称。可以使用 `#` 字符添加注释。

示例 `ignore.txt`：
```
# 这些是内部依赖，不需要 EOL 检查
internal-lib
legacy-component
# 这个有自定义支持合同
enterprise-framework
```

## 支持的项目类型

- Java: pom.xml, build.gradle
  - 需要安装 Maven/Gradle 以进行完整的依赖分析
  - 如果构建工具不可用，则回退到基本解析
- Node.js: package.json, package-lock.json, yarn.lock
  - 需要安装 npm/yarn 以进行完整的依赖分析
  - 如果构建工具不可用，则回退到基本解析
- Python: requirements.txt, Pipfile, pyproject.toml
  - 需要安装 pip/poetry/pipenv 以进行完整的依赖分析
  - 如果构建工具不可用，则回退到基本解析

## 高级功能

### 破坏性变更检测

该工具会自动检测推荐的升级是否涉及主要版本变更（例如，从 2.x 升级到 3.x），并用警告表情符号 (⚠️) 标记这些变更，以指示潜在的破坏性变更。

### 传递性依赖分析

对于 Java 项目，该工具分析完整的依赖树，包括：
- 项目中声明的直接依赖
- 由直接依赖引入的传递性依赖
- 由父 POM 管理的依赖
- 来自依赖管理部分的依赖

这确保你能获得关于应用程序实际使用的所有库的 EOL 状态警报，而不仅仅是你直接声明的库。

### CI/CD 集成

该工具设计为易于集成到 CI/CD 流水线中：
- 退出代码 0：未发现问题
- 退出代码 1：运行工具时出错
- 退出代码 2：发现严重问题（依赖已达到 EOL）

这允许你在检测到关键依赖项时使构建失败或触发警报。

GitHub Actions 集成示例：
```yaml
name: 检查依赖 EOL

on:
  schedule:
    - cron: '0 8 * * 1'  # 每周一上午 8:00 运行
  workflow_dispatch:  # 允许手动触发

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: 设置 Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: 安装 eol-check
        run: pip install eol-check
        
      - name: 检查依赖
        run: eol-check . --format json --output eol-report.json
        
      - name: 上传报告作为构建产物
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: eol-report
          path: eol-report.json
```

## 故障排除

### 常见问题

1. **API 速率限制**
   - 症状：性能缓慢或关于"请求过多"的错误
   - 解决方案：使用 `--max-workers` 选项减少并行请求数，或使用 `--offline` 模式和缓存数据

2. **缺失依赖**
   - 症状：工具没有检测到你期望的所有依赖
   - 解决方案：确保你使用了正确的构建工具（Maven、npm 等），并且它已正确安装。如果构建工具不可用，工具会回退到基本解析。

3. **未知 EOL 状态**
   - 症状：许多依赖显示为"UNKNOWN"状态
   - 解决方案：endoflife.date API 可能没有这些依赖的数据。考虑为 endoflife.date 项目做贡献。

### 详细模式

使用 `--verbose` 标志获取更详细的信息：
- API 请求详情和响应
- 缓存使用信息
- 依赖解析过程
- 详细的错误消息和堆栈跟踪

这在排除故障或想要了解工具如何处理项目时特别有用。

## 许可证

MIT
