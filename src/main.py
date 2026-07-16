"""
Ctl 秘书机器人 - 主入口文件
支持 Webhook 模式（用于 Render 等云平台）和 Polling 模式（本地开发）
"""
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, LOG_LEVEL
from handlers import (
    start_command,
    help_command,
    today_command,
    todo_command,
    add_command,
    done_command,
    clear_command,
    note_command,
    notes_command,
    nsearch_command,
    remind_command,
    reminds_command,
    rdel_command,
    schedule_command,
    sadd_command,
    sdel_command,
    callback_handler,
    handle_message,
    check_reminders,
)

# 设置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)


def setup_handlers(application: Application):
    """注册所有命令处理器"""
    # 基础命令
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))

    # 待办事项命令
    application.add_handler(CommandHandler("todo", todo_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("clear", clear_command))

    # 笔记命令
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("notes", notes_command))
    application.add_handler(CommandHandler("nsearch", nsearch_command))

    # 提醒命令
    application.add_handler(CommandHandler("remind", remind_command))
    application.add_handler(CommandHandler("reminds", reminds_command))
    application.add_handler(CommandHandler("rdel", rdel_command))

    # 日程命令
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("sadd", sadd_command))
    application.add_handler(CommandHandler("sdel", sdel_command))

    # 回调处理器（内联键盘）
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 普通消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


def setup_scheduler(application: Application):
    """设置定时任务"""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=1,
        args=[application],
        id="reminder_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("⏰ 提醒定时任务已启动（每分钟检查）")
    return scheduler


def run_webhook_mode():
    """Webhook 模式 - 用于 Render 等云平台"""
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL", "https://ctl444bot.onrender.com")
    webhook_path = "/telegram-webhook"
    full_webhook_url = f"{webhook_url.rstrip('/')}{webhook_path}"

    logger.info(f"🚀 启动 Webhook 模式...")
    logger.info(f"📡 Webhook URL: {full_webhook_url}")
    logger.info(f"🌐 监听端口: {port}")

    application = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(application)
    setup_scheduler(application)

    # 启动 Webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=full_webhook_url,
        secret_token=None,
    )


def run_polling_mode():
    """Polling 模式 - 用于本地开发"""
    logger.info("🚀 启动 Polling 模式...")

    application = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(application)
    setup_scheduler(application)

    logger.info("✅ Ctl 秘书机器人已启动！按 Ctrl+C 停止。")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """主函数：根据环境选择启动模式"""
    # 如果有 RENDER 环境变量，使用 Webhook 模式
    if os.environ.get("RENDER") or os.environ.get("WEBHOOK_URL"):
        run_webhook_mode()
    else:
        run_polling_mode()


if __name__ == "__main__":
    main()
