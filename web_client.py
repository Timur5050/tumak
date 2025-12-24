import socket
import threading
import hashlib
from flask import Flask, render_template_string, request, redirect, url_for, session
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = 'tumak_chat_fix_final_v3'

HOST = '127.0.0.1'
PORT = 5555

active_sessions = {}

try:
    with open("secret.key", "rb") as k_file:
        cipher = Fernet(k_file.read())
except:
    print("Error: secret.key not found.")
    exit()

def get_color(name):
    colors = ['#e74c3c', '#d35400', '#f39c12', '#16a085', '#27ae60', '#2980b9', '#8e44ad', '#2c3e50']
    return colors[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(colors)]

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Вхід Tumak</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #333; }
        .box { background: white; padding: 40px; border-radius: 10px; width: 300px; text-align: center; }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; }
        button { width: 100%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .error { color: red; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Вхід у Чат</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="post">
            <input type="text" name="username" placeholder="Логін" required autocomplete="off">
            <input type="password" name="password" placeholder="Пароль" required>
            <button>Увійти</button>
        </form>
    </div>
</body>
</html>
"""

CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Чат: {{ username }}</title>
    <style>
        body { font-family: sans-serif; background: #e9ecef; margin: 0; padding: 20px; height: 90vh; display: flex; justify-content: center; }
        .container { width: 900px; display: flex; gap: 20px; height: 100%; }
        .chat-wrap { flex: 3; background: white; border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .header { background: #007bff; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        #box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; background: #f8f9fa; }
        .row { display: flex; flex-direction: column; max-width: 75%; }
        .bubble { padding: 10px 15px; border-radius: 15px; word-wrap: break-word; font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .name { font-size: 12px; font-weight: bold; margin-bottom: 3px; }
        .mine { align-self: flex-end; align-items: flex-end; }
        .mine .bubble { background: #007bff; color: white; border-bottom-right-radius: 2px; }
        .mine .name { color: #007bff; margin-right: 5px; }
        .other { align-self: flex-start; align-items: flex-start; }
        .other .bubble { background: white; color: #333; border: 1px solid #ddd; border-bottom-left-radius: 2px; }
        .other .name { margin-left: 5px; }
        .system { align-self: center; align-items: center; width: 100%; }
        .system .bubble { background: #fff3cd; color: #856404; border-radius: 20px; font-size: 13px; }
        .input-area { padding: 15px; background: white; display: flex; gap: 10px; border-top: 1px solid #eee; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; padding-left: 15px; outline: none; }
        .input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 20px; cursor: pointer; }
        .sidebar { flex: 1; display: flex; flex-direction: column; gap: 15px; }
        .panel { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .panel h4 { margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 5px; }
        .panel input { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; box-sizing: border-box; }
        .btn-green { width: 100%; padding: 8px; background: #28a745; color: white; border: none; cursor: pointer; }
        .btn-red { width: 100%; padding: 8px; background: #dc3545; color: white; border: none; cursor: pointer; }
    </style>
    <script>
        const currentUser = "{{ username }}";
        function loadMessages() {
            fetch('/updates?u=' + encodeURIComponent(currentUser))
                .then(r => r.text())
                .then(html => {
                    if (html.trim()) {
                        const box = document.getElementById('box');
                        const isBottom = box.scrollHeight - box.clientHeight <= box.scrollTop + 100;
                        box.innerHTML = html;
                        if (isBottom) box.scrollTop = box.scrollHeight;
                    }
                });
        }
        setInterval(loadMessages, 2000);
        window.onload = function() { loadMessages(); document.getElementById('msg-in').focus(); }
    </script>
</head>
<body>
    <div class="container">
        <div class="chat-wrap">
            <div class="header">
                <h3>{{ username }}</h3>
                <a href="/logout" style="color:white;">Вийти</a>
            </div>
            <div id="box"></div>
            <form class="input-area" action="/send" method="post" onsubmit="setTimeout(loadMessages, 300)">
                <input type="hidden" name="username_fix" value="{{ username }}">
                <input id="msg-in" type="text" name="message" placeholder="Написати..." autocomplete="off">
                <button>Send</button>
            </form>
        </div>
        <div class="sidebar">
            <div class="panel">
                <h4>+ Створити</h4>
                <form action="/admin/register" method="post">
                    <input type="hidden" name="username_fix" value="{{ username }}">
                    <input type="text" name="new_login" placeholder="Логін" required>
                    <input type="text" name="new_pass" placeholder="Пароль" required>
                    <button class="btn-green">Додати</button>
                </form>
            </div>
            <div class="panel">
                <h4>- Видалити</h4>
                <form action="/admin/kick" method="post">
                    <input type="hidden" name="username_fix" value="{{ username }}">
                    <input type="text" name="target" placeholder="Нікнейм" required>
                    <button class="btn-red">Kick</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

MSGS_TEMPLATE = """
{% for m in messages %}
    {% if m.type == 'system' %}
        <div class="row system"><div class="bubble">{{ m.text }}</div></div>
    {% elif m.type == 'mine' %}
        <div class="row mine">
            <div class="name">{{ m.sender }}</div>
            <div class="bubble">{{ m.text }}</div>
        </div>
    {% else %}
        <div class="row other">
            <div class="name" style="color: {{ m.color }}">{{ m.sender }}</div>
            <div class="bubble">{{ m.text }}</div>
        </div>
    {% endif %}
{% endfor %}
"""

def listen_socket(user, sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data: break
            text = cipher.decrypt(data).decode()
            msg = {'type': 'system', 'text': text}
            if text.startswith("System:") or "Welcome" in text or "ERROR" in text:
                pass
            elif ":" in text:
                sender, content = text.split(":", 1)
                msg['type'] = 'other'
                msg['sender'] = sender.strip()
                msg['text'] = content.strip()
                msg['color'] = get_color(sender.strip())
            if user in active_sessions:
                active_sessions[user]['messages'].append(msg)
        except: break

@app.route('/updates')
def get_updates():
    u = request.args.get('u') or session.get('user')
    if u and u in active_sessions:
        return render_template_string(MSGS_TEMPLATE, messages=active_sessions[u]['messages'])
    return ""

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u in active_sessions:
            try: active_sessions[u]['socket'].close()
            except: pass
            del active_sessions[u]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((HOST, PORT))
            cipher.decrypt(s.recv(1024))
            s.send(cipher.encrypt(u.encode()))
            cipher.decrypt(s.recv(1024))
            s.send(cipher.encrypt(p.encode()))
            if "SUCCESS" in cipher.decrypt(s.recv(1024)).decode():
                session['user'] = u
                active_sessions[u] = {'socket': s, 'messages': []}
                threading.Thread(target=listen_socket, args=(u, s), daemon=True).start()
                return redirect(url_for('chat', username=u))
            else:
                return render_template_string(LOGIN_HTML, error="Невірний пароль або логін")
        except:
            return render_template_string(LOGIN_HTML, error="Сервер вимкнено")
    return render_template_string(LOGIN_HTML)

@app.route('/chat')
def chat():
    u = request.args.get('username') or session.get('user')
    if not u or u not in active_sessions: return redirect('/')
    return render_template_string(CHAT_HTML, username=u)

@app.route('/send', methods=['POST'])
def send():
    u = request.form.get('username_fix')
    msg = request.form.get('message')
    if u and u in active_sessions and msg:
        try:
            active_sessions[u]['socket'].send(cipher.encrypt(msg.encode()))
            active_sessions[u]['messages'].append({'type': 'mine', 'sender': u, 'text': msg})
        except: pass
    return '', 204

@app.route('/admin/register', methods=['POST'])
def reg():
    u = request.form.get('username_fix')
    if u in active_sessions:
        cmd = f"/register {request.form.get('new_login')} {request.form.get('new_pass')}"
        active_sessions[u]['socket'].send(cipher.encrypt(cmd.encode()))
    return redirect(url_for('chat', username=u))

@app.route('/admin/kick', methods=['POST'])
def kick():
    u = request.form.get('username_fix')
    if u in active_sessions:
        active_sessions[u]['socket'].send(cipher.encrypt(f"/kick {request.form.get('target')}".encode()))
    return redirect(url_for('chat', username=u))

@app.route('/logout')
def logout():
    u = session.get('user')
    if u in active_sessions:
        try: active_sessions[u]['socket'].close()
        except: pass
        del active_sessions[u]
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)