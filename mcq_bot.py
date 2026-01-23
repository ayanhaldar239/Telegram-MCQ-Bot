import os
import re
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import openai

# ========= ENVIRONMENT VARIABLES =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

user_mode = {}
user_settings = {}

# ========= COMMANDS =========
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
        "/level – Toggle difficulty\n"
        "/exam – Toggle exam\n"
        "/lang – Toggle language"
    )

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode[update.effective_user.id] = "upload"
    await update.message.reply_text(
        "📥 Paste MCQs now.\n"
        "Mark correct option with *"
    )

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode[update.effective_user.id] = "generate"
    await update.message.reply_text("✍ Send topic or text for MCQs")

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = user_settings[update.effective_user.id]
    s["level"] = {"Easy": "Moderate", "Moderate": "Tough", "Tough": "Easy"}[s["level"]]
    await update.message.reply_text(f"✅ Level set to {s['level']}")

async def exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = user_settings[update.effective_user.id]
    s["exam"] = "WBCS" if s["exam"] == "SSC CGL" else "SSC CGL"
    await update.message.reply_text(f"✅ Exam set to {s['exam']}")

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = user_settings[update.effective_user.id]
    s["lang"] = "Bengali" if s["lang"] == "English" else "English"
    await update.message.reply_text(f"✅ Language set to {s['lang']}")

# ========= AI GENERATION =========
def generate_mcqs(topic, s):
    prompt = f"""
Create 5 {s['level']} level MCQs for {s['exam']}.
Language: {s['lang']}
Topic/Text: {topic}

Rules:
- Competitive exam standard
- 4 options only
- Mark correct option with *
- Strict format

Q1.
A)
B)
C) *
D)
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )

    return response.choices[0].message.content

# ========= MCQ POSTER =========
async def post_mcqs(update: Update, text: str):
    blocks = re.split(r"\n\n+", text)

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 5:
            continue

        question = lines[0]
        options = []
        correct_id = 0

        for i, line in enumerate(lines[1:5]):
            if "*" in line:
                correct_id = i
                line = line.replace("*", "")
            options.append(line[3:].strip())

        await update.message.reply_poll(
            question=question,
            options=options,
            type="quiz",
            correct_option_id=correct_id,
            is_anonymous=False
        )

# ========= MESSAGE HANDLER =========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = user_mode.get(uid)

    if mode == "upload":
        await post_mcqs(update, update.message.text)

    elif mode == "generate":
        mcqs = generate_mcqs(update.message.text, user_settings[uid])
        await post_mcqs(update, mcqs)

# ========= MAIN =========
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
    asyncio.run(main())
