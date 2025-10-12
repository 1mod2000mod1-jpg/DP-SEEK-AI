from flask import Flask, request, jsonify
import telebot
import requests
import sqlite3
import os
from datetime import datetime, timedelta

# تهيئة Flask
app = Flask(__name__)

# توكن البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# قائمة المشرفين
ADMINS = [6521966233]  # استبدل برقمك الحقيقي

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    
    # جدول الأعضاء المحظورين
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                 (user_id INTEGER PRIMARY KEY, 
                  reason TEXT, 
                  banned_at TIMESTAMP)''')
    
    # جدول المشتركين
    c.execute('''CREATE TABLE IF NOT EXISTS subscribed_users
                 (user_id INTEGER PRIMARY KEY,
                  subscribed_at TIMESTAMP,
                  expires_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# استدعاء التهيئة عند البدء
init_db()

# ========== دوال الحظر ========== #
def ban_user(user_id, reason="إساءة استخدام"):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO banned_users VALUES (?, ?, ?)",
              (user_id, reason, datetime.now()))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM banned_users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

# ========== دوال الاشتراك ========== #
def add_subscription(user_id, days=30):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    subscribed_at = datetime.now()
    expires_at = subscribed_at + timedelta(days=days)
    c.execute("INSERT OR REPLACE INTO subscribed_users VALUES (?, ?, ?)",
              (user_id, subscribed_at, expires_at))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT expires_at FROM subscribed_users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        expires_at = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
        return datetime.now() < expires_at
    return False

# ========== أوامر البوت ========== #
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ تم حظرك من استخدام البوت.")
        return
        
    welcome_text = """
    🌹 أهلاً وسهلاً بك!
    
    أنا بوت الذكاء الاصطناعي، يمكنك محاورتي في أي موضوع.
    
    📋 الأوامر المتاحة:
    /help - عرض المساعدة
    /mysub - التحقق من حالة الاشتراك
    /subscribe - الاشتراك في البوت
    """
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = """
    🆘 أوامر المساعدة:
    
    /start - بدء استخدام البوت
    /help - عرض هذه المساعدة
    /mysub - التحقق من حالة الاشتراك
    /subscribe - الاشتراك في البوت
    
    للمشرفين فقط:
    /ban - حظر مستخدم (بالرد على رسالته)
    /unban - إلغاء حظر مستخدم
    /stats - إحصائيات البوت
    """
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['subscribe'])
def subscribe_cmd(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ تم حظرك من استخدام البوت.")
        return
    
    add_subscription(user_id, 30)  # 30 يوم اشتراك
    bot.reply_to(message, "✅ تم تفعيل اشتراكك لمدة 30 يوم!")

@bot.message_handler(commands=['mysub'])
def check_subscription(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ تم حظرك من استخدام البوت.")
        return
    
    if is_subscribed(user_id):
        bot.reply_to(message, "✅ اشتراكك مفعل ومازال صالحاً")
    else:
        bot.reply_to(message, "❌ ليس لديك اشتراك فعال. استخدم /subscribe للاشتراك")

# ========== أوامر المشرفين ========== #
@bot.message_handler(commands=['ban'])
def ban_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ ليس لديك صلاحية لهذا الأمر.")
        return
        
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        reason = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else "إساءة استخدام"
        
        ban_user(target_id, reason)
        bot.reply_to(message, f"✅ تم حظر المستخدم {target_id}")
    else:
        bot.reply_to(message, "❌ يجب الرد على رسالة المستخدم لحظره.")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ ليس لديك صلاحية لهذا الأمر.")
        return
        
    try:
        target_id = int(message.text.split()[1])
        unban_user(target_id)
        bot.reply_to(message, f"✅ تم إلغاء حظر المستخدم {target_id}")
    except:
        bot.reply_to(message, "❌ استخدم: /unban <user_id>")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ ليس لديك صلاحية لهذا الأمر.")
        return
    
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    
    # عدد المشتركين
    c.execute("SELECT COUNT(*) FROM subscribed_users WHERE expires_at > ?", (datetime.now(),))
    active_subs = c.fetchone()[0]
    
    # عدد المحظورين
    c.execute("SELECT COUNT(*) FROM banned_users")
    banned_users = c.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""
    📊 إحصائيات البوت:
    
    👥 المشتركين النشطين: {active_subs}
    🚫 المستخدمين المحظورين: {banned_users}
    🚀 حالة البوت: نشط ✅
    """
    
    bot.reply_to(message, stats_text)

# ========== معالجة الرسائل العادية ========== #
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # التحقق من الحظر
    if is_banned(user_id):
        bot.reply_to(message, "❌ تم حظرك من استخدام البوت.")
        return
        
    # التحقق من الاشتراك
    if not is_subscribed(user_id):
        bot.reply_to(message, f"⚠️ عذراً {user_name},\nيجب الاشتراك لاستخدام البوت.\n\nاستخدم /subscribe للاشتراك")
        return
    
    # إظهار حالة "يكتب..." للمستخدم
    bot.send_chat_action(message.chat.id, 'typing')
    
    # معالجة الرسالة باستخدام الذكاء الاصطناعي
    try:
        txt = message.text
        res = requests.get(f"https://sii3.top/api/deepseek.php?v3={txt}", timeout=10)
        res.raise_for_status()
        data = res.json()
        response = data.get("response", "❌ لا يوجد رد من الخادم")
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "⚠️ عذراً، حدث خطأ في المعالجة")

# ========== routes للويب هوك ========== #
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid content type', 403

@app.route('/')
def home():
    return jsonify({
        "status": "Bot is running!",
        "service": "Telegram AI Bot",
        "version": "1.0"
    })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

# ========== تشغيل التطبيق ========== #
if __name__ == '__main__':
    print("🚀 بدء تشغيل بوت التلغرام...")
    
    # حذف الويب هوك القديم
    try:
        bot.remove_webhook()
        print("✅ تم حذف الويب هوك القديم")
    except Exception as e:
        print(f"⚠️ خطأ في حذف الويب هوك: {e}")
    
    # تعيين الويب هوك الجديد
    try:
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
        bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        print(f"✅ تم تعيين الويب هوك: {webhook_url}")
    except Exception as e:
        print(f"⚠️ خطأ في تعيين الويب هوك: {e}")
    
    # تشغيل الخادم
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 الخادم يعمل على المنفذ: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
