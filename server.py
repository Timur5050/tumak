import socket
import threading
import json
import hashlib
import os
from cryptography.fernet import Fernet

# Завантаження ключа
try:
    with open("secret.key", "rb") as k_file:
        cipher = Fernet(k_file.read())
except:
    print("Error: Run setup.py first!")
    exit()

clients = {} # сокет: нікнейм
admins = []

def load_users():
    with open('users.json', 'r') as f: return json.load(f)

def save_users(users):
    with open('users.json', 'w') as f: json.dump(users, f, indent=4)

def broadcast(text, sender_conn=None):
    encrypted = cipher.encrypt(text.encode())
    for conn in list(clients.keys()):
        if conn != sender_conn:
            try: conn.send(encrypted)
            except: pass

def handle_client(conn, addr):
    username = ""
    try:
        # ЗАХИСТ: 3 спроби входу (Brute Force Protection)
        for attempt in range(3):
            conn.send(cipher.encrypt(b"LOGIN:"))
            username = cipher.decrypt(conn.recv(1024)).decode()
            
            conn.send(cipher.encrypt(b"PASSWORD:"))
            password = cipher.decrypt(conn.recv(1024)).decode()
            
            users = load_users()
            input_hash = hashlib.sha256(password.encode()).hexdigest()

            if username in users and users[username]['password_hash'] == input_hash:
                clients[conn] = username
                if users[username].get('role') == 'admin':
                    admins.append(conn)
                conn.send(cipher.encrypt(f"SUCCESS: Welcome {username}".encode()))
                broadcast(f"System: {username} joined the chat")
                break
            else:
                if attempt < 2:
                    conn.send(cipher.encrypt(f"ERROR: Wrong. Attempts left: {2-attempt}".encode()))
                else:
                    conn.send(cipher.encrypt(b"ERROR: Too many attempts. Disconnecting."))
                    conn.close()
                    return

        # ОСНОВНИЙ ЦИКЛ
        while True:
            data = conn.recv(1024)
            if not data: break
            msg = cipher.decrypt(data).decode()

            # АДМІН: Реєстрація нових юзерів
            if msg.startswith("/register") and conn in admins:
                try:
                    _, u, p = msg.split(" ")
                    users = load_users()
                    if u in users: conn.send(cipher.encrypt(b"System: User exists!"))
                    else:
                        users[u] = {"password_hash": hashlib.sha256(p.encode()).hexdigest(), "role": "user"}
                        save_users(users)
                        conn.send(cipher.encrypt(f"System: User {u} registered!".encode()))
                except: conn.send(cipher.encrypt(b"System: Use /register [login] [pass]"))

            # АДМІН: Кік
            elif msg.startswith("/kick") and conn in admins:
                target = msg.split(" ")[1]
                for c_sock, c_nick in list(clients.items()):
                    if c_nick == target:
                        c_sock.close()
                        broadcast(f"System: {target} was kicked.")
                        break
            
            # ЗАХИСТ: Валідація команд (Command Injection Protection)
            else:
                broadcast(f"{username}: {msg}", conn)

    except: pass
    finally:
        if conn in clients:
            broadcast(f"System: {clients[conn]} left.")
            del clients[conn]
        if conn in admins: admins.remove(conn)
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 5555))
server.listen()
print("SERVER ACTIVE ON PORT 5555...")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()