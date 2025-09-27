import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
from flask import Flask, request

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداداتك
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "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")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")  # سيتعرف عليه Render تلقائياً

app = Flask(__name__)

# إنشاء تطبيق تليجرام
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحباً! 🎉 أنا بوت مدعوم بـ DeepSeek. كيف يمكنني مساعدتك اليوم؟')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 **أوامر البوت:**
/start - بدء التشغيل
/help - عرض المساعدة
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    if not user_message.strip():
        await update.message.reply_text("يرجى إرسال رسالة نصية.")
        return
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "أنت مساعد مفيد ومهذب."},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "max_tokens": 1000
    }
    
    try:
        await update.message.reply_chat_action(action="typing")
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_response = response_data["choices"][0]["message"]["content"]
                if len(ai_response) > 4096:
                    for i in range(0, len(ai_response), 4096):
                        await update.message.reply_text(ai_response[i:i+4096])
                else:
                    await update.message.reply_text(ai_response)
            else:
                await update.message.reply_text("⚠️ لم أتمكن من معالجة طلبك.")
        else:
            await update.message.reply_text("عذراً، حدث خطأ في الخادم. حاول مرة أخرى.")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Telegram Bot Error: {context.error}")

# إعداد handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_error_handler(error_handler)

@app.route('/')
def home():
    return "🤖 البوت يعمل! أرسل /start في تليجرام."

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), telegram_app.bot)
    telegram_app.process_update(update)
    return 'OK'

def set_webhook():
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")

if __name__ == '__main__':
    print("🤖 جاري تشغيل البوت...")
    print(f"✅ توكن البوت: {TELEGRAM_BOT_TOKEN[:10]}...")  # طباعة جزء من التوكن فقط للأمان
    
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ يرجى إضافة TELEGRAM_BOT_TOKEN الفعلي!")
    else:
        set_webhook()
        # على Render استخدم PORT المحدد من البيئة
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
