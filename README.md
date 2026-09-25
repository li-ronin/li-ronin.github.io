# LKH 的个人网站

首页是简洁的个人介绍。技术文章和生活随笔分别从 Blog / Notes 进入，首页不展示文章流。

## 页面与文件

| 地址 / 文件 | 用途 |
| --- | --- |
| `/` → `index.html` | 个人介绍；直接修改姓名、介绍段落和链接 |
| `/blog/` | 技术文章目录，按年份排列 |
| `/notes/` | 生活随笔目录 |
| `/post/*.html` | 原有文章，正文和访问地址保留 |
| `/archives/`、`/tags/`、`/page/` | 原有归档、标签和分页，保留兼容 |
| `assets/academic.css` | 新首页与目录的共享样式，不覆盖旧文章样式 |
| `data/writing.json` | 写作目录数据：日期、标题、原地址、分类 |
| `scripts/build_indexes.py` | 用 Python 标准库生成 Blog / Notes 两个静态目录 |
| `js/main.js` | 旧主题初始化，以及跨新旧页面的导航兼容 |

当前导入旧站的 35 篇文章：34 篇技术文章、1 篇《摘录与感悟》。分类可修改 `kind`。旧归档里部分标题本来就重复；本次保留原标题，未依据文件名猜测和重写正文。

## 修改个人介绍

直接编辑 `index.html` 中的 `introduction-copy` 段落。简介按当前工作、技术方向和个人兴趣组织；修改后也请同步更新页面的 `description` 与 `og:description`。未填写不确定的邮箱、学历、雇主、论文或履历。

头像使用已上传的 `/images/profile.jpg`，不再使用羊驼图标作为主页照片。显示尺寸为桌面端 220 × 220px、手机端 144 × 144px，圆角为 12px，保持圆角方形而非圆形。样式位于 `assets/academic.css` 的 `.portrait` 规则及移动端覆盖规则中。`object-fit: cover` 会等比例裁剪而不拉伸原图；需要调整取景位置时可修改 `object-position`，无需重新上传图片。

首页正文使用 1.65 倍行距、10px 段落间距，相关规则限定在 `.home` 内，不改变 Blog / Notes 目录或旧文章的正文行距。

新页面不加载旧主题脚本，不添加统计服务，不依赖远程字体。它们在关闭 JavaScript 时仍可以阅读和导航。

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

## 新旧页面导航

旧主题使用 Swup 局部切换，新页面不使用它。`js/main.js` 为独立首页和目录添加完整页面跳转，保留 Ctrl / Command 点击和新标签页行为；旧文章页增加了主页、Blog、Notes、归档入口。旧首页分页的“第一页”链接改为 Blog 目录。文章、归档和标签页仍使用原主题。

## 测试与回退

结构测试验证目录生成一致性、分区、转义、URL 校验和可访问性基础。在完整仓库中还会校验文章目标文件是否存在；只下载改动文件的预览包会跳过这一项。浏览器视觉和跳转检查应使用上面的本地 HTTP 服务。

修改通过独立分支和 Pull Request 提供。需要回退时，撤销该 PR 的合并提交即可恢复旧首页；不要删除 `post/`、图片或旧资源目录。
