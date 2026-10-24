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

旧站最初导入 35 篇文章。2026-10-20 按正文 HTML（含代码与图片属性）完全一致的证据，清理了 2023 年及以前的 11 份重复副本，保留 23 篇技术文章和 1 篇《摘录与感悟》。分组及保留路径记录在 `data/legacy-deduplication.json`。同标题但正文不同的文章仍保留；未依据文件名猜测和重写正文。Blog、旧归档、标签与分页入口同步清理，上一篇/下一篇跳过已删除副本；删除可通过 Git 历史恢复。分类可修改 `kind`。

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

## Agent 与大模型学习问题整理

`/post/agent-llm-learning-notes.html` 是问题目录，13 个主题分别放在 `/post/learning-*.html`，Blog 中各自列出。每篇以原问题为小节标题，保留知识标签和问题来源。

- `data/original-questions.json` 保留收集的 79 个原始问题位置、原文和来源映射。相近问法可以共用一个知识条目，但原文仍分别显示。残缺句子保留原样，并显示编者注。
- `data/interviews.json` 保留 89 个知识问题的知识标签和来源索引。其中 59 个对应上述原始问题，另 30 个是外部资料的概念整理，页面单独标为延伸问题，不宣称逐字摘录。旧 `answer` 和 `answerSources` 已清空，不能作为答案的维护入口。
- `data/learning-series.json` 仅维护文章标题、地址 slug 和问题分组。
- `data/question-answers.json` 的 `questions` 数组包含 `id`、`answerMarkdown`、`learningNotesMarkdown`、`sources`。答案和学习记录目前为空，留给本站作者学习后填写；`sources` 是自行填写内容所引用的资料，不是问题原文来源。
- 按 `id` 找到对应条目后，在 `answerMarkdown` 中写自己的理解，在 `learningNotesMarkdown` 中记录学习过程。两者可独立填写；两者都为空字符串或纯空白时，每组问题下面仅保留一处无标题、无底色的正文留白，以浅灰分隔线与问题区分，不生成答案、提示语或占位文字。填写后，两项内容按答案、学习过程的顺序自然接排，不额外添加标题或空区域。这是文章排版，不是网页输入框；填写仍在数据文件中进行。参考资料按需填入 `sources`，每项包含 `title` 和 HTTPS `url`。
- `scripts/markdown_subset.py` 是标准库实现的有限 Markdown 渲染器，支持段落、标题、列表、表格、代码围栏、行内代码、加粗及 HTTPS 链接；不执行原始 HTML，不加载外部脚本。数学公式请使用 Unicode 或代码块，不使用 LaTeX。
- `scripts/build_learning_series.py` 校验问题覆盖、重复 ID、Markdown 字段类型和不安全链接，生成文章和两个入口地址。`scripts/build_interviews.py` 是兼容命令。
- `assets/learning-series.css` 只影响这一组文章，不改变旧博客或 Notes。无搜索框、下拉框、题库交互或 JavaScript 依赖。
- 原始问题来源与以后填写的参考资料分开显示；不运行旧 Hexo 构建来覆盖静态站点。

修改后运行：

```bash
python3 scripts/build_learning_series.py
python3 scripts/build_indexes.py
python3 scripts/build_learning_series.py --check
python3 scripts/build_indexes.py --check
python3 -m unittest discover -s tests -v
```

浏览器检查覆盖问题目录、原问题锚点、来源链接和上一篇/下一篇。填写内容后，再检查窄屏段落、代码和表格的显示。
