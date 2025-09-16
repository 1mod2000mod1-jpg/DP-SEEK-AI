import telebot
import requests
import time
import os

# الحصول على التوكن من متغير البيئة
bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    print("Error: BOT_TOKEN not set!")
    exit(1)

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.reply_to(message, "هلا حبي 🌹 ارسل أي كلمة واني اجاوبك")

@bot.message_handler(func=lambda msg: True)
def message_handler(message):
    try:
        txt = message.text
        res = requests.get(f"https://sii3.moayman.top/api/deepseek.php?v3={txt}", timeout=10)
        res.raise_for_status()
        data = res.json()
        response = data.get("response", "ماكو رد من السيرفر ❌")
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "حدث خطأ في الاتصال ❌")

if __name__ == "__main__":
    print("✅ البوت يعمل على Render!")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(15)
