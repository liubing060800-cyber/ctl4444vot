# 🤖 Ctl 秘书机器人

> 基于 Telegram Bot API 的综合型智能秘书机器人，支持待办事项、笔记管理、定时提醒、日程安排等功能。

---

## ✨ 功能特性

| 功能模块 | 说明 |
|---------|------|
| 📋 **待办事项** | 添加、查看、完成、删除、清空任务，支持优先级和分类 |
| 📝 **笔记管理** | 快速保存笔记，支持标题、标签、搜索 |
| ⏰ **定时提醒** | 支持相对时间（30m/2h/1d）和绝对时间设置 |
| 📅 **日程安排** | 管理日程，支持地点和描述 |
| 📊 **今日概览** | 一键查看今日所有事项汇总 |
| 💬 **智能识别** | 自动识别消息意图，引导用户使用 |

---

## 📁 项目结构

```
ctl-bot/
├── src/
│   ├── main.py           # 主入口文件
│   ├── config.py         # 配置文件
│   ├── database.py       # SQLite 数据库操作
│   └── handlers.py       # 命令处理器
├── data/                 # 数据库文件目录（自动创建）
├── .env                  # 环境变量（从 .env.example 复制）
├── .env.example          # 环境变量模板
├── requirements.txt      # Python 依赖
└── README.md             # 本文件
```

---

## 🚀 快速部署

### 方式一：本地运行

```bash
# 1. 克隆/下载项目后进入目录
cd ctl-bot

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或：venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 复制环境变量文件
cp .env.example .env

# 5. 启动机器人
cd src
python main.py
```

### 方式二：部署到服务器（后台运行）

```bash
# 使用 nohup 后台运行
cd src
nohup python main.py > ../bot.log 2>&1 &

# 或使用 systemd 服务（推荐）
```

### 方式三：Docker 部署

```bash
# 创建 Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/src
CMD ["python", "main.py"]
EOF

# 构建并运行
docker build -t ctl-bot .
docker run -d --name ctl-bot --restart unless-stopped ctl-bot
```

### 方式四：免费云平台部署（推荐新手）

#### Railway 部署（免费）

1. 注册 [Railway](https://railway.app/) 账号
2. 新建项目，连接 GitHub 仓库
3. 设置环境变量 `BOT_TOKEN`
4. 自动部署，无需额外配置

#### Render 部署（免费）

1. 注册 [Render](https://render.com/) 账号
2. 新建 Web Service，连接 GitHub
3. 设置环境变量 `BOT_TOKEN`
4. 免费实例会自动休眠，建议配合 UptimeRobot 保活

---

## 📖 命令列表

### 基础命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/start` | 开始使用 | `/start` |
| `/help` | 帮助指南 | `/help` |
| `/today` | 今日概览 | `/today` |

### 待办事项

| 命令 | 说明 | 示例 |
|------|------|------|
| `/todo` | 查看待办列表 | `/todo` |
| `/add` | 添加任务 | `/add 完成项目报告` |
| `/add` | 高优先级任务 | `/add 紧急会议 priority:high` |
| `/add` | 分类任务 | `/add 买牛奶 category:生活` |
| `/done` | 标记完成 | `/done 1` |
| `/clear` | 清空已完成 | `/clear` |

### 笔记管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `/note` | 保存笔记 | `/note 明天下午3点开会` |
| `/note` | 带标题笔记 | `/note title:会议 讨论了Q3计划` |
| `/notes` | 查看笔记 | `/notes` |
| `/nsearch` | 搜索笔记 | `/nsearch 会议` |

### 定时提醒

| 命令 | 说明 | 示例 |
|------|------|------|
| `/remind` | 相对时间提醒 | `/remind 30m 喝水` |
| `/remind` | 小时提醒 | `/remind 2h 开会` |
| `/remind` | 今日时间 | `/remind 09:00 晨会` |
| `/remind` | 指定日期 | `/remind 2026-07-20 14:00 提交报告` |
| `/reminds` | 查看提醒 | `/reminds` |
| `/rdel` | 删除提醒 | `/rdel 1` |

### 日程管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `/schedule` | 查看日程 | `/schedule` |
| `/sadd` | 添加日程 | `/sadd 09:00 团队晨会` |
| `/sadd` | 带地点日程 | `/sadd 15:00 客户会议 location:会议室A` |
| `/sdel` | 删除日程 | `/sdel 1` |

---

## ⚙️ 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `BOT_TOKEN` | ✅ | Telegram Bot Token（从 BotFather 获取） |
| `OPENAI_API_KEY` | ❌ | OpenAI API Key（可选，用于AI问答） |
| `DB_PATH` | ❌ | 数据库路径，默认 `data/ctl_bot.db` |
| `TIMEZONE` | ❌ | 时区，默认 `Asia/Shanghai` |
| `ADMIN_IDS` | ❌ | 管理员ID，逗号分隔 |
| `LOG_LEVEL` | ❌ | 日志级别，默认 `INFO` |

---

## 🔧 进阶配置

### 添加智能问答（OpenAI）

1. 在 `.env` 中填入 `OPENAI_API_KEY`
2. 在 `handlers.py` 中取消 `handle_message` 的 AI 回复注释
3. 重启机器人

### 设置 Webhook（生产环境）

```python
# 在 main.py 中，将 application.run_polling() 替换为：
application.run_webhook(
    listen="0.0.0.0",
    port=8443,
    webhook_url="https://your-domain.com/webhook",
)
```

### 数据备份

```bash
# SQLite 数据库文件可直接复制备份
cp data/ctl_bot.db data/ctl_bot_backup_$(date +%Y%m%d).db
```

---

## 📝 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-16 | 初始版本，包含核心功能 |

---

## 📄 License

MIT License
