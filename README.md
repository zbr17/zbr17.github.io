# Borui Zhang · 个人科研主页

英文个人主页，采用近白背景与蓝色强调的科技风。使用 Python + YAML + Jinja2 生成纯静态网页，并从同一份内容生成完整英文学术 CV。CV 延续原版的衬线正文、深红编号和浅绿标题线。提交到 GitHub 后自动构建与发布到 GitHub Pages。

## 快速使用

建议 Python 3.10 或更新版本：

```bash
python -m pip install -r requirements.txt
python scripts/build.py
python -m http.server 8000
```

打开 http://localhost:8000 。构建会更新根目录的 `index.html` 与 `assets/resume/BoruiZhang_CV.pdf`。这些是生成文件，请维护配置和模板，不直接编辑生成后的 HTML 或 PDF。

生成精简发布包：

```bash
python scripts/build.py --output-dir dist
python -m http.server 8000 --directory dist
```

发布包只包含入口网页、样式、脚本、引用的图片、新版英文 CV 和 `.nojekyll`。源码和团队介绍均不打包，CV 照片直接嵌入 PDF。输出目录必须位于项目内，不能覆盖源码目录；已有非构建目录不会被清空。由此脚本生成的发布目录在重建时会被替换，以避免遗留素材继续发布。

## 日常更新

- `content/site.yaml`：个人信息、统一社交链接、简介、研究方向、新闻、任职、教育、公司、荣誉、教学和学术服务。
- `content/papers/`：每篇论文一份 YAML；网页与 CV 共用这些记录。
- `src/templates/`：页面骨架和复用组件；`assets/css/style.css` 与 `assets/js/main.js` 管理视觉和交互。
- `scripts/build.py`：内容检查、网页渲染与发布打包；`scripts/build_cv.py`：英文学术 CV 排版。
- `tests/`：验证论文一致性、静态导航、文件隔离和新增论文流程。

提交内容配置和素材即可，Actions 会重新生成网页与 CV；无需手动提交每次生成结果。根目录的生成文件仍保留，方便直接预览或兼容传统静态部署。

### 新增论文

创建 `content/papers/年份_简称.yaml`：

```yaml
title: "Paper Title"
authors:
  - name: "Borui Zhang"
    highlight: true
    equal_contrib: true
  - name: "Coauthor Name"
venue: "CVPR"
year: 2026
type: "publication"
image: "assets/images/publications/example.png"
links:
  - name: "Paper"
    url: "https://example.com/paper"
  - name: "Code"
    url: "https://github.com/example/project"
abstract: >
  A short, public description of this work.
```

把图片放到对应路径即可。默认 `selected: true`，会显示在主页；`type: preprint` 则显示在预印本区。

仅用于完整 CV 的条目设置 `selected: false`，可省略 `image` 和 `abstract`。所有条目都需要标题、作者、会议/期刊、整数年份及类型。重复标题、缺失图片、失效章节链接和错误字段会导致构建失败，并给出具体原因。

CV 自动区分常见期刊缩写；新增其他期刊时加 `kind: journal`。完整期刊名称可使用 `venue_full` 字段。预印本与正式版本通常合并到一个条目并更新发表信息；会议论文和独立期刊扩展可分别保留。

### 个人信息与简历

网页与 CV 共用任职、教育、研究方向、荣誉和服务信息。CV 另有 `basic_info.cv_summary` 简介及 `interests` 字段，其他内容无需维护第二遍。邮箱、Scholar、GitHub 等 URL 只在 `basic_info` 中维护；`profile_links` 按字段引用，可排序或增删。

新照片替换到 `assets/images/`，修改 `profile_image` 后构建即可；CV 使用 `cv_image` 指定的正式照片。CV 由脚本生成，修改个人配置即可更新。页面显示日期采用北京时间；CI 使用提交日期，避免仅重跑部署就改变内容更新日期。`tmp/`、`dist/` 与 Python 缓存均为可重新生成的临时文件，验证后可直接删除。

## GitHub Pages 自动发布

首次在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。

随后：

1. 向 `main` 提交或合入内容更新。
2. **Actions → Build and deploy homepage** 自动检查、生成并发布网站。
3. 成功的部署会显示网站链接。构建失败时，现有线上版本保留；修复错误后重新提交即可。
4. Pull request 只运行检查与构建，不发布。也可手动运行工作流重新部署。
5. 回滚时撤销对应提交，再推送至 `main`，会重新部署上一个内容版本。

工作流仅部署 `dist/`。请勿把发布路径改为仓库根目录，也不要使用 `git add -f` 提交被忽略的团队介绍。`LoopEva-团队介绍-v1.pdf` 仅供本地参考，不提供公开下载。当前未配置自定义域名；如后续添加域名，需要同步设置 Pages 和发布包中的 CNAME。

## 检查

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

浏览器检查建议覆盖 1440、768、390 和 320 像素宽度，以及键盘导航、减少动态效果、关闭 JavaScript。导航和所有正文由构建时生成；JavaScript 只增强当前章节提示与轻微渐入。

## 设计参考

原创浅色布局参考 [Brittany Chiang](https://brittanychiang.com/) 的信息层级、[Rauno Freiberg](https://rauno.me/) 的排版细节，以及 [LoopEva](http://www.loopeva.com/) 的机器人科技视觉。保留项目此前参考 [Jon Barron](https://jonbarron.info/) 的学术内容组织思路。CV 参考仓库旧版简历的视觉风格，保留完整作者顺序并自动处理多页排版。
