import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import json

app = Flask(__name__)

# التوكنات من متغيرات البيئة
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# إنشاء كائن البوت
bot = Bot(token=TELEGRAM_TOKEN)

def start(update, context):
    """معالجة أمر /start"""
    update.message.reply_text('🌐 مرحباً! أنا بوت DeepSeek يعمل على السحابة!')

def help(update, context):
    """معالجة أمر /help"""
    update.message.reply_text('💡 أرسل لي أي سؤال وسأجيبك باستخدام الذكاء الاصطناعي!')

def echo(update, context):
    """معالجة الرسائل النصية"""
    user_message = update.message.text
    
    try:
        # إظهار حالة الكتابة
        bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        
        # استخدام DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["message"]["content"]
            update.message.reply_text(ai_response)
        else:
            update.message.reply_text("❌ حدث خطأ في الاتصال بالذكاء الاصطناعي")
            
    except Exception as e:
        print(f"Error: {e}")
        update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع")

@app.route('/')
def home():
    return '🤖 البوت يعمل على Render!'

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة ويبهوك تليجرام"""
    if request.method == 'POST':
        try:
            # تحليل البيانات الواردة من تليجرام
            data = request.get_json()
            update = Update.de_json(data, bot)
            
            # إنشاء Dispatcher
            dispatcher = Dispatcher(bot, None, workers=0)
            
            # إضافة handlers
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(CommandHandler("help", help))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
            
            # معالجة التحديث
            dispatcher.process_update(update)
            
            return 'OK'
        except Exception as e:
            print(f"Webhook error: {e}")
            return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """تعيين ويبهوك تليجرام"""
    try:
        # الحصول على عنوان التطبيق من Render
        webhook_url = f"https://{request.host}/webhook"
        
        # تعيين الويبهوك
        result = bot.set_webhook(webhook_url)
        
        return f'✅ تم تعيين الويبهوك: {webhook_url}<br>النتيجة: {result}'
    except Exception as e:
        return f'❌ خطأ في تعيين الويبهوك: {e}'

if __name__ == '__main__':
    print("🤖 جاري تشغيل البوت على السحابة...")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import json

app = Flask(__name__)

# التوكنات من متغيرات البيئة
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# إنشاء كائن البوت
bot = Bot(token=TELEGRAM_TOKEN)

def start(update, context):
    """معالجة أمر /start"""
    update.message.reply_text('🌐 مرحباً! أنا بوت DeepSeek يعمل على السحابة!')

def help(update, context):
    """معالجة أمر /help"""
    update.message.reply_text('💡 أرسل لي أي سؤال وسأجيبك باستخدام الذكاء الاصطناعي!')

def echo(update, context):
    """معالجة الرسائل النصية"""
    user_message = update.message.text
    
    try:
        # إظهار حالة الكتابة
        bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        
        # استخدام DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["message"]["content"]
            update.message.reply_text(ai_response)
        else:
            update.message.reply_text("❌ حدث خطأ في الاتصال بالذكاء الاصطناعي")
            
    except Exception as e:
        print(f"Error: {e}")
        update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع")

@app.route('/')
def home():
    return '🤖 البوت يعمل على Render!'

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالجة ويبهوك تليجرام"""
    if request.method == 'POST':
        try:
            # تحليل البيانات الواردة من تليجرام
            data = request.get_json()
            update = Update.de_json(data, bot)
            
            # إنشاء Dispatcher
            dispatcher = Dispatcher(bot, None, workers=0)
            
            # إضافة handlers
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(CommandHandler("help", help))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
            
            # معالجة التحديث
            dispatcher.process_update(update)
            
            return 'OK'
        except Exception as e:
            print(f"Webhook error: {e}")
            return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """تعيين ويبهوك تليجرام"""
    try:
        # الحصول على عنوان التطبيق من Render
        webhook_url = f"https://{request.host}/webhook"
        
        # تعيين الويبهوك
        result = bot.set_webhook(webhook_url)
        
        return f'✅ تم تعيين الويبهوك: {webhook_url}<br>النتيجة: {result}'
    except Exception as e:
        return f'❌ خطأ في تعيين الويبهوك: {e}'

if __name__ == '__main__':
    print("🤖 جاري تشغيل البوت على السحابة...")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
