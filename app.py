import os
import requests
from flask import Flask, request
import json

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

def send_telegram_message(chat_id, text):
    """إرسال رسالة عبر تليجرام API مباشرة"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Telegram API error: {e}")
        return None

def send_typing_action(chat_id):
    """إظهار حالة الكتابة"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    data = {
        "chat_id": chat_id,
        "action": "typing"
    }
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

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
                    send_telegram_message(
                        chat_id, 
                        '🌐 مرحباً! أنا بوت DeepSeek. اسألني أي شيء!'
                    )
                elif message_text == '/help':
                    send_telegram_message(
                        chat_id, 
                        '💡 فقط أرسل لي أي سؤال وسأجيبك باستخدام الذكاء الاصطناعي!'
                    )
                else:
                    # إظهار حالة الكتابة
                    send_typing_action(chat_id)
                    
                    # الحصول على الرد من الذكاء الاصطناعي
                    response = get_ai_response(message_text)
                    
                    # إرسال الرد
                    send_telegram_message(chat_id, response)
            
            return 'OK'
            
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """تعيين الويبهوك"""
    try:
        webhook_url = f"https://{request.host}/webhook"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        
        response = requests.post(url, json=data)
        result = response.json()
        
        return f'''
        <h1>✅ تم تعيين الويبهوك بنجاح!</h1>
        <p><strong>الرابط:</strong> {webhook_url}</p>
        <p><strong>النتيجة:</strong> {result}</p>
        '''
    except Exception as e:
        return f'<h1>❌ خطأ في تعيين الويبهوك:</h1><p>{e}</p>'

if __name__ == '__main__':
    print("🚀 بدء تشغيل البوت...")
    
    if TELEGRAM_TOKEN:
        print(f"✅ تم تحميل توكن البوت")
    else:
        print("❌ لم يتم العثور على TELEGRAM_TOKEN")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
