"""
Ctl 秘书机器人 - 命令处理器
处理所有 Telegram 命令和消息
"""
import logging
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db

# 设置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== 辅助函数 ==========

def escape_md(text: str) -> str:
    """转义 MarkdownV2 特殊字符"""
    if not text:
        return ""
    escape_chars = r"_[]()~>#+-=|{}.!"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text


def format_datetime(dt_str: str) -> str:
    """格式化日期时间字符串"""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%m月%d日 %H:%M")
    except:
        return dt_str


async def register_user(update: Update):
    """注册用户到数据库"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)


# ========== 命令处理器 ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start - 开始使用机器人"""
    await register_user(update)
    user = update.effective_user

    welcome_text = f"""
👋 你好，{escape_md(user.first_name)}\！

🤖 *我是 Ctl 秘书* — 您的智能个人助理

我可以帮您：
📅 管理日程与提醒
✅ 记录待办事项
📝 保存笔记与备忘
🔔 设置定时提醒
📊 整理每日状态
💡 智能问答助手

发送 /help 查看完整命令列表
发送 /today 查看今日概览
"""

    keyboard = [
        [InlineKeyboardButton("📋 待办事项", callback_data="menu_todo"),
         InlineKeyboardButton("📝 快速笔记", callback_data="menu_note")],
        [InlineKeyboardButton("🔔 设置提醒", callback_data="menu_remind"),
         InlineKeyboardButton("📅 日程管理", callback_data="menu_schedule")],
        [InlineKeyboardButton("📊 今日概览", callback_data="menu_today")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help - 查看完整帮助指南"""
    help_text = """
📖 *Ctl 秘书 - 完整命令指南*

*📝 待办事项*
`/todo` - 查看待办列表
`/add` \<内容\> - 添加新任务
`/done` \<编号\> - 标记任务完成
`/clear` - 清空已完成任务

*🗒️ 笔记功能*
`/note` \<内容\> - 快速保存笔记
`/notes` - 查看笔记列表
`/nsearch` \<关键词\> - 搜索笔记

*🔔 提醒功能*
`/remind` \<时间\> \<内容\> - 设置提醒
`/reminds` - 查看提醒列表
`/rdel` \<编号\> - 删除提醒

*📅 日程管理*
`/schedule` - 查看日程列表
`/sadd` \<时间\> \<标题\> - 添加日程
`/sdel` \<编号\> - 删除日程

*📊 其他*
`/today` - 今日概览
`/start` - 重新开始
`/help` - 显示本帮助

*💡 使用示例：*
`/add 完成项目报告`
`/note 会议记录：明天下午3点开会`
`/remind 30m 喝水`
`/remind 2026\-07\-20 09:00 提交周报`
"""
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/today - 查看今日概览"""
    await register_user(update)
    user_id = update.effective_user.id
    overview = db.get_today_overview(user_id)

    today_str = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

    text = f"""
📊 *{escape_md(today_str)} {weekday} - 今日概览*

📌 待办事项：{overview['pending_todos']} 项待完成
📅 今日日程：{overview['today_schedules']} 项安排
🔔 今日提醒：{overview['today_reminders']} 项提醒
📝 笔记总数：{overview['total_notes']} 条记录

*快捷操作：*
"""
    keyboard = [
        [InlineKeyboardButton("➕ 添加任务", callback_data="menu_todo"),
         InlineKeyboardButton("📝 写笔记", callback_data="menu_note")],
        [InlineKeyboardButton("📋 查看待办", callback_data="cb_todo_list"),
         InlineKeyboardButton("📅 查看日程", callback_data="cb_schedule_list")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=reply_markup)


# ========== 待办事项 (Todo) ==========

async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/todo - 查看待办事项列表"""
    await register_user(update)
    user_id = update.effective_user.id

    todos = db.get_todos(user_id, completed=False)
    stats = db.get_todo_stats(user_id)

    if not todos:
        text = f"""
✅ *待办事项*

您当前没有待办任务\！
已完成：{stats['completed']} 项

使用 `/add \<内容\>` 添加新任务
"""
        await update.message.reply_text(text, parse_mode="MarkdownV2")
        return

    text = f"📋 *待办事项列表* \({len(todos)} 项待完成\)\n\n"
    for i, todo in enumerate(todos, 1):
        priority_emoji = {3: "🔴", 2: "🟡", 1: "🟢"}.get(todo["priority"], "⚪")
        text += f"{priority_emoji} *#{todo['id']}* {escape_md(todo['content'])}\n"
        text += f"    📂 {escape_md(todo['category'])}  |  ⏰ {format_datetime(todo['created_at'])}\n\n"

    text += f"\n_已完成 {stats['completed']} 项，共 {stats['total']} 项_"

    keyboard = [
        [InlineKeyboardButton("✅ 标记完成", callback_data="cb_todo_done"),
         InlineKeyboardButton("🗑️ 删除任务", callback_data="cb_todo_del")],
        [InlineKeyboardButton("➕ 添加任务", callback_data="menu_todo")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=reply_markup)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/add - 添加新任务"""
    await register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "📝 请告诉我需要添加什么任务\！\n\n"
            "*示例：*\n"
            "`/add 完成项目报告`\n"
            "`/add 买牛奶 priority:high`\n"
            "`/add 开会 category:work`",
            parse_mode="MarkdownV2"
        )
        return

    content = " ".join(context.args)
    category = "general"
    priority = 1

    # 解析参数
    if "category:" in content:
        match = re.search(r'category:(\w+)', content)
        if match:
            category = match.group(1)
            content = content.replace(f"category:{category}", "").strip()

    if "priority:high" in content or "priority:3" in content:
        priority = 3
        content = content.replace("priority:high", "").replace("priority:3", "").strip()
    elif "priority:medium" in content or "priority:2" in content:
        priority = 2
        content = content.replace("priority:medium", "").replace("priority:2", "").strip()

    todo_id = db.add_todo(user_id, content, category, priority)

    priority_emoji = {3: "🔴 高", 2: "🟡 中", 1: "🟢 低"}.get(priority)
    await update.message.reply_text(
        f"✅ *任务已添加\！*\n\n"
        f"📌 {escape_md(content)}\n"
        f"📂 分类：{category}\n"
        f"🔥 优先级：{priority_emoji}\n\n"
        f"编号：#{todo_id}\n"
        f"发送 `/done {todo_id}` 标记完成",
        parse_mode="MarkdownV2"
    )


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/done - 标记任务已完成"""
    await register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        todos = db.get_todos(user_id, completed=False)
        if not todos:
            await update.message.reply_text("✅ 您没有待完成的任务\！")
            return
        text = "📋 *请选择要完成的任务编号：*\n\n"
        for todo in todos:
            text += f"`/done {todo['id']}` \- {escape_md(todo['content'])}\n"
        await update.message.reply_text(text, parse_mode="MarkdownV2")
        return

    try:
        todo_id = int(context.args[0])
        if db.complete_todo(todo_id, user_id):
            await update.message.reply_text(f"✅ 任务 #{todo_id} 已完成\！")
        else:
            await update.message.reply_text("❌ 找不到该任务或无权操作\。")
    except ValueError:
        await update.message.reply_text("❌ 请输入正确的任务编号\。")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/clear - 清空已完成任务"""
    await register_user(update)
    user_id = update.effective_user.id

    count = db.clear_completed(user_id)
    if count > 0:
        await update.message.reply_text(f"🗑️ 已清空 {count} 项已完成任务\。")
    else:
        await update.message.reply_text("📭 没有已完成的任务需要清空\。")


# ========== 笔记 (Notes) ==========

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/note - 快速保存笔记"""
    await register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "📝 请告诉我需要记录什么\！\n\n"
            "*示例：*\n"
            "`/note 明天下午3点和客户开会`\n"
            "`/note title:会议记录 讨论了Q3计划和预算`",
            parse_mode="MarkdownV2"
        )
        return

    content = " ".join(context.args)
    title = None
    tags = None

    # 解析标题
    if "title:" in content:
        match = re.search(r'title:([^\s]+)', content)
        if match:
            title = match.group(1)
            content = content.replace(f"title:{title}", "").strip()

    # 解析标签
    if "tags:" in content:
        match = re.search(r'tags:([^\s]+)', content)
        if match:
            tags = match.group(1)
            content = content.replace(f"tags:{tags}", "").strip()

    note_id = db.add_note(user_id, content, title, tags)

    text = f"✅ *笔记已保存\！*\n\n📝 {escape_md(content)}\n\n编号：#{note_id}"
    if title:
        text += f"\n标题：{escape_md(title)}"
    if tags:
        text += f"\n标签：{escape_md(tags)}"

    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/notes - 查看笔记列表"""
    await register_user(update)
    user_id = update.effective_user.id

    notes = db.get_notes(user_id)

    if not notes:
        await update.message.reply_text(
            "📝 *笔记列表*\n\n您还没有保存任何笔记\。\n\n"
            "使用 `/note \<内容\>` 快速添加笔记\。",
            parse_mode="MarkdownV2"
        )
        return

    text = f"🗒️ *笔记列表* \({len(notes)} 条\)\n\n"
    for note in notes[:10]:  # 最多显示10条
        title_display = f"「{escape_md(note['title'])}」" if note['title'] else ""
        content_preview = escape_md(note['content'][:30]) + "..." if len(note['content']) > 30 else escape_md(note['content'])
        text += f"*#{note['id']}* {title_display}\n{content_preview}\n"
        text += f"    🏷️ {escape_md(note['tags'] or '无标签')} | 📅 {format_datetime(note['created_at'])}\n\n"

    if len(notes) > 10:
        text += f"_\.
\.\.还有 {len(notes) - 10} 条笔记_"

    keyboard = [
        [InlineKeyboardButton("🔍 搜索笔记", callback_data="cb_note_search"),
         InlineKeyboardButton("➕ 添加笔记", callback_data="menu_note")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=reply_markup)


async def nsearch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/nsearch - 搜索笔记"""
    await register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("🔍 请输入搜索关键词\n\n*示例：*`/nsearch 会议`", parse_mode="MarkdownV2")
        return

    keyword = " ".join(context.args)
    notes = db.get_notes(user_id, search=keyword)

    if not notes:
        await update.message.reply_text(f"🔍 未找到包含「{escape_md(keyword)}」的笔记\。")
        return

    text = f"🔍 *搜索结果* \- `{escape_md(keyword)}` \({len(notes)} 条\)\n\n"
    for note in notes:
        content_preview = escape_md(note['content'][:50]) + "..." if len(note['content']) > 50 else escape_md(note['content'])
        text += f"*#{note['id']}* {content_preview}\n\n"

    await update.message.reply_text(text, parse_mode="MarkdownV2")


# ========== 提醒 (Reminders) ==========

def parse_time(time_str: str) -> datetime:
    """解析时间字符串，返回 datetime 对象"""
    now = datetime.now()

    # 相对时间：30m, 2h, 1d
    if time_str.endswith("m") and time_str[:-1].isdigit():
        minutes = int(time_str[:-1])
        return now + timedelta(minutes=minutes)
    elif time_str.endswith("h") and time_str[:-1].isdigit():
        hours = int(time_str[:-1])
        return now + timedelta(hours=hours)
    elif time_str.endswith("d") and time_str[:-1].isdigit():
        days = int(time_str[:-1])
        return now + timedelta(days=days)

    # 绝对时间：2026-07-20 09:00 或 07-20 09:00
    formats = [
        "%Y-%m-%d %H:%M",
        "%m-%d %H:%M",
        "%H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            if fmt == "%H:%M":
                dt = dt.replace(year=now.year, month=now.month, day=now.day)
                if dt < now:
                    dt += timedelta(days=1)
            elif fmt == "%m-%d %H:%M":
                dt = dt.replace(year=now.year)
                if dt < now:
                    dt = dt.replace(year=now.year + 1)
            return dt
        except ValueError:
            continue

    raise ValueError(f"无法解析时间格式: {time_str}")


async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/remind - 设置定时提醒"""
    await register_user(update)
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text(
            "⏰ *设置提醒*\n\n"
            "*格式：* `/remind \<时间\> \<内容\>`\n\n"
            "*时间格式：*\n"
            "• `30m` \- 30分钟后\n"
            "• `2h` \- 2小时后\n"
            "• `1d` \- 1天后\n"
            "• `09:00` \- 今天/明天9点\n"
            "• `07\-20 09:00` \- 7月20日9点\n\n"
            "*示例：*\n"
            "`/remind 30m 喝水`\n"
            "`/remind 2h 开会`\n"
            "`/remind 09:00 晨会`\n"
            "`/remind 2026\-07\-20 14:00 提交报告`",
            parse_mode="MarkdownV2"
        )
        return

    time_str = context.args[0]
    content = " ".join(context.args[1:])

    try:
        remind_at = parse_time(time_str)
        reminder_id = db.add_reminder(user_id, content, remind_at)
        time_display = remind_at.strftime("%Y-%m-%d %H:%M")

        await update.message.reply_text(
            f"🔔 *提醒已设置\！*\n\n"
            f"📌 {escape_md(content)}\n"
            f"⏰ {escape_md(time_display)}\n\n"
            f"编号：#{reminder_id}",
            parse_mode="MarkdownV2"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ 时间格式不正确：{escape_md(str(e))}", parse_mode="MarkdownV2")


async def reminds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/reminds - 查看提醒列表"""
    await register_user(update)
    user_id = update.effective_user.id

    reminders = db.get_user_reminders(user_id)

    if not reminders:
        await update.message.reply_text(
            "🔔 *提醒列表*\n\n您没有待执行的提醒\。\n\n"
            "使用 `/remind \<时间\> \<内容\>` 设置提醒\。",
            parse_mode="MarkdownV2"
        )
        return

    text = f"⏰ *提醒列表* \({len(reminders)} 项\)\n\n"
    for r in reminders:
        time_display = format_datetime(r["remind_at"])
        text += f"*#{r['id']}* 📌 {escape_md(r['content'])}\n"
        text += f"    ⏰ {escape_md(time_display)}\n\n"

    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def rdel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/rdel - 删除提醒"""
    await register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("🗑️ 请指定要删除的提醒编号\n\n*示例：*`/rdel 1`", parse_mode="MarkdownV2")
        return

    try:
        reminder_id = int(context.args[0])
        if db.delete_reminder(reminder_id, user_id):
            await update.message.reply_text(f"🗑️ 提醒 #{reminder_id} 已删除\。")
        else:
            await update.message.reply_text("❌ 找不到该提醒或无权操作\。")
    except ValueError:
        await update.message.reply_text("❌ 请输入正确的提醒编号\。")


# ========== 日程 (Schedules) ==========

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/schedule - 查看日程列表"""
    await register_user(update)
    user_id = update.effective_user.id

    schedules = db.get_schedules(user_id)

    if not schedules:
        await update.message.reply_text(
            "📅 *日程列表*\n\n您暂时没有日程安排\。\n\n"
            "使用 `/sadd \<时间\> \<标题\>` 添加日程\。",
            parse_mode="MarkdownV2"
        )
        return

    text = f"📅 *日程安排* \({len(schedules)} 项\)\n\n"
    for s in schedules:
        start = format_datetime(s["start_time"])
        end = format_datetime(s["end_time"]) if s["end_time"] else ""
        time_range = f"{start} ~ {end}" if end else start

        text += f"*#{s['id']}* 📌 {escape_md(s['title'])}\n"
        text += f"    ⏰ {escape_md(time_range)}\n"
        if s["location"]:
            text += f"    📍 {escape_md(s['location'])}\n"
        if s["description"]:
            text += f"    📝 {escape_md(s['description'][:30])}\n"
        text += "\n"

    keyboard = [
        [InlineKeyboardButton("➕ 添加日程", callback_data="cb_schedule_add"),
         InlineKeyboardButton("🗑️ 删除日程", callback_data="cb_schedule_del")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=reply_markup)


async def sadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/sadd - 添加日程"""
    await register_user(update)
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text(
            "📅 *添加日程*\n\n"
            "*格式：* `/sadd \<时间\> \<标题\>`\n\n"
            "*示例：*\n"
            "`/sadd 09:00 团队晨会`\n"
            "`/sadd 2026\-07\-20 14:00 项目评审 location:会议室A`\n"
            "`/sadd 15:00 客户会议 desc:准备PPT和演示文稿`",
            parse_mode="MarkdownV2"
        )
        return

    time_str = context.args[0]
    content = " ".join(context.args[1:])

    # 解析参数
    location = None
    description = None

    if "location:" in content:
        match = re.search(r'location:([^\s]+)', content)
        if match:
            location = match.group(1)
            content = content.replace(f"location:{location}", "").strip()

    if "desc:" in content:
        match = re.search(r'desc:(.+?)(?=\s+\w+:|$)', content)
        if match:
            description = match.group(1).strip()
            content = content.replace(f"desc:{description}", "").strip()

    title = content

    try:
        start_time = parse_time(time_str)
        schedule_id = db.add_schedule(user_id, title, start_time,
                                      description=description, location=location)
        time_display = start_time.strftime("%Y-%m-%d %H:%M")

        text = f"✅ *日程已添加\！*\n\n📌 {escape_md(title)}\n⏰ {escape_md(time_display)}"
        if location:
            text += f"\n📍 {escape_md(location)}"
        if description:
            text += f"\n📝 {escape_md(description)}"
        text += f"\n\n编号：#{schedule_id}"

        await update.message.reply_text(text, parse_mode="MarkdownV2")
    except ValueError as e:
        await update.message.reply_text(f"❌ 时间格式不正确\。", parse_mode="MarkdownV2")


async def sdel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/sdel - 删除日程"""
    await register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("🗑️ 请指定要删除的日程编号\n\n*示例：*`/sdel 1`", parse_mode="MarkdownV2")
        return

    try:
        schedule_id = int(context.args[0])
        if db.delete_schedule(schedule_id, user_id):
            await update.message.reply_text(f"🗑️ 日程 #{schedule_id} 已删除\。")
        else:
            await update.message.reply_text("❌ 找不到该日程或无权操作\。")
    except ValueError:
        await update.message.reply_text("❌ 请输入正确的日程编号\。")


# ========== 回调处理 (Inline Keyboard) ==========

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理内联键盘回调"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if data == "menu_todo":
        await query.edit_message_text(
            "📝 *添加待办事项*\n\n"
            "请使用命令：\n"
            "`/add \<任务内容\>`\n\n"
            "*示例：*\n"
            "`/add 完成项目报告`\n"
            "`/add 买牛奶 priority:high`\n"
            "`/add 准备会议材料 category:work`",
            parse_mode="MarkdownV2"
        )

    elif data == "menu_note":
        await query.edit_message_text(
            "📝 *快速保存笔记*\n\n"
            "请使用命令：\n"
            "`/note \<笔记内容\>`\n\n"
            "*示例：*\n"
            "`/note 明天下午3点和客户开会`\n"
            "`/note title:会议记录 讨论了Q3计划`",
            parse_mode="MarkdownV2"
        )

    elif data == "menu_remind":
        await query.edit_message_text(
            "⏰ *设置提醒*\n\n"
            "请使用命令：\n"
            "`/remind \<时间\> \<内容\>`\n\n"
            "*示例：*\n"
            "`/remind 30m 喝水`\n"
            "`/remind 2h 开会`\n"
            "`/remind 09:00 晨会`",
            parse_mode="MarkdownV2"
        )

    elif data == "menu_schedule":
        await query.edit_message_text(
            "📅 *日程管理*\n\n"
            "查看日程：`/schedule`\n"
            "添加日程：`/sadd \<时间\> \<标题\>`\n\n"
            "*示例：*\n"
            "`/sadd 09:00 团队晨会`\n"
            "`/sadd 15:00 客户会议 location:会议室A`",
            parse_mode="MarkdownV2"
        )

    elif data == "menu_today":
        overview = db.get_today_overview(user_id)
        today_str = datetime.now().strftime("%Y年%m月%d日")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

        text = f"📊 *{escape_md(today_str)} {weekday} - 今日概览*\n\n"
        text += f"📌 待办事项：{overview['pending_todos']} 项\n"
        text += f"📅 今日日程：{overview['today_schedules']} 项\n"
        text += f"🔔 今日提醒：{overview['today_reminders']} 项\n"
        text += f"📝 笔记总数：{overview['total_notes']} 条"

        await query.edit_message_text(text, parse_mode="MarkdownV2")

    elif data == "cb_todo_list":
        todos = db.get_todos(user_id, completed=False)
        if not todos:
            await query.edit_message_text("📋 您没有待办任务\！")
            return
        text = f"📋 *待办事项* \({len(todos)} 项\)\n\n"
        for todo in todos[:5]:
            text += f"• {escape_md(todo['content'])}\n"
        await query.edit_message_text(text, parse_mode="MarkdownV2")

    elif data == "cb_schedule_list":
        schedules = db.get_schedules(user_id)
        if not schedules:
            await query.edit_message_text("📅 暂无日程安排\。")
            return
        text = f"📅 *日程安排* \({len(schedules)} 项\)\n\n"
        for s in schedules[:5]:
            start = format_datetime(s["start_time"])
            text += f"• {escape_md(start)} \- {escape_md(s['title'])}\n"
        await query.edit_message_text(text, parse_mode="MarkdownV2")

    elif data == "cb_note_search":
        await query.edit_message_text(
            "🔍 *搜索笔记*\n\n"
            "请使用命令：\n"
            "`/nsearch \<关键词\>`\n\n"
            "*示例：* `/nsearch 会议`",
            parse_mode="MarkdownV2"
        )

    elif data in ("cb_todo_done", "cb_todo_del", "cb_schedule_add", "cb_schedule_del"):
        action_map = {
            "cb_todo_done": "请发送 `/done \<编号\>` 标记任务完成",
            "cb_todo_del": "请发送 `/done \<编号\>` 或直接在待办列表中操作",
            "cb_schedule_add": "请发送 `/sadd \<时间\> \<标题\>` 添加日程",
            "cb_schedule_del": "请发送 `/sdel \<编号\>` 删除日程",
        }
        await query.edit_message_text(action_map.get(data, "请使用对应命令操作"))


# ========== 提醒检查任务 ==========

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    """定时检查并发送提醒"""
    reminders = db.get_pending_reminders()

    for r in reminders:
        try:
            await context.bot.send_message(
                chat_id=r["user_id"],
                text=f"🔔 *提醒时间到\！*\n\n📌 {escape_md(r['content'])}\n\n"
                     f"发送 `/done` 查看任务 或 `/reminds` 管理提醒",
                parse_mode="MarkdownV2"
            )
            db.complete_reminder(r["id"])
            logger.info(f"Reminder sent to user {r['user_id']}: {r['content']}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")


# ========== 未知消息处理 ==========

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通文本消息（智能回复）"""
    await register_user(update)
    text = update.message.text

    # 简单的自然语言识别
    if any(kw in text for kw in ["提醒", "记得", "别忘了"]):
        await update.message.reply_text(
            "⏰ 看起来您想设置提醒\！\n\n"
            "请使用命令格式：\n"
            "`/remind \<时间\> \<内容\>`\n\n"
            "*示例：* `/remind 30m 喝水`",
            parse_mode="MarkdownV2"
        )
    elif any(kw in text for kw in ["笔记", "记录", "记下来"]):
        await update.message.reply_text(
            "📝 想保存笔记吗\？\n\n"
            "请使用命令：\n"
            "`/note \<笔记内容\>`",
            parse_mode="MarkdownV2"
        )
    elif any(kw in text for kw in ["任务", "待办", "要做"]):
        await update.message.reply_text(
            "📋 想添加待办任务吗\？\n\n"
            "请使用命令：\n"
            "`/add \<任务内容\>`",
            parse_mode="MarkdownV2"
        )
    else:
        # 默认帮助回复
        await update.message.reply_text(
            f"💬 收到您的消息：{text[:50]}\n\n"
            f"我是 Ctl 秘书，可以帮您管理任务、笔记、提醒和日程\！\n\n"
            f"发送 /help 查看完整命令列表\。",
            parse_mode="MarkdownV2"
        )
