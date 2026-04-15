# CBETA CLI 注册到 CLI-Hub 官方仓库指南

## 注册信息

```json
{
  "name": "cbeta",
  "display_name": "CBETA",
  "version": "2.0.0",
  "description": "中华电子佛典协会 API CLI - 佛典搜索、典籍信息、全文获取、经目查询等全部功能",
  "requires": "click>=8.0, requests>=2.28",
  "homepage": "https://api.cbetaonline.cn",
  "install_cmd": "pip install cli-anything-cbeta",
  "entry_point": "cli-anything-cbeta",
  "category": "search",
  "source_url": null,
  "skill_md": null,
  "contributors": [
    {
      "name": "YOUR_GITHUB_USERNAME",
      "url": "https://github.com/YOUR_GITHUB_USERNAME"
    }
  ]
}
```

## 提交步骤

### 1. Fork CLI-Anything 仓库

访问 https://github.com/HKUDS/CLI-Anything 并点击 Fork

### 2. 克隆你的 Fork

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/CLI-Anything.git
cd CLI-Anything
```

### 3. 创建 CLI 目录结构

```bash
mkdir -p cli_anything/cbeta
mkdir -p cli_anything/cbeta/utils
mkdir -p cli_anything/cbeta/tests
mkdir -p cli_anything/cbeta/core
```

### 4. 复制代码文件

将以下文件复制到 CLI-Anything 仓库：

```
cli_anything/cbeta/
├── __init__.py              # 包入口
├── __main__.py              # python -m 入口
├── cbeta_cli.py             # CLI 主文件
├── pyproject.toml           # 包配置
├── README.md                # 文档
├── utils/
│   ├── __init__.py
│   └── cbeta_backend.py     # HTTP 客户端
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── pytest.ini
│   ├── test_backend.py      # 后端测试
│   └── test_cli.py          # CLI 测试
└── core/
│   └── __init__.py
```

### 5. 修改 registry.json

编辑 `registry.json`，在 `clis` 数组末尾添加注册信息：

```json
{
  "name": "cbeta",
  "display_name": "CBETA",
  "version": "2.0.0",
  "description": "中华电子佛典协会 API CLI - 佛典搜索、典籍信息、全文获取、经目查询等全部功能",
  "requires": "click>=8.0, requests>=2.28",
  "homepage": "https://api.cbetaonline.cn",
  "install_cmd": "pip install cli-anything-cbeta",
  "entry_point": "cli-anything-cbeta",
  "category": "search",
  "source_url": null,
  "skill_md": null,
  "contributors": [
    {
      "name": "YOUR_GITHUB_USERNAME",
      "url": "https://github.com/YOUR_GITHUB_USERNAME"
    }
  ]
}
```

### 6. 提交更改

```bash
git add .
git commit -m "Add CBETA CLI - Chinese Buddhist Electronic Text Association API tool"
git push origin main
```

### 7. 创建 Pull Request

- 访问你的 Fork 页面
- 点击 "Compare & pull request"
- 填写 PR 标题和描述：

```
标题: Add CBETA CLI - Chinese Buddhist Electronic Text Association API tool

描述:
## 概述
添加 CBETA（中华电子佛典协会）API 的完整 CLI 封装工具。

## 功能
- 28 个命令，100% API 覆盖率
- 搜索命令：全文搜索、KWIC、经目、相似文本、注释、标题、异体字、分面统计
- 佛典命令：信息、目录、全文、列表、字数统计、下载
- 工具命令：简繁转换、中文分词
- 导出命令：佛典列表、作译者、朝代信息
- JSON 输出和交互式 REPL

## 测试
- 64 个单元测试，100% 通过
- 使用 pytest + mock 测试框架

## 参考资料
- CBETA API: https://api.cbetaonline.cn
- CBETA API GitHub: https://github.com/DILA-edu/cbeta-api
```

### 8. 等待审核

PR 被审核并合并后，CBETA CLI 将自动出现在 CLI-Hub 仓库中，用户可以通过：

```bash
cli-hub install cbeta
```

安装使用。

---

## 替代方案：使用 GitHub Issues

如果不想提交 PR，可以通过 GitHub Issues 提交请求：

1. 访问 https://github.com/HKUDS/CLI-Anything/issues/new?template=contributor-signup.yml
2. 填写贡献者注册表单，附上 CLI 信息

---

*更新时间: 2026-04-15*