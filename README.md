# 腾讯元宝对话批量导出工具

一个基于 Playwright 的 Python 脚本，用于批量导出腾讯元宝（Tencent Yuanbao）中的对话记录。

## ✨ 功能特性

- **两种导出模式**：
  - **模式 A**：导出侧边栏 Chat 列表中所有未归入分组的对话
  - **模式 B**：导出指定分组内的全部对话（需手动选中分组）
- **智能滚动**：自动处理虚拟列表滚动，确保加载完整对话列表
- **全量抓取**：每个对话内部向上回溯，抓取所有历史消息
- **思考过程保留**：自动识别并保留元宝的思考过程（如显示）
- **持久化登录**：使用浏览器持久化会话，首次登录后无需重复登录
- **输出格式**：Markdown 格式，便于阅读和存档

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

还需要安装 Playwright 浏览器内核：

```bash
playwright install chromium
```

## 🚀 使用方法

### 模式 A：导出未分组对话

```bash
python scripts/export_ungrouped.py
```

流程：
1. 脚本会自动打开浏览器并访问元宝页面
2. **请确保已登录**，侧边栏能看到 Chat 和 Group 列表
3. 按提示按 Enter 开始全量深度备份
4. 脚本会展开所有会话分组，滚动侧边栏加载完整列表
5. 自动逐一进入每个对话，抓取所有消息
6. 输出文件：`yuanbao_full_content.md`

### 模式 B：导出指定分组对话

```bash
# 默认重试次数（10次）
python scripts/export_group.py

# 自定义重试次数（推荐）
python scripts/export_group.py --max-retry 8
```

流程：
1. 脚本会打开浏览器并访问元宝页面
2. **请在浏览器中手动进入要备份的分组**，确保卡片列表已显示
3. 按提示按 Enter 开始备份
4. 脚本会智能滚动，确保加载分组内所有对话卡片
5. 自动逐一进入每个对话，抓取所有消息
6. 输出文件：`元宝分组全量备份_月日_时分.md`

#### 关于 `--max-retry` 参数

这个参数控制"当视口没找到新卡片时，最多尝试滚动几次才放弃"。

**推荐值公式**：`ceil(N / 10) + 1`，其中 N 为分组内对话总数

| 对话数量 | 推荐值 | 说明 |
|---------|--------|------|
| 1-20条  | 3      | 少量对话，滚动几次即可 |
| 21-40条 | 5      | 中等规模 |
| 41-70条 | 8      | 较大分组 |
| 71-100条| 11     | 大型分组 |
| 100+条  | N+1    | 超大型分组 |

示例：66条对话 → `ceil(66/10)+1 = 7+1 = 8`

## 📁 项目结构

```
.
├── README.md           # 本文件
├── requirements.txt    # Python 依赖
├── .gitignore         # Git 忽略规则
├── LICENSE            # MIT 许可证
└── scripts/
    ├── export_group.py      # 分组导出脚本
    └── export_ungrouped.py  # 未分组导出脚本
```

## ⚠️ 注意事项

### 安全性
- 脚本**不包含任何 API 密钥、Cookie 或用户凭证**
- 认证完全依赖 Playwright 的持久化会话（`browser_session/` 目录）
- **请勿将 `browser_session/` 目录提交到 Git**（已在 .gitignore 中忽略）

### 使用前提
1. 需要安装 Python 3.8+
2. 需要稳定的网络连接
3. 需要有足够的磁盘空间保存导出文件
4. 首次运行需要在浏览器中手动登录一次

### 滚动机制
- 分组导出脚本使用两种滚动方案：
  - **方案 A**（默认）：JS 操作列表容器 scrollTop，不依赖窗口坐标
  - **方案 B**（备用）：鼠标坐标滚动（坐标 800,500，经实测验证）
- 若遇到页面改版导致滚动失效，可参考脚本内的注释切换方案

### 输出文件
- 文件格式为 Markdown，每段对话以 `---` 分隔
- 用户发言标记为 `### [我]`
- 元宝回复标记为 `### [元宝]`
- 如存在思考过程，会以 `> **思考过程：**` 引用块形式保留

## 🔧 故障排除

### 1. 脚本卡在"等待登录"或列表加载不全
- 确保已登录腾讯账号
- 检查网络连接
- 适当增加 `await asyncio.sleep()` 的时间（在脚本中调整）

### 2. 滚动无法触发新内容
- 对于分组导出，尝试增加 `--max-retry` 参数值
- 检查屏幕分辨率，如使用方案 B 可能需要调整 `SCROLL_X`、`SCROLL_Y` 坐标

### 3. 浏览器崩溃或页面卡死
- 确保 Playwright Chromium 已正确安装：`playwright install chromium`
- 减少并行任务，或增加 `slow_mo` 参数（在脚本中调整）

### 4. 输出文件为空或内容不全
- 确认对话列表已完全加载（脚本会显示已发现对话数量）
- 检查是否有权限访问某些对话
- 确保 `browser_session/` 目录存在且包含有效会话

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化框架
- 腾讯元宝团队 - 提供了优秀的 AI 对话产品

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
- 报告 Bug
- 提出新功能建议
- 改进文档
- 优化代码

---

> **免责声明**：本工具仅为个人学习和技术研究目的开发，不隶属于腾讯公司。使用者需遵守腾讯元宝的服务条款，不得用于任何违法或侵犯他人权益的用途。

---

# Tencent Yuanbao Conversation Batch Export Tool

A Python script based on Playwright for batch exporting conversations from Tencent Yuanbao.

## ✨ Features

- **Two export modes**:
  - **Mode A**: Export all ungrouped conversations from the sidebar Chat list
  - **Mode B**: Export all conversations within a specified group (requires manual selection)
- **Smart scrolling**: Automatically handles virtual list scrolling to ensure complete conversation loading
- **Full capture**: Scrolls upward within each conversation to capture all historical messages
- **Thought process preservation**: Automatically identifies and preserves Yuanbao's thought process (if displayed)
- **Persistent login**: Uses browser persistent sessions, no need to log in repeatedly after first login
- **Output format**: Markdown format, easy to read and archive

## 📦 Installation

```bash
pip install -r requirements.txt
```

Also install Playwright browser kernel:

```bash
playwright install chromium
```

## 🚀 Usage

### Mode A: Export Ungrouped Conversations

```bash
python scripts/export_ungrouped.py
```

Process:
1. The script automatically opens browser and visits Yuanbao page
2. **Ensure you are logged in**, sidebar should show Chat and Group lists
3. Press Enter when prompted to start full-depth backup
4. Script expands all conversation groups, scrolls sidebar to load complete list
5. Automatically enters each conversation one by one, captures all messages
6. Output file: `yuanbao_full_content.md`

### Mode B: Export Conversations in Specific Group

```bash
# Default retry count (10 times)
python scripts/export_group.py

# Custom retry count (recommended)
python scripts/export_group.py --max-retry 8
```

Process:
1. Script opens browser and visits Yuanbao page
2. **Manually navigate to the group you want to backup** in browser, ensure card list is displayed
3. Press Enter when prompted to start backup
4. Script intelligently scrolls to ensure all conversation cards in group are loaded
5. Automatically enters each conversation one by one, captures all messages
6. Output file: `元宝分组全量备份_月日_时分.md`

#### About `--max-retry` Parameter

This parameter controls "maximum number of scroll attempts when no new cards are found in viewport".

**Recommended formula**: `ceil(N / 10) + 1`, where N is total number of conversations in group

| Conversation Count | Recommended Value | Description |
|--------------------|-------------------|-------------|
| 1-20               | 3                 | Small group, few scrolls needed |
| 21-40              | 5                 | Medium size |
| 41-70              | 8                 | Large group |
| 71-100             | 11                | Very large group |
| 100+               | N+1               | Extra large group |

Example: 66 conversations → `ceil(66/10)+1 = 7+1 = 8`

## 📁 Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── LICENSE            # MIT License
└── scripts/
    ├── export_group.py      # Group export script
    └── export_ungrouped.py  # Ungrouped export script
```

## ⚠️ Important Notes

### Security
- Script **does not contain any API keys, cookies, or user credentials**
- Authentication relies entirely on Playwright's persistent session (`browser_session/` directory)
- **Do NOT commit `browser_session/` directory to Git** (already excluded in .gitignore)

### Prerequisites
1. Python 3.8+ required
2. Stable network connection required
3. Enough disk space to save exported files
4. First run requires manual login in browser

### Scrolling Mechanism
- Group export script uses two scrolling methods:
  - **Method A** (default): JS operation of list container scrollTop, independent of window coordinates
  - **Method B** (backup): Mouse coordinate scrolling (coordinates 800,500, verified by user testing)
- If page redesign causes scrolling failure, refer to comments in script to switch method

### Output Files
- File format is Markdown, each conversation separated by `---`
- User messages marked as `### [我]`
- Yuanbao replies marked as `### [元宝]`
- If thought process exists, preserved as `> **思考过程：**` quote block

## 🔧 Troubleshooting

### 1. Script stuck at "waiting for login" or incomplete list loading
- Ensure logged into Tencent account
- Check network connection
- Increase `await asyncio.sleep()` duration (adjust in script)

### 2. Scrolling doesn't trigger new content
- For group export, try increasing `--max-retry` parameter value
- Check screen resolution, if using Method B may need to adjust `SCROLL_X`, `SCROLL_Y` coordinates

### 3. Browser crashes or page freezes
- Ensure Playwright Chromium correctly installed: `playwright install chromium`
- Reduce parallel tasks, or increase `slow_mo` parameter (adjust in script)

### 4. Output file empty or incomplete
- Confirm conversation list fully loaded (script shows discovered conversation count)
- Check if you have permission to access certain conversations
- Ensure `browser_session/` directory exists and contains valid session

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation framework
- Tencent Yuanbao team - Provides excellent AI conversation product

## 🤝 Contribution

Welcome to submit Issues and Pull Requests!
- Report bugs
- Suggest new features
- Improve documentation
- Optimize code

---

> **Disclaimer**: This tool is developed for personal learning and technical research purposes only, not affiliated with Tencent. Users must comply with Tencent Yuanbao's service terms and shall not use it for any illegal or rights-infringing purposes.