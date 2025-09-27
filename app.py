import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# إعداد التسجيل لرؤية الأخطاء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداداتك - يُفضّل استخدام متغيرات البيئة
DEEPSEEK_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8389962293:AAHrLNDdcvL9M1jvTuv4n2pUKwa8F2deBYY"  # استبدل هذا بمفتاح بوتك الفعلي

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحباً! 🎉 أنا بوت موبي مدعوم بـ DeepSeek. كيف يمكنني مساعدتك اليوم؟')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 **أوامر البوت:**
/start - بدء التشغيل
/help - عرض المساعدة
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # تجاهل الرسائل الفارغة
    if not user_message.strip():
        await update.message.reply_text("يرجى إرسال رسالة نصية.")
        return
    
    # استخدام DeepSeek API
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
        # إرسال رسالة "جاري الكتابة..." أثناء الانتظار
        await update.message.reply_chat_action(action="typing")
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # وقت انتظار 30 ثانية
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_response = response_data["choices"][0]["message"]["content"]
                # تقسيم الرد إذا كان طويلاً جداً لتليجرام
                if len(ai_response) > 4096:
                    for i in range(0, len(ai_response), 4096):
                        await update.message.reply_text(ai_response[i:i+4096])
                else:
                    await update.message.reply_text(ai_response)
            else:
                await update.message.reply_text("⚠️ لم أتمكن من معالجة طلبك.")
        else:
            error_msg = f"❌ خطأ في API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            await update.message.reply_text("عذراً، حدث خطأ في الخادم. حاول مرة أخرى.")
            
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ انتهت مهلة الانتظار. حاول مرة أخرى.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("🌐 خطأ في الاتصال. تحقق من اتصالك بالإنترنت.")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Telegram Bot Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("⚠️ حدث خطأ في المعالجة. حاول مرة أخرى.")

def main():
    # التحقق من وجود التوكنات
    if TELEGRAM_BOT_TOKEN == "8389962293:AAHrLNDdcvL9M1jvTuv4n2pUKwa8F2deBYY":
        print("❌ يرجى إضافة TELEGRAM_BOT_TOKEN الفعلي!")
        return
    
    if not DEEPSEEK_API_KEY:
        print("❌ يرجى إضافة DEEPSEEK_API_KEY الفعلي!")
        return
    
    print("🤖 جاري تشغيل البوت...")
    
    try:
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)
        
        print("✅ البوت يعمل الآن! اضغط Ctrl+C لإيقافه.")
        print("🔍 اذهب إلى تليجرام وجرب إرسال /start للبوت")
        
        app.run_polling(poll_interval=2, timeout=60)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ فشل تشغيل البوت: {e}")

if __name__ == '__main__':
    main()
