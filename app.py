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
            "messages": [
                {
                    "role": "user",
                    "content": message_text
                }
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        print(f"🔗 محاولة الاتصال بـ DeepSeek API...")
        print(f"📝 الرسالة: {message_text}")
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        print(f"📊 حالة الرد: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ نجح الاتصال: {result}")
            return result["choices"][0]["message"]["content"]
        else:
            error_msg = f"❌ خطأ في API: {response.status_code} - {response.text}"
            print(error_msg)
            return error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "⏰ انتهت مهلة الاتصال بـ DeepSeek API"
        print(error_msg)
        return error_msg
    except requests.exceptions.ConnectionError:
        error_msg = "🌐 خطأ في الاتصال بالإنترنت"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ خطأ غير متوقع: {str(e)}"
        print(error_msg)
        return error_msg

@app.route('/')
def home():
    return '''
    <h1>🤖 بوت DeepSeek يعمل!</h1>
    <p>الحالة:</p>
    <ul>
        <li>✅ تليجرام: {}</li>
        <li>✅ DeepSeek: {}</li>
    </ul>
    <p><a href="/setwebhook">تعيين الويبهوك</a></p>
    '''.format(
        "متصل" if TELEGRAM_TOKEN else "غير متصل",
        "متصل" if DEEPSEEK_API_KEY else "غير متصل"
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print("📩 بيانات مستلمة:", json.dumps(data, ensure_ascii=False))
            
            if 'message' in data and 'text' in data['message']:
                chat_id = data['message']['chat']['id']
                message_text = data['message']['text']
                
                print(f"💬 رسالة من {chat_id}: {message_text}")
                
                if message_text == '/start':
                    send_telegram_message(
                        chat_id, 
                        '🌐 مرحباً! أنا بوت DeepSeek. اسألني أي شيء!\n\n'
                        '💡 مثال: "ما هو الذكاء الاصطناعي؟"'
                    )
                elif message_text == '/help':
                    send_telegram_message(
                        chat_id, 
                        '🆘 المساعدة:\n'
                        '/start - بدء التشغيل\n'
                        '/help - عرض هذه الرسالة\n'
                        '💬 أرسل أي سؤال للحصول على إجابة من DeepSeek'
                    )
                elif message_text == '/test':
                    send_telegram_message(chat_id, '✅ البوت يعمل بشكل صحيح!')
                else:
                    # إظهار حالة الكتابة
                    send_typing_action(chat_id)
                    
                    # الحصول على الرد من الذكاء الاصطناعي
                    response = get_ai_response(message_text)
                    
                    # إرسال الرد
                    send_telegram_message(chat_id, response)
            
            return 'OK'
            
        except Exception as e:
            print(f"❌ خطأ في الويبهوك: {e}")
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
        <h1>✅ تم تعيين الويبهوك!</h1>
        <p><strong>الرابط:</strong> {webhook_url}</p>
        <p><strong>النتيجة:</strong> {result}</p>
        <p><strong>توكن البوت:</strong> {TELEGRAM_TOKEN[:10]}...</p>
        <p><strong>مفتاح DeepSeek:</strong> {DEEPSEEK_API_KEY[:10] if DEEPSEEK_API_KEY else 'غير موجود'}...</p>
        '''
    except Exception as e:
        return f'<h1>❌ خطأ في تعيين الويبهوك:</h1><p>{e}</p>'

@app.route('/debug', methods=['GET'])
def debug():
    """صفحة تصحيح الأخطاء"""
    test_message = "مرحبا، هل تعمل؟"
    
    try:
        # اختبار DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": test_message}],
            "max_tokens": 100
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        deepseek_status = f"✅ يعمل (كود: {response.status_code})" if response.status_code == 200 else f"❌ خطأ (كود: {response.status_code})"
        
    except Exception as e:
        deepseek_status = f"❌ خطأ: {str(e)}"
    
    return f'''
    <h1>🐛 تصحيح الأخطاء</h1>
    <p><strong>توكن البوت:</strong> {TELEGRAM_TOKEN[:10] if TELEGRAM_TOKEN else 'غير موجود'}...</p>
    <p><strong>مفتاح DeepSeek:</strong> {DEEPSEEK_API_KEY[:10] if DEEPSEEK_API_KEY else 'غير موجود'}...</p>
    <p><strong>حالة DeepSeek API:</strong> {deepseek_status}</p>
    <p><a href="/setwebhook">تعيين الويبهوك</a></p>
    '''

if __name__ == '__main__':
    print("🚀 بدء تشغيل البوت...")
    print(f"🔑 توكن البوت: {'موجود' if TELEGRAM_TOKEN else 'غير موجود'}")
    print(f"🔑 مفتاح DeepSeek: {'موجود' if DEEPSEEK_API_KEY else 'غير موجود'}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
