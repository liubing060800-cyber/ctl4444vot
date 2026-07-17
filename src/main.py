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
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("todo", todo_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("notes", notes_command))
    application.add_handler(CommandHandler("nsearch", nsearch_command))
    application.add_handler(CommandHandler("remind", remind_command))
    application.add_handler(CommandHandler("reminds", reminds_command))
    application.add_handler(CommandHandler("rdel", rdel_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("sadd", sadd_command))
    application.add_handler(CommandHandler("sdel", sdel_command))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


def setup_scheduler(application: Application):
    """使用 python-telegram-bot 内置的 JobQueue 设置定时任务"""
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            check_reminders,
            interval=60,  # 每 60 秒检查一次
            first=10,     # 启动后 10 秒开始第一次检查
            name="reminder_check",
        )
        logger.info("⏰ 提醒定时任务已启动（每分钟检查）")
    else:
        logger.warning("⚠️ JobQueue 未启用，提醒功能将不可用")


def run_webhook_mode():
    """Webhook 模式 - 用于 Render 等云平台"""
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL", "https://ctl444bot.onrender.com")
    webhook_path = "/telegram-webhook"
    full_webhook_url = f"{webhook_url.rstrip('/')}{webhook_path}"

    logger.info("🚀 启动 Webhook 模式...")
    logger.info(f"📡 Webhook URL: {full_webhook_url}")
    logger.info(f"🌐 监听端口: {port}")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .updater(None)  # Webhook 模式不需要 updater
        .build()
    )
    setup_handlers(application)
    setup_scheduler(application)

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=full_webhook_url,
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
    if os.environ.get("PORT") or os.environ.get("RENDER") or os.environ.get("WEBHOOK_URL"):
        run_webhook_mode()
    else:
        run_polling_mode()


if __name__ == "__main__":
    main()
