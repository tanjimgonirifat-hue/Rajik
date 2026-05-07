import telebot
from flask import Flask, render_template_string, request, redirect
import threading
import json
import os
import requests

# Render-এর Environment Variables থেকে টোকেন নিবে
# Render ড্যাশবোর্ডে গিয়ে BOT_TOKEN নামে ভ্যারিয়েবল সেট করতে ভুলবেন না
API_TOKEN = os.getenv('BOT_TOKEN') 
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# আপনার গুগল অ্যাপস স্ক্রিপ্ট লিঙ্ক (যা আপনি আগে দিয়েছিলেন)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyODVRgX4trvBhvut8HQ7Rr9VT6DsFJevS9v9QoGEcX4ySgiHXbzOFWTpA6PSs3q19kQg/exec"

CONFIG_FILE = 'bot_settings.json'

# ডিফল্ট সেটিংস
default_config = {
    "btn1_name": "🧾 কাজ শুরু", 
    "msg1_reply": "🟡 নিচের ক্যাটাগরি থেকে আপনার কাজ বেছে নিন 👇",
    "btn2_name": "💰 প্রোফাইল", 
    "msg2_reply": "👤 আপনার প্রোফাইল ডিটেইলস এখানে শো করবে।",
    "btn3_name": "💳 উইথড্র", 
    "msg3_reply": "পেমেন্ট মেথড সিলেক্ট করুন:",
    "btn4_name": "📞 সাপোর্ট", 
    "msg4_reply": "যেকোনো সমস্যায় যোগাযোগ করুন: @TanjimZc1234",
    "task_cali": "╔════════════════════╗\n      ✨ NEW TASK ✨\n╚════════════════════╝\n🔗 লিঙ্ক: {link}\n💰 পেমেন্ট: $0.03\n━━━━━━━━━━━━━━━━━━━━━━",
    "success_msg": "✅ আপনার রিপোর্টটি সফলভাবে গুগল শিটে সেভ হয়েছে।"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default_config

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_to_google_sheet(row_data):
    try:
        response = requests.post(WEB_APP_URL, json={"row": row_data}, timeout=15)
        return response.status_code == 200
    except:
        return False

# অ্যাডমিন প্যানেল UI
@app.route('/')
def index():
    config = load_config()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tanjim Master Control</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: white; padding: 20px; }
            .card { background: #161b22; padding: 15px; margin-bottom: 15px; border-radius: 10px; border: 1px solid #30363d; }
            input, textarea { width: 100%; padding: 10px; margin-top: 5px; background: #010409; color: #58a6ff; border: 1px solid #333; border-radius: 5px; box-sizing: border-box; }
            textarea { height: 100px; font-family: monospace; }
            button { background: #238636; color: white; padding: 15px; width: 100%; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; }
            label { font-weight: bold; color: #8b949e; }
        </style>
    </head>
    <body>
        <h2>🛠️ Tanjim Master Controller</h2>
        <form action="/update" method="POST">
            {% for key, value in config.items() %}
            <div class="card">
                <label>{{ key.replace('_', ' ').upper() }}</label><br>
                {% if 'msg' in key or 'cali' in key %}
                <textarea name="{{ key }}">{{ value }}</textarea>
                {% else %}
                <input name="{{ key }}" value="{{ value }}">
                {% endif %}
            </div>
            {% endfor %}
            <button type="submit">💾 সব সেটিংস লাইভ আপডেট করুন</button>
        </form>
    </body>
    </html>
    ''', config=config)

@app.route('/update', methods=['POST'])
def update():
    save_config(request.form.to_dict())
    return redirect('/')

# টেলিগ্রাম বট হ্যান্ডলার
@bot.message_handler(commands=['start'])
def start(message):
    c = load_config()
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(c['btn1_name'], c['btn2_name'], c['btn3_name'], c['btn4_name'])
    bot.send_message(message.chat.id, "🤖 বট সচল আছে। নিচের মেনু ব্যবহার করুন।", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    c = load_config()
    if message.text == c['btn1_name']:
        design = c['task_cali'].format(link="https://instagram.com/tanjim")
        bot.send_message(message.chat.id, design)
        bot.send_message(message.chat.id, "কাজ শেষ করে আপনার ইউজারনেমটি লিখুন:")
        bot.register_next_step_handler(message, process_to_sheet)
    
    elif message.text == c['btn2_name']:
        bot.send_message(message.chat.id, c['msg2_reply'])
    
    elif message.text == c['btn3_name']:
        bot.send_message(message.chat.id, c['msg3_reply'])
        
    elif message.text == c['btn4_name']:
        bot.send_message(message.chat.id, c['msg4_reply'])

def process_to_sheet(message):
    c = load_config()
    # শিটে ডাটা পাঠানো: আইডি, নাম, ইউজারের টেক্সট
    row = [message.from_user.id, message.from_user.first_name, message.text]
    if send_to_google_sheet(row):
        bot.send_message(message.chat.id, c['success_msg'])
    else:
        bot.send_message(message.chat.id, "❌ গুগল শিটে ডাটা সেভ করা যায়নি।")

# মেইন রান ফাংশন
def run_flask():
    # Render-এর জন্য পোর্ট সেট করা (এই লাইনটি Status 2 এরর সমাধান করবে)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # ওয়েবসাইট এবং বট একসাথে চালানোর জন্য থ্রেডিং
    t = threading.Thread(target=run_flask)
    t.start()
    print("✅ System Online...")
    bot.polling(none_stop=True)

