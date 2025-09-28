#!/usr/bin/env python3
import os
import logging
import telebot

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# التوكن
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN غير معروف")
    exit(1)

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        welcome_text = """
🎉 **مرحباً! البوت يعمل بنجاح**

🤖 **تم النشر على Render بنجاح**

✅ **الحالة: نشط ومستقر**

💡 **جرب هذه الأوامر:**
/start - هذه الرسالة
/ping - فحص الاتصال
/help - المساعدة
/about - معلومات عن البوت
        """
        bot.send_message(message.chat.id, welcome_text)
        logger.info(f"✅ تم معالجة /start من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['ping'])
def handle_ping(message):
    try:
        bot.send_message(message.chat.id, "🏓 **pong!**\n\n✅ البوت يعمل بشكل ممتاز!")
        logger.info(f"✅ تم معالجة /ping من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /ping: {e}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    try:
        help_text = """
🆘 **مركز المساعدة**

**الأوامر المتاحة:**
/start - بدء البوت
/ping - فحص الاتصال
/help - هذه الرسالة
/about - معلومات عن البوت

**معلومات تقنية:**
• يعمل على Render.com
• Python 3.10+
• إصدار مستقر
        """
        bot.send_message(message.chat.id, help_text)
        logger.info(f"✅ تم معالجة /help من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /help: {e}")

@bot.message_handler(commands=['about'])
def handle_about(message):
    try:
        about_text = """
🤖 **معلومات عن البوت**

**المميزات:**
✅ يعمل على السحابة (Render)
✅ مستقر وسريع
✅ يدعم الأوامر الأساسية
✅ سهل التطوير

**التقنيات:**
• Python
• pyTelegramBotAPI
• Render.com
        """
        bot.send_message(message.chat.id, about_text)
        logger.info(f"✅ تم معالجة /about من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /about: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        response = f"💬 **رسالتك:** {message.text}\n\n💡 استخدم /help لرؤية الأوامر المتاحة"
        bot.send_message(message.chat.id, response)
        logger.info(f"📩 رسالة من {message.from_user.first_name}: {message.text}")
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء تشغيل البوت...")
    
    try:
        # إزالة أي webhook سابق
        bot.remove_webhook()
        
        logger.info("✅ البوت جاهز للاستقبال...")
        
        # بدء الاستماع
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ رئيسي: {e}")
        
        # إعادة المحاولة بعد 10 ثواني
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
