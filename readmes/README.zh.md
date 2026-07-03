[![en](https://img.shields.io/badge/English-blue.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/README.md)
[![uk](https://img.shields.io/badge/українська-blue.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/readmes/README.uk.md)
[![pl](https://img.shields.io/badge/polski-green.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/readmes/README.pl.md)
[![zh](https://img.shields.io/badge/中文-red.svg)](https://github.com/PanVena/SteamAchievementLocalizer/blob/main/readmes/README.zh.md)


<h1 align="center">🏆 Steam 成就本地化工具 by Vena</h1>
<p align="center">
一款基于 PyQt6 的图形化工具，用于查看、编辑和本地化 Steam 成就文件 <code>UserGameStatsSchema_*.bin</code>。
</p>
<p align="center">
<b>⬇️ 下载最新版本</b>
</p>

<p align="center">
  <a href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest/download/SteamAchievementLocalizer-win64.zip"><img src="https://img.shields.io/badge/Windows-下载-00f2ff.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHg9IjBweCIgeT0iMHB4IiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDQ4IDQ4Ij4KPHBhdGggZmlsbD0iI2ZmZmZmZiIgZD0iTTYsNmgxN3YxN0g2VjZ6Ij48L3BhdGg+PHBhdGggZmlsbD0iI2ZmZmZmZiIgZD0iTTI1LjA0MiwyMi45NThWNkg0MnYxNi45NThIMjUuMDQyeiI+PC9wYXRoPjxwYXRoIGZpbGw9IiNmZmZmZmYiIGQ9Ik02LDI1aDE3djE3SDZWMjV6Ij48L3BhdGg+PHBhdGggZmlsbD0iI2ZmZmZmZiIgZD0iTTI1LDQyVjI1aDE3djE3SDI1eiI+PC9wYXRoPgo8L3N2Zz4=&logoColor=white" alt="Windows"></a>
  <a href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest/download/SteamAchievementLocalizer-linux64.AppImage"><img src="https://img.shields.io/badge/Linux-下载-10b981?logo=linux&logoColor=white" alt="Linux"></a>
  <a href="https://github.com/PanVena/SteamAchievementLocalizer/releases/latest/download/SteamAchievementLocalizer-macOS.dmg"><img src="https://img.shields.io/badge/macOS-下载-007AFF?logo=apple&logoColor=white" alt="macOS"></a>
  <a href="https://github.com/PanVena/SteamAchievementLocalizer/releases/"><img src="https://img.shields.io/github/downloads/PanVena/SteamAchievementLocalizer/total?color=bd00ff&logo=github&logoColor=white&label=下载量" alt="Downloads"></a>
</p>

<p align="center">
  <img src="readmes/screens/scrn_en.png" alt="截图" width="720">
</p>

---

## 目录
- [✨ 功能特性](#-功能特性)
- [⚠️ 编辑警告](#️-编辑警告)
- [🚀 快速上手](#-快速上手)
- [📂 文件位置](#-文件位置)
- [📝 导出与导入](#-导出与导入)
- [🧠 处理算法](#-处理算法)
- [🛠 架构与技术细节](#-架构与技术细节)
- [❓ 常见问题](#-常见问题)
- [🎨 主题开发](#-主题开发)
- [🌍 本地化翻译](#-本地化翻译)
- [🤝 参与贡献](#-参与贡献)
- [🔐 许可证](#-许可证)
- [👤 作者与社区](#-作者与社区)
- [💬 联系方式](#-联系方式)

---

## ✨ 功能特性
- **🚀 自动检测 Steam 路径**（Windows 注册表 / Linux / Snap 版；macOS 部分支持）。
- **📂 两种加载模式：**
  - 手动模式（选择一个 `.bin` 文件）；
  - 通过游戏 ID 加载（可粘贴完整链接，如 `https://store.steampowered.com/app/123456/`）。
- **🏆 成就解析与表格生成：**
  - 如区块中存在重复项，自动为描述创建单独行（`*_opis`）；
  - 缺少 `ukrainian` 列时自动补充；
  - 确保 `english` 列始终存在（文件中缺失则为空）。
- **✏️ 表格编辑**：可在应用内直接编辑。
- **🔍 全局搜索**：支持高亮 + 行过滤。
- **🔄 查找与替换**：针对选定列的对话框式查找替换。
- **👁️ 列显隐切换**。
- **📤 CSV 导出：**
  - 完整导出（文件中的所有语言）；
  - 翻译格式导出（english + translation + context）。
- **📥 CSV 导入**：将翻译数据导入到指定语言列。
- **💾 保存本地化内容**到二进制文件内。
- **📁 在文件管理器中查看并打开**原始二进制文件。
- **📋 Steam 中所有 `UserGameStatsSchema_*.bin` 文件列表**，包含：
  - 游戏名称（`gamename`）；
  - 版本（`version`）；
  - 大致成就数量（通过 English 条目数估算）。
- **⚙️ 设置缓存**（通过 `QSettings`）：界面语言、路径、上次 ID、上次版本（用于更新提醒）。
- **🌍 可扩展的多语言界面**：目前支持 English / Українська / Polski / 简体中文。
- **🎨 动态主题系统**：主题从 JSON 文件自动加载。
- **🔌 插件式架构**：模块化组件设计。

---

## ⚠️ 编辑警告
编辑 `.bin` 文件可能导致：
- Steam 缓存冲突；
- 显示文本不正确；
- 需要重新生成文件。

如果游戏中未显示你的翻译：
1. 关闭 Steam。
2. 删除目标文件 `UserGameStatsSchema_XXXX.bin`。
3. 打开该游戏的商店/社区页面（文件会重新生成）。
4. 重新应用你的翻译。

建议：修改前务必备份原始 `.bin` 文件。

---

## 🚀 快速上手
1. 下载[最新版本](https://github.com/PanVena/SteamAchievementLocalizer/releases/latest)。
2. 运行可执行程序。
3. 输入游戏 ID 或手动选择 `.bin` 文件。
4. 进行翻译 / 编辑。
5. （可选）导出 CSV → 发给翻译人员 → 导入回来。
6. 保存：
   - 直接保存到 Steam 目录（立即生效）；
   - 或保存到自定义路径（用作备份 / 分发）。

---

## 📂 文件位置
Windows 典型路径：
```
C:\Program Files (x86)\Steam\appcache\stats\UserGameStatsSchema_XXXX.bin
```
Linux（其中一种）：
```
~/.local/share/Steam/appcache/stats/UserGameStatsSchema_XXXX.bin
```
Snap 版路径会自动搜索。  
macOS 目前无法保证自动检测（如需请手动选择）。

---

## 📝 导出与导入

### 完整导出
CSV 包含所有列（包括可能的内部/服务列），适合分析或存档。

### 翻译导出
结构：
```
key,english,translation,<context>
```
- `translation` — 翻译人员编辑的列。
- `<context>` — 额外选择的上下文列（通过对话框选择），如 `polish`、`german` 或描述列等。

### 导入
1. 在对话框中选择目标列（数据将写入该列）。
2. 加载包含 `key`、`translation` 字段的 CSV。
3. 空的 `translation` 单元格将被忽略（保留现有值）。

### 备注：有意替换 english 列
如果你希望用（例如）最终定稿的本地化版本或编辑后的文本覆盖内建的 `english` 字符串：
- 以翻译格式导出（保留原始 english）。
- 编辑 `translation` 列，填入应成为新 "english" 的文本。
- 导入时选择 `english` 作为目标列。
- 工具将清除每个区块中的旧 English 条目并注入新内容。
这样你可以将 english 列改造为规范化 / 清理后 / 社区认可的基准文本。请注意其他本地化内容可能依赖原始英语的语义；建议先用完整导出 CSV 进行归档。

---

## 🧠 处理算法
1. 读取原始文件字节。
2. 通过标记 `\x00bits\x00 | \x02bit\x00` 分割为区块。
3. 在区块内通过模式 `\x00\x01name\x00(.*?)\x00` 查找成就键。
4. 丢弃不含 `\x01english\x00` 的区块（确保基本可本地化性）。
5. 通过模式 `\x01<lang>\x00<text>\x00` 提取语言标签。
6. 过滤服务词（`EXCLUDE_WORDS` 集合）。
7. 生成两个潜在行：
   - 主行（`key`）；
   - 描述行（`key_opis`），当出现重复语言键时。
8. 确保 `ukrainian` 和 `english` 列存在（缺失则插入空值）。
9. 构建表格并排序列头：`key`、`ukrainian`、`english`，其余按字母排序。
10. 保存时：
    - 清除先前的语言片段（针对正在重写的特定语言）；
    - 在 `english` 标记后插入新片段，若编辑 English 本身则替换；
    - 输出重建的二进制区块。

---

## 🛠 架构与技术细节
| 组件 | 说明 |
|------|------|
| 界面 | PyQt6（`QMainWindow`、`QTableWidget`） |
| 状态持久化 | `QSettings`（语言、路径、版本、上次 ID） |
| **本地化** | **从 `assets/locales/` 自动加载带元数据的 JSON** |
| **主题** | **从 `assets/themes/` 自动加载 JSON，按优先级排序** |
| **插件系统** | **模块化组件：`theme_manager`、`ui_builder`、`file_manager` 等** |
| 搜索高亮 | 自定义 `HighlightDelegate` |
| 对话框 | `FindReplaceDialog`、`ContextLangDialog`、`UserGameStatsListDialog` |
| 界面框架 | 自定义 JSON 本地化系统（非 Qt Linguist） |
| 插入算法 | 位置扫描 + 逐字节 `bytearray` 组装 |
| 行生成 | 启发式去重算法（描述归入 `_opis`） |

---

## ❓ 常见问题

| 问题 | 解答 |
|------|------|
| Steam 中看不到翻译 | 关闭 Steam → 删除文件 → 打开游戏页面 |
| 列表为空 | 文件错误或缺少 `english` 标记 |
| 显示乱码 | 确保使用 UTF-8 编码和正确的 CSV 格式 |
| 导入后无法撤销 | 导入会完全重建表格，这是预期行为 |
| 支持多少种语言？ | `.bin` 文件中存在的语言均可支持，外加强制添加的 `ukrainian` |
| 如何添加新的界面语言？ | 在 `assets/locales/` 中添加 JSON 文件即可 |

---

## 🤝 参与贡献
1. Fork → 创建分支 → 提交修改 → 发起 Pull Request。
2. 明确说明 PR 的修改内容（界面 / 逻辑 / 本地化）。
3. **贡献主题** — 直接将 JSON 文件添加到 `assets/themes/` 目录（详见[主题指南](readmes/contribution/THEMES.md)）。
4. **贡献语言** — 直接将 JSON 文件添加到 `assets/locales/` 目录（详见[本地化指南](readmes/contribution/LOCALES.md)）。
5. 验证要点：
   - 文件加载是否正常；
   - 导出 / 导入功能是否正常；
   - 保存到 Steam 和保存到独立文件是否正常；
   - 切换界面语言时是否不崩溃。

无需编写代码即可提出建议 — 直接发起 Issue 即可。

---

## 🎨 主题开发

想为应用创建自定义主题？**无需修改代码！**

只需在 `assets/themes/` 目录中创建一个 JSON 文件，你的主题就会自动出现在菜单中。

**📖 文档：**
- **[主题创建指南（英文）](readmes/contribution/THEMES.md)** — 创建自定义主题的完整说明
- **[Посібник зі створення тем（乌克兰语）](readmes/contribution/THEMES_UA.md)** — 乌克兰语完整说明

**✨ 特性：**
- 🎨 **自动发现**：放入 JSON 主题文件 → 自动出现在菜单中
- 🌍 **多语言支持**：主题名称支持多种语言
- 📊 **智能排序**：通过优先级值控制主题显示位置
- 🎯 **无需编程**：纯 JSON 配置，无需修改源码

**主题结构示例：**
```json
{
  "name": "MyTheme",
  "display_names": {
    "en": "🌙 Dark Blue",
    "ua": "🌙 Темно-синя"
  },
  "priority": 50,
  "palette": { /* 颜色 */ },
  "styles": { /* CSS样式 */ }
}
```

---

## 🌍 本地化翻译

想为应用添加你的语言？**无需修改代码！**

只需在 `assets/locales/` 目录中创建一个 JSON 文件，你的语言就会自动出现在菜单中。

**📖 文档：**
- **[语言添加指南（英文）](readmes/contribution/LOCALES.md)** — 添加新语言的完整说明
- **[Посібник з додавання мов（乌克兰语）](readmes/contribution/LOCALES_UA.md)** — 乌克兰语完整说明

**✨ 特性：**
- 🌐 **自动发现**：放入 JSON 语言文件 → 自动出现在语言菜单中
- 📊 **智能排序**：通过优先级值控制语言显示位置
- 🔄 **回退系统**：缺失的翻译自动回退到英文
- 🎯 **无需编程**：纯 JSON 配置，无需修改源码

**语言文件结构示例：**
```json
{
  "_locale_info": {
    "name": "Español",
    "native_name": "Español (Spanish)",
    "code": "es",
    "priority": 40
  },
  "app_title": "Localizador de Logros...",
  "language": "Idioma"
  // ... 其他翻译
}
```

**当前支持语言：**
- 🇬🇧 **English**（priority: 10）
- 🇺🇦 **Українська**（priority: 20）
- 🇵🇱 **Polski**（priority: 30）
- 🇨🇳 **简体中文**（priority: 40）

---

## 🔐 许可证
MIT — 自由使用、修改、翻译。欢迎给个 ⭐ 和注明作者。

---

## 👤 作者与社区
作者：**Vena**
- [GitHub](https://github.com/PanVena)
- Telegram: [@Pan_Vena](https://t.me/Pan_Vena)

翻译 / 讨论社区：
- 频道：[Ліниві ШІ](https://t.me/linyvi_sh_ji)

---

## 💬 联系方式
想法 / 问题 / bug 反馈 → 发起 Issue 或 Telegram 联系。  
喜欢这个项目？ — 分享给本地化社区并点个 ⭐。

<p align="center">为本地化与游戏而生 💛💙</p>
