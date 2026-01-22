from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import re
import openai

# ====== CONFIG ======
BOT_TOKEN = "8067802179:AAFises245Wos6A36affylDp8YYoZUkkb14"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

user_mode = {}
user_settings = {}

# ====== COMMANDS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings[update.effective_user.id] = {
        "level": "Moderate",
        "exam": "SSC CGL",
        "lang": "English"
    }
    await update.message.reply_text(
        "📘 MCQ Bot Ready\n\n"
        "/upload – Upload MCQs\n"
        "/generate – Auto-create MCQs\n"
        "/level – Easy / Moderate / Tough\n"
        "/exam – SSC CGL / WBCS\n"
        "/lang – English / Bengali"
    )

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode[update.effective_user.id] = "upload"
    await update.message.reply_text("📥 Paste MCQs now.\nMark correct option with *")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode[update.effective_user.id] = "generate"
    await update.message.reply_text("✍ Send topic or text for MCQs")

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings[update.effective_user.id]["level"] = "Tough"
    await update.message.reply_text("✅ Level set to Tough")

async def exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings[update.effective_user.id]["exam"] = "WBCS"
    await update.message.reply_text("✅ Exam set to WBCS")

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings[update.effective_user.id]["lang"] = "Bengali"
    await update.message.reply_text("✅ Language set to Bengali")

# ====== HANDLER ======
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = user_mode.get(uid)

    if mode == "upload":
        await post_mcqs(update, update.message.text)

    elif mode == "generate":
        settings = user_settings[uid]
        mcqs = ai_generate_mcqs(update.message.text, settings)
        await post_mcqs(update, mcqs)

# ====== AI FUNCTION ======
def ai_generate_mcqs(topic, s):
    prompt = f"""
Create 5 {s['level']} level MCQs for {s['exam']}.
Language: {s['lang']}
Topic/Text: {topic}

Rules:
- Competitive exam standard
- 4 options
- Mark correct option with *
- Strict format
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content

# ====== MCQ POSTER ======
async def post_mcqs(update, text):
    blocks = re.split(r"\n\n+", text)

    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 5:
            continue

        question = lines[0]
        options = []
        correct = 0

        for i, opt in enumerate(lines[1:5]):
            if "*" in opt:
                correct = i
                opt = opt.replace("*", "")
            options.append(opt[3:].strip())

        await update.message.reply_poll(
            question=question,
            options=options,
            type="quiz",
            correct_option_id=correct,
            is_anonymous=False
        )

# ====== MAIN ======
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("level", level))
    app.add_handler(CommandHandler("exam", exam))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
