import os
import requests
from flask import Flask, request
import telegram

app = Flask(__name__)

# التوكنات من متغيرات البيئة
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# إنشاء كائن البوت
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def get_ai_response(message_text):
    """الحصول على رد من DeepSeek"""
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message_text}],
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return "❌ حدث خطأ في الاتصال بالذكاء الاصطناعي"
            
    except Exception as e:
        print(f"AI Error: {e}")
        return "❌ عذراً، حدث خطأ غير متوقع"

@app.route('/')
def home():
    return '🤖 البوت يعمل على Render!'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print("📩 Received data:", data)
            
            if 'message' in data and 'text' in data['message']:
                chat_id = data['message']['chat']['id']
                message_text = data['message']['text']
                
                print(f"💬 Message from {chat_id}: {message_text}")
                
                if message_text == '/start':
                    bot.send_message(
                        chat_id=chat_id, 
                        text='🌐 مرحباً! أنا بوت DeepSeek. اسألني أي شيء!'
                    )
                elif message_text == '/help':
                    bot.send_message(
                        chat_id=chat_id, 
                        text='💡 فقط أرسل لي أي سؤال وسأجيبك باستخدام الذكاء الاصطناعي!'
                    )
                else:
                    # إظهار حالة الكتابة
                    bot.send_chat_action(chat_id=chat_id, action="typing")
                    
                    # الحصول على الرد من الذكاء الاصطناعي
                    response = get_ai_response(message_text)
                    
                    # إرسال الرد
                    bot.send_message(chat_id=chat_id, text=response)
            
            return 'OK'
            
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """تعيين الويبهوك"""
    try:
        webhook_url = f"https://{request.host}/webhook"
        result = bot.set_webhook(webhook_url)
        return f'''
        <h1>✅ تم تعيين الويبهوك بنجاح!</h1>
        <p><strong>الرابط:</strong> {webhook_url}</p>
        <p><strong>النتيجة:</strong> {result}</p>
        <p>الآن يمكنك استخدام البوت في تليجرام!</p>
        '''
    except Exception as e:
        return f'<h1>❌ خطأ في تعيين الويبهوك:</h1><p>{e}</p>'

@app.route('/test', methods=['GET'])
def test():
    """صفحة اختبار"""
    return '''
    <h1>🤖 اختبار البوت</h1>
    <ul>
        <li><a href="/">الصفحة الرئيسية</a></li>
        <li><a href="/setwebhook">تعيين الويبهوك</a></li>
        <li><a href="/getwebhook">معلومات الويبهوك</a></li>
    </ul>
    '''

@app.route('/getwebhook', methods=['GET'])
def get_webhook():
    """الحصول على معلومات الويبهوك"""
    try:
        webhook_info = bot.get_webhook_info()
        return f'''
        <h1>🔍 معلومات الويبهوك</h1>
        <p><strong>URL:</strong> {webhook_info.url or 'Not set'}</p>
        <p><strong>Pending Updates:</strong> {webhook_info.pending_update_count}</p>
        '''
    except Exception as e:
        return f'<h1>❌ خطأ:</h1><p>{e}</p>'

if __name__ == '__main__':
    print("🚀 بدء تشغيل البوت...")
    
    if TELEGRAM_TOKEN:
        print(f"✅ تم تحميل توكن البوت: {TELEGRAM_TOKEN[:10]}...")
    else:
        print("❌ لم يتم العثور على TELEGRAM_TOKEN")
    
    if DEEPSEEK_API_KEY:
        print("✅ تم تحميل مفتاح DeepSeek")
    else:
        print("❌ لم يتم العثور على DEEPSEEK_API_KEY")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
