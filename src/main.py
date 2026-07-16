"""
Ctl 秘书机器人 - 主入口文件
启动 Telegram Bot 并注册所有命令处理器
"""
import logging
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


def main():
    """主函数：创建应用、注册处理器、启动轮询"""

    logger.info("🚀 Ctl 秘书机器人正在启动...")

    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册命令处理器
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

    # 设置定时任务 - 每分钟检查一次提醒
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

    # 启动 Bot（轮询模式）
    logger.info("✅ Ctl 秘书机器人已启动！按 Ctrl+C 停止。")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
