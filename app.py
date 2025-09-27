import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = Flask(__name__)

# التوكنات من متغيرات البيئة في Render
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# إنشاء تطبيق تليجرام
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🌐 مرحباً! أنا الآن أعمل على السحابة!')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('💡 أرسل لي أي سؤال وسأجيبك!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    await update.message.reply_chat_action(action="typing")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["message"]["content"]
            await update.message.reply_text(ai_response)
        else:
            await update.message.reply_text("❌ حدث خطأ في الاتصال")
            
    except Exception as e:
        await update.message.reply_text("❌ عذراً، حدث خطأ")

# إعداد ال handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return '🤖 البوت يعمل على Render!'

@app.route('/webhook', methods=['POST'])
def webhook():
    # استقبال البيانات من تليجرام
    json_data = request.get_json()
    update = Update.de_json(json_data, telegram_app.bot)
    telegram_app.process_update(update)
    return 'OK'

def set_webhook():
    # الحصول على عنوان التطبيق من Render
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        webhook_url = f"{render_url}/webhook"
        telegram_app.bot.set_webhook(webhook_url)
        print(f"✅ تم تعيين الويبهوك: {webhook_url}")

if __name__ == '__main__':
    print("🤖 جاري تشغيل البوت على السحابة...")
    set_webhook()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
