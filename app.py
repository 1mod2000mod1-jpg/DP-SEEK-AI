from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
import requests
import sqlite3
import os
from datetime import datetime, timedelta
import hashlib

# تهيئة Flask
app = Flask(__name__)
CORS(app)  # للسماح للموقع بالاتصال

# توكن البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# قائمة المشرفين
ADMINS = [6521966233]

# مفتاح سري للموقع (API Key)
API_SECRET = os.environ.get('API_SECRET', 'change-this-secret-key')

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                 (user_id INTEGER PRIMARY KEY, 
                  reason TEXT, 
                  banned_at TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subscribed_users
                 (user_id INTEGER PRIMARY KEY,
                  subscribed_at TIMESTAMP,
                  expires_at TIMESTAMP)''')
    
    # جدول جلسات الموقع
    c.execute('''CREATE TABLE IF NOT EXISTS web_sessions
                 (session_id TEXT PRIMARY KEY,
                  created_at TIMESTAMP,
                  message_count INTEGER DEFAULT 0)''')
    
    # جدول محادثات الموقع
    c.execute('''CREATE TABLE IF NOT EXISTS web_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  message TEXT,
                  response TEXT,
                  created_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

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

# ========== دوال جلسات الموقع ========== #
def create_session():
    session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO web_sessions VALUES (?, ?, 0)", (session_id, datetime.now()))
    conn.commit()
    conn.close()
    return session_id

def save_web_message(session_id, message, response):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO web_messages (session_id, message, response, created_at) VALUES (?, ?, ?, ?)",
              (session_id, message, response, datetime.now()))
    c.execute("UPDATE web_sessions SET message_count = message_count + 1 WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

# ========== دالة الذكاء الاصطناعي الموحدة ========== #
def get_ai_response(text):
    """دالة موحدة للحصول على رد من الذكاء الاصطناعي"""
    try:
        res = requests.get(f"https://sii3.top/api/deepseek.php?v3={text}", timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("response", "❌ لا يوجد رد من الخادم")
    except Exception as e:
        print(f"AI Error: {e}")
        return "⚠️ عذراً، حدث خطأ في المعالجة"

# ========== API للموقع ========== #
@app.route('/api/chat', methods=['POST'])
def web_chat():
    """API موحد للموقع - بدون حاجة للاشتراك"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return jsonify({"error": "الرسالة فارغة"}), 400
        
        # إنشاء جلسة جديدة إذا لم تكن موجودة
        if not session_id:
            session_id = create_session()
        
        # الحصول على الرد من الذكاء الاصطناعي
        ai_response = get_ai_response(message)
        
        # حفظ المحادثة
        save_web_message(session_id, message, ai_response)
        
        return jsonify({
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error in web_chat: {e}")
        return jsonify({"error": "حدث خطأ في الخادم"}), 500

@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """الحصول على سجل المحادثات لجلسة معينة"""
    try:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT message, response, created_at FROM web_messages WHERE session_id = ? ORDER BY created_at", 
                  (session_id,))
        messages = c.fetchall()
        conn.close()
        
        history = [
            {
                "message": msg[0],
                "response": msg[1],
                "timestamp": msg[2]
            }
            for msg in messages
        ]
        
        return jsonify({"history": history})
    
    except Exception as e:
        print(f"Error in get_history: {e}")
        return jsonify({"error": "حدث خطأ"}), 500

# ========== أوامر البوت (كما هي) ========== #
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
/ban - حظر مستخدم
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
    
    add_subscription(user_id, 30)
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
    
    c.execute("SELECT COUNT(*) FROM subscribed_users WHERE expires_at > ?", (datetime.now(),))
    active_subs = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM banned_users")
    banned_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM web_sessions")
    web_users = c.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""
📊 إحصائيات البوت:

👥 المشتركين النشطين (تليجرام): {active_subs}
🌐 مستخدمي الموقع: {web_users}
🚫 المستخدمين المحظورين: {banned_users}
🚀 حالة البوت: نشط ✅
    """
    
    bot.reply_to(message, stats_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ تم حظرك من استخدام البوت.")
        return
        
    if not is_subscribed(user_id):
        bot.reply_to(message, f"⚠️ عذراً {user_name},\nيجب الاشتراك لاستخدام البوت.\n\nاستخدم /subscribe للاشتراك")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    # استخدام الدالة الموحدة
    response = get_ai_response(message.text)
    bot.reply_to(message, response)

# ========== Routes ========== #
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
        "service": "Telegram AI Bot + Web API",
        "version": "2.0",
        "endpoints": {
            "chat": "/api/chat",
            "history": "/api/history/<session_id>"
        }
    })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

# ========== تشغيل التطبيق ========== #
if __name__ == '__main__':
    print("🚀 بدء تشغيل بوت التلغرام...")
    
    try:
        bot.remove_webhook()
        print("✅ تم حذف الويب هوك القديم")
    except Exception as e:
        print(f"⚠️ خطأ في حذف الويب هوك: {e}")
    
    try:
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
        bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        print(f"✅ تم تعيين الويب هوك: {webhook_url}")
    except Exception as e:
        print(f"⚠️ خطأ في تعيين الويب هوك: {e}")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 الخادم يعمل على المنفذ: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
