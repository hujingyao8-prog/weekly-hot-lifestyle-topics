# Weekly Hot Topic Report — Automation Pipeline

```
生成中文HTML  →  localize_ru.py  →  upload_and_notify.py  →  Telegram群
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `upload_and_notify.py` | 上传两个HTML到GitHub Pages，发Telegram消息 |
| `localize_ru.py` | 按 ru-report-localizer Skill 规则生成俄语版 |
| `get_chat_id.py` | 一次性工具：查询群组 chat_id |
| `.github/workflows/weekly-report.yml` | 每周一自动运行的 GitHub Actions |

## 一次性配置（仅需做一次）

### 1. 创建 GitHub 仓库 + 开启 Pages

1. 在 GitHub 创建公开仓库，名称如 `weekly-hot-topics`
2. `Settings → Pages → Source` 选 **Deploy from a branch → main**
3. 生成 Personal Access Token：`Settings → Developer settings → Tokens (classic)`，勾选 `repo` 权限

### 2. 创建 Telegram Bot

1. 在 Telegram 找 **@BotFather** → `/newbot` → 得到 Bot Token
2. 把 Bot 加入目标群组，并给予发消息权限
3. 在群里随便发一条消息，然后运行：
   ```bash
   TG_BOT_TOKEN=你的token python get_chat_id.py
   ```
   记录输出的 `chat_id`（负数，如 `-1001234567890`）

### 3. 配置 GitHub Actions Secrets

在仓库 `Settings → Secrets and variables → Actions` 添加：

| Secret 名 | 值 |
|---|---|
| `TG_BOT_TOKEN` | BotFather 给的 token |
| `TG_CHAT_ID` | 群组 chat_id（负整数） |

> `GITHUB_TOKEN` 由 Actions 自动提供，无需手动配置。

## 本地手动运行

```bash
pip install requests beautifulsoup4

# 设置环境变量
export GITHUB_TOKEN=ghp_xxxx
export GITHUB_OWNER=your_username
export GITHUB_REPO=weekly-hot-topics
export TG_BOT_TOKEN=123456:ABC-xxxx
export TG_CHAT_ID=-1001234567890

# 生成俄语版
python localize_ru.py --input report-2026-08-18.html --output report-2026-08-18-ru.html

# 上传并发送
python upload_and_notify.py --zh report-2026-08-18.html --ru report-2026-08-18-ru.html
```

## （可选）接入完整AI翻译

如需 LLM 翻译全文（而非仅词汇表替换），设置：
```bash
export TRANSLATE_API=anthropic
export ANTHROPIC_API_KEY=sk-ant-xxxx
python localize_ru.py ...
```

## GitHub Pages 访问延迟

文件推送后约 **1-3 分钟**内 Pages 生效。
Actions 中 upload 和 notify 步骤之间可加 `sleep 120` 等待。
