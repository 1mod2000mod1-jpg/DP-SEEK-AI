# في بداية الكود بعد imports
init_db()

# تعديل دالة الاستقبال الرئيسية لإضافة التحقق من الاشتراك
@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # التحقق من الحظر
    if is_banned(user_id):
        bot.reply_to(message, "❌ تم حظرك من استخدام البوت.")
        return
        
    # التحقق من الاشتراك (يمكنك تعليق هذا إذا أردت البوت مجانياً)
    if not is_subscribed(user_id) and not message.text.startswith('/subscribe'):
        bot.reply_to(message, "⚠️ يجب الاشتراك لاستخدام البوت. /subscribe")
        return
    
    # المعالجة العادية للرسائل
    try:
        txt = message.text
        res = requests.get(f"https://sii3.moayman.top/api/deepseek.php?v3={txt}", timeout=10).json()
        response = res.get("response", "ماكو رد من السيرفر ❌")
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "حدث خطأ ❌")
