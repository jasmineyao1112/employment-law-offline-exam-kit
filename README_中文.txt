离线考试资料速查工具（macOS）
============================

它是什么
--------
这不是本地 AI，也不会在考试时连接 ChatGPT。它会在考前把 PDF / Markdown
资料做成一个可以双击打开的离线检索页面：输入关键词后，直接跳到相关讲义页，
并可查看原始页面截图、收藏卡片、添加个人笔记。

首次部署（请在有网络时完成）
----------------------------
1. 从 GitHub 下载整个仓库 ZIP，解压后把整个文件夹放到 Mac 上一个固定位置，例如“文稿/Offline Exam Kit”。
2. 第一次双击“02_打开离线速查.command”时，工具会自动恢复完整的图片和课程资料；请耐心等待约一分钟。
2. 把课程 PDF 或 Markdown 文件复制进 materials 文件夹。
3. 双击“01_构建考试资料库.command”。
   - 第一次运行会在本文件夹中创建 .venv，并安装 PyMuPDF。
   - macOS 如提示无法打开：右键该文件 → 打开 → 再确认。
4. 构建成功后会自动打开 index.html。
5. 双击“03_考前自检.command”，确认 cards、assets、missing images 和
   external HTML references 均正常。

考试当天
--------
1. 不需要 Python，不需要网络，也不需要启动服务器。
2. 双击“02_打开离线速查.command”，或直接双击 index.html。
3. 必须保留整个文件夹，不要只移动 index.html；data.js 和 assets/ 是必需的。
4. 常用操作：
   - Cmd/Ctrl + K：定位搜索框
   - 多个词：默认同时匹配；若无结果会自动显示部分匹配
   - "exact phrase"：精确短语
   - -word：排除某个词
   - ↑ / ↓：移动结果；Enter：打开首个结果
   - 左侧可浏览来源、数字/期限、法条、案例、缩写、收藏和笔记

更新资料
--------
把新资料放进 materials，再运行“01_构建考试资料库.command”。旧的 data.js
和 assets/ 会被重建；浏览器中的收藏/笔记保存在浏览器本地。重建前建议在页面
左侧选择“Export stars & notes”备份。

中文注释与例题（可选）
----------------------
编辑 annotations.py 后重新构建。文件内保留了填写格式，但默认没有预填内容，
避免把未经核对的规则或答案带进考试资料。

资料格式
--------
- 支持：带文字层的 PDF、.md、.markdown。
- 扫描版 PDF：如果构建时提示 blank/unreadable pages，需要先做 OCR。
- Word / PowerPoint：建议先导出为 PDF，以保留页面和版式。

重要限制
--------
- 只有当考试规则允许访问本机文件和浏览器时，才可以在考试中使用。
- Examplify 的 Secure assessment 会阻止访问硬盘资料和其他程序；本工具无法、
  也不应绕过该限制。
- Non-Secure 或 Non-Secure + Block Internet 是否允许使用本工具，仍以老师、
  院系及当场考试说明为准。请务必用正式考试相同设置的 mock exam 实测。

文件说明
--------
index.html                    离线检索界面
data.js                       构建生成的索引数据
assets/                       构建生成的讲义页面图片
materials/                    课程资料放置处
build_index.py                索引构建脚本
annotations.py                可选中文注释与例题
01_构建考试资料库.command     首次部署与重建
02_打开离线速查.command       考试当天打开
03_考前自检.command           完整性检查
