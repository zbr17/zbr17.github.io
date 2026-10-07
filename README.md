# Borui Zhang 个人学术主页

这是一个静态个人学术主页项目。页面内容主要写在 YAML 文件中，通过 Jinja2 模板生成根目录的 `index.html`，部署时只需要把整个目录作为静态网站提供即可。

## 目录结构

```text
.
├── index.html              # 生成后的主页入口，部署服务器会访问这个文件
├── content/
│   ├── site.yaml           # 个人信息、简介、新闻、研究方向、荣誉、服务
│   └── papers/             # 每篇论文一个 YAML 文件
├── assets/
│   ├── css/style.css       # 页面样式
│   ├── images/             # 头像、图标、论文图片
│   └── resume/             # CV 和个人简历 PDF
├── src/templates/          # HTML 模板
├── scripts/build.py        # 生成主页的脚本
├── requirements.txt        # Python 依赖
└── CNAME                   # 自定义域名配置
```

## 安装依赖

建议使用 Python 3.10 或更新版本。

```bash
pip install -r requirements.txt
```

## 生成主页

每次修改 `content/`、`src/templates/` 或 `assets/css/style.css` 后，运行：

```bash
python scripts/build.py
```

脚本会重新生成根目录的 `index.html`。部署到 Ubuntu 服务器时，请确认服务器的静态站点根目录中包含这个 `index.html` 以及 `assets/` 目录。

## 修改个人主页内容

主要内容在 `content/site.yaml` 中维护。

- `basic_info`：姓名、邮箱、主页链接、CV 路径、头像路径等。
- `about_me`：个人简介，支持少量 HTML 链接。
- `research_intro`：研究方向总述。
- `research_areas`：研究方向列表，每个方向包含 `title` 和 `details`。
- `news`：新闻列表，新增时把最新消息放在列表前面。
- `honors`：荣誉奖励列表。
- `services`：学术服务，包括会议审稿和期刊审稿。

页面左侧导航会自动读取模板中带有 `id` 的主要版块标题生成；通常只需要维护页面内容，不需要手动维护导航链接。

示例：

```yaml
news:
  - date: "2026-03"
    content: "1 paper accepted to <strong>Conference Name 2026</strong>."
```

## 新增论文

在 `content/papers/` 下新建一个 YAML 文件，推荐命名为：

```text
年份_论文简称.yaml
```

例如：

```text
2026_example.yaml
```

论文条目格式如下：

```yaml
title: "Paper Title"
authors:
  - name: "Borui Zhang"
    highlight: true
    equal_contrib: true
  - name: "Coauthor Name"
    url: "https://example.com/"
    equal_contrib: true
venue: "CVPR"
year: 2026
type: "publication"
image: "assets/images/publications/example.png"
links:
  - name: "Paper"
    url: "https://arxiv.org/"
  - name: "Code"
    url: "https://github.com/"
abstract: >
  A short description of this paper.
```

字段说明：

- `type: "publication"` 会显示在 `Selected Publications`。
- `type: "preprint"` 会显示在 `Preprints`。
- `highlight: true` 用于加粗自己的姓名。
- `equal_contrib: true` 会在作者名后显示 `*`。
- `image` 路径应放在 `assets/images/publications/` 下。
- `abstract` 支持少量 HTML，例如 `<span class="highlight">Method Name</span>`。

新增论文图片后，请把图片文件也放入 `assets/images/publications/`，再运行 `python scripts/build.py`。

## 替换头像和 CV

- 头像文件放在 `assets/images/`，然后修改 `content/site.yaml` 中的 `basic_info.profile_image`。
- CV 或简历 PDF 放在 `assets/resume/`，然后修改 `content/site.yaml` 中的 `basic_info.cv_link`。

路径需要从项目根目录开始写，例如：

```yaml
profile_image: "assets/images/BoruiZhang_small.png"
cv_link: "assets/resume/BoruiZhang_CV.pdf"
```

## 部署提示

这是纯静态网站，不需要后端服务。常见部署方式：

- 直接把项目目录放到 Nginx 的静态站点目录。
- 或只上传 `index.html`、`assets/`、`CNAME` 等静态部署所需文件。

修改 YAML 内容后一定要重新运行生成脚本，否则 `index.html` 不会自动更新。
