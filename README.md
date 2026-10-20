# 李可涵 Khan Li 的个人网站

首页是简洁的个人介绍。技术文章和生活随笔分别从 Blog / Notes 进入，首页不展示文章流。

## 页面与文件

| 地址 / 文件 | 用途 |
| --- | --- |
| `/` → `index.html` | 个人介绍；直接修改姓名、介绍段落和链接 |
| `/blog/` | 技术文章目录，按年份排列 |
| `/notes/` | 生活随笔目录 |
| `/post/*.html` | 原有文章，正文和访问地址保留 |
| `/archives/`、`/tags/`、`/page/` | 原有归档、标签和分页，保留兼容 |
| `assets/academic.css` | 首页、目录与文章页共用的基础样式 |
| `data/writing.json` | 写作目录数据：日期、标题、原地址、分类 |
| `scripts/build_indexes.py` | 用 Python 标准库生成 Blog / Notes 两个静态目录 |
| `css/style.css` | 旧页面的公共样式入口，仅引入学术风样式 |
| `assets/reading.css` | 正文、代码、目录、归档、标签和旧分页的阅读样式 |
| `js/main.js` | 学术风导航、原图片懒加载兼容、目录与代码复制 |

当前导入旧站的 35 篇文章：34 篇技术文章、1 篇《摘录与感悟》。分类可修改 `kind`。旧归档里部分标题本来就重复；本次保留原标题，未依据文件名猜测和重写正文。

## 修改个人介绍

直接编辑 `index.html` 中的 `introduction-copy` 段落。简介按当前工作、技术方向和个人兴趣组织；修改后也请同步更新页面的 `description` 与 `og:description`。未填写不确定的邮箱、学历、雇主、论文或履历。

头像使用已上传的 `/images/profile.jpg`，不再使用羊驼图标作为主页照片。显示尺寸为桌面端 220 × 220px、手机端 144 × 144px，圆角为 12px，保持圆角方形而非圆形。样式位于 `assets/academic.css` 的 `.portrait` 规则及移动端覆盖规则中。`object-fit: cover` 会等比例裁剪而不拉伸原图；需要调整取景位置时可修改 `object-position`，无需重新上传图片。

首页正文使用 1.65 倍行距、10px 段落间距，照片及布局保持不变。姓名显示为「李可涵 Khan Li」；首页元数据、写作目录及文章页导航同步使用全名。文章正文同样使用 1.65 倍行距，代码使用独立的等宽字体与行高。

首页和 Blog / Notes 目录不加载旧主题脚本，不添加统计服务，不依赖远程字体；关闭 JavaScript 时仍可以阅读和导航。旧文章的兼容方式见下文。

## 本地预览

在仓库根目录运行（建议 Python 3.9 或更新版本）：

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

浏览器打开 `http://localhost:8000/`。不要直接双击 HTML；页面使用站点根目录路径，需要通过 HTTP 服务预览。

## 更新文章目录

先准备或生成实际文章 HTML，并放在 `post/` 中，然后在 `data/writing.json` 增加记录：

```json
{
  "date": "2026-09-24",
  "title": "文章标题",
  "url": "/post/my-article.html",
  "kind": "blog"
}
```

技术文章的 `kind` 是 `blog`，公开日记/随笔是 `note`。之后运行：

```bash
python3 scripts/build_indexes.py
python3 scripts/build_indexes.py --check
python3 -m unittest discover -s tests -v
```

生成器只更新 `blog/index.html` 和 `notes/index.html`，不会改写首页或文章正文。它不负责把 Markdown 转成文章页面，也不是 Hexo 源码工程的替代品。

## 关于原来的 Hexo 工程

本仓库原来提交的是 Hexo / Redefine 生成的静态产物，不包含完整写作工程。此次改造直接在静态站点上完成，不要求找回旧工程，也不新增 npm 构建依赖。

如果以后恢复原 Hexo 工程并直接重新部署，生成器可能覆盖新首页及这些维护文件。请先备份、在源工程中整合独立首页和目录，或在生成之后恢复这些文件；不要未经检查就将整个输出目录覆盖到仓库。

## 文章页与导航

文章的 `/post/*.html` 路径和原 HTML 内容不变。所有旧页面原本就引用 `css/style.css`；该入口现在只引入 `assets/academic.css` 与 `assets/reading.css`，不再引入 Redefine 样式。因此改动共享文件即可统一全部文章，也会统一原归档、标签和分页的基本排版。

正文采用白底、800px 最大宽度、蓝色链接、1.65 倍行距；移除视觉上的封面横幅、头像侧栏、浮动工具和访问计数。原有标题、日期、标签、许可证、上下篇链接、正文图片和代码保留。代码块可横向滚动，保留原有高亮和行号，并提供复制按钮；无剪贴板权限时改为选中代码，需手动复制。

`js/main.js` 关闭旧 Swup 导航和不再使用的主题初始化，以原生页面跳转连接 Home / Blog / Notes / 归档。它将旧图片的 `data-src` 提升为真实 `src`，否则只移除旧懒加载脚本会让图片停留在占位图；多节文章增加可折叠目录。新增文章分类从 `data/writing.json` 读取；读取失败也不阻止正文显示。

本次采用兼容样式层，不重写 35 篇已有 HTML，也没有清除其中历史遗留的第三方脚本引用；不新增第三方依赖或统计服务。第三方图床与外部嵌入的可用性仍取决于原服务。禁用 JavaScript 时正文和原链接仍可阅读，但旧格式图片加载兼容、生成目录和复制按钮需要 JavaScript。

未来恢复 Hexo 写作工程时，应把这套共享样式与导航整合进源工程，或在生成后恢复这些公共文件；不要直接用旧主题生成物覆盖它们。

## 测试与回退

请在完整仓库中运行测试，以检查文章目标文件、公共样式入口、全名、目录生成一致性、分区、转义与 URL 校验。浏览器视觉和完整跳转检查应使用上面的本地 HTTP 服务。

修改通过独立分支和 Pull Request 提供。需要回退时，撤销该 PR 的合并提交即可恢复旧首页；不要删除 `post/`、图片或旧资源目录。

## 面试学习题库

`/post/ai-interview-learning-archive.html` 是面向 Agent 开发、大模型算法与工程基础的学习题库。保留现有 Blog 入口，不修改旧文章或使用 Hexo 重生成。

- `data/interviews.json`：唯一内容源，含规范化问题、具体知识标签、难度、岗位方向、建议学习范围、原面经招聘类别、来源和题目覆盖映射。
- `scripts/build_interviews.py`：标准库静态生成器；`--check` 检查产物是否过期。
- `assets/interviews.css` / `assets/interviews.js`：独立样式与渐进增强筛选。JavaScript 关闭时所有题目、来源与学习线索仍在 HTML 中。
- 标签只用于具体知识，不用于难度、校招 / 社招或岗位；这些分别保存在独立字段。`audience` 表示建议学习范围，不证明原面经招聘类别；`sourceAudience` 仅按已核实来源填写。
- 保留稳定题目 ID，作为 `#题目ID` 永久链接。合并重复题时保留 `sourceRefs` 和 `coverage`，不要删除独立追问。
- 来源状态需区分：用户提供文本、已读取公开正文、资源导航、无法读取。没有正文证据的链接不得补造题目。第三方内容应归纳改写并署名链接，不全文转载。
- `knowledge`、`extensions` 是编排的学习线索，不是标准答案或原面经引文。厂商实现细节需要固定版本和官方来源后另行补充。

修改题库后执行：

```bash
python3 scripts/build_interviews.py
python3 scripts/build_indexes.py
python3 scripts/build_interviews.py --check
python3 scripts/build_indexes.py --check
python3 -m unittest discover -s tests -v
node --check assets/interviews.js
node tests/test_interviews_js.cjs
```

本地 HTTP 预览方式同上。筛选条件保存在 URL 查询参数中；题目锚点可直接定位并展开学习线索。静态页面无需后端、外部脚本、远程字体或额外 npm 依赖。
