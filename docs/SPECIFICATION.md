# End of Life Checker - 产品研发规格说明书

## 1. 产品概述

End of Life Checker 是一个命令行工具，用于检查项目中软件依赖的生命周期状态。该工具通过比对本地项目依赖与 [endoflife.date](https://endoflife.date/) 网站提供的数据，帮助开发者识别已过期或即将过期的依赖，从而降低安全风险和兼容性问题。

## 2. 目标用户

- 软件开发者
- DevOps 工程师
- 安全团队
- 项目管理人员

## 3. 功能需求

### 3.1 核心功能

1. **依赖检测**
   - 扫描项目文件以识别依赖及其版本
   - 支持多种编程语言和包管理系统
   
2. **EOL 数据获取**
   - 从 endoflife.date API 获取最新的生命周期数据
   - 支持本地缓存数据，减少网络请求
   
3. **生命周期分析**
   - 比对依赖版本与 EOL 数据
   - 计算距离生命周期结束的时间
   
4. **报告生成**
   - 生成详细的分析报告
   - 支持多种输出格式

### 3.2 支持的项目类型

1. **Java**
   - Maven (pom.xml)
   - Gradle (build.gradle)
   
2. **Node.js**
   - npm (package.json, package-lock.json)
   - Yarn (yarn.lock)
   
3. **Python**
   - pip (requirements.txt)
   - Poetry (pyproject.toml)
   - Pipenv (Pipfile)

### 3.3 命令行选项

- `--format`: 输出格式 (text, json, csv, html)，默认为 text
- `--output`: 将报告保存到文件而非标准输出
- `--threshold`: 开始警告的天数阈值，默认为 90 天
- `--offline`: 使用缓存的 EOL 数据而非在线获取
- `--update`: 强制更新缓存的 EOL 数据
- `--verbose`: 显示检查过程的详细信息
- `--ignore-file`: 包含要忽略的依赖的文件路径

## 4. 技术规格

### 4.1 系统架构

1. **模块化设计**
   - 核心引擎：负责协调各组件
   - 解析器模块：负责解析不同类型的项目文件
   - API 客户端：与 endoflife.date API 交互
   - 报告生成器：生成不同格式的报告

2. **数据流**
   - 输入：项目路径和命令行选项
   - 处理：解析项目文件 → 获取 EOL 数据 → 分析生命周期 → 生成报告
   - 输出：依赖生命周期状态报告

### 4.2 技术栈

- **编程语言**: Python 3.8+
- **依赖管理**: pip, setuptools
- **HTTP 客户端**: requests
- **数据解析**: json, xml, yaml
- **命令行界面**: argparse, click
- **测试框架**: pytest

### 4.3 API 集成

End of Life Checker 将使用 endoflife.date 提供的 API 获取软件生命周期数据。API 端点格式为：

- `https://endoflife.date/api/{product}.json` - 获取产品所有版本的 EOL 信息
- `https://endoflife.date/api/{product}/{version}.json` - 获取特定版本的 EOL 信息

### 4.4 数据缓存

- 缓存位置: `~/.cache/end-of-life-checker/`
- 缓存格式: JSON 文件
- 默认缓存有效期: 7 天

## 5. 用户体验

### 5.1 命令行界面

```
eol-check [OPTIONS] PROJECT_PATH
```

### 5.2 输出示例

#### 文本输出 (默认)

```
End of Life Checker Report
=========================
Project: /path/to/project
Scan Date: 2025-03-27

CRITICAL: 2 dependencies have reached end of life
WARNING: 3 dependencies will reach end of life within 90 days

Details:
--------
[CRITICAL] react 16.8.0 - EOL since 2022-06-14 (280 days ago)
  → Recommended upgrade: react 18.2.0

[CRITICAL] django 2.2.0 - EOL since 2022-04-01 (360 days ago)
  → Recommended upgrade: django 4.2.0

[WARNING] node 14.17.0 - EOL in 45 days (2023-05-12)
  → Recommended upgrade: node 18.15.0

...
```

#### JSON 输出

```json
{
  "project": "/path/to/project",
  "scan_date": "2025-03-27T12:34:56",
  "summary": {
    "critical": 2,
    "warning": 3,
    "ok": 15
  },
  "dependencies": [
    {
      "name": "react",
      "version": "16.8.0",
      "status": "CRITICAL",
      "eol_date": "2022-06-14",
      "days_remaining": -280,
      "recommended_version": "18.2.0"
    },
    ...
  ]
}
```

## 6. 开发计划

### 6.1 项目结构

```
end_of_life_checker/
├── __init__.py
├── __main__.py
├── cli.py
├── core.py
├── api/
│   ├── __init__.py
│   └── endoflife_client.py
├── parsers/
│   ├── __init__.py
│   ├── java.py
│   ├── nodejs.py
│   └── python.py
├── reporters/
│   ├── __init__.py
│   ├── text.py
│   ├── json_reporter.py
│   ├── csv_reporter.py
│   └── html_reporter.py
└── utils/
    ├── __init__.py
    ├── cache.py
    └── version.py
```

### 6.2 开发阶段

1. **阶段一：核心功能**
   - 实现基本的命令行界面
   - 开发 endoflife.date API 客户端
   - 实现缓存机制
   - 开发基本的文本报告生成器

2. **阶段二：解析器**
   - 实现 Python 项目解析器
   - 实现 Node.js 项目解析器
   - 实现 Java 项目解析器

3. **阶段三：报告生成**
   - 实现 JSON 报告生成器
   - 实现 CSV 报告生成器
   - 实现 HTML 报告生成器

4. **阶段四：优化与测试**
   - 编写单元测试和集成测试
   - 性能优化
   - 用户体验改进

## 7. 测试计划

1. **单元测试**
   - 测试各个模块的功能
   - 测试边缘情况和错误处理

2. **集成测试**
   - 测试完整的工作流程
   - 测试与 endoflife.date API 的集成

3. **用户测试**
   - 在不同类型的项目上测试工具
   - 收集用户反馈并改进

## 8. 部署与分发

- 通过 PyPI 分发
- 提供详细的安装和使用文档
- 提供 Docker 镜像以便在 CI/CD 环境中使用

## 9. 维护计划

- 定期更新以支持新的项目类型和包管理系统
- 监控 endoflife.date API 的变化并相应调整
- 根据用户反馈添加新功能和改进现有功能
