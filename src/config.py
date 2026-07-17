"""
Ctl 秘书机器人 - 配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token（必须从环境变量读取）
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

# OpenAI API Key（可选，用于智能问答）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 数据库路径（Render 用 /tmp，本地用 data）
if os.environ.get("RENDER"):
    DB_PATH = "/tmp/ctl_bot.db"
else:
    DB_PATH = os.getenv("DB_PATH", "data/ctl_bot.db")

# 时区
TIMEZONE = os.getenv("TIMEZONE", "Asia/Shanghai")

# 管理员 ID 列表（用于管理功能）
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# 日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
