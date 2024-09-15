from telegram.ext import Updater, CommandHandler, MessageHandler
import os
import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)

TOKEN = 'YOUR_BOT_TOKEN'

def start_program(update, context):
    os.system('python main.py --setup mysetup')

def stop_program(update, context):
    os.system('pkill your_program')

def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start_program))
    dp.add_handler(CommandHandler('stop', stop_program))

    updater.start_polling()
    updater.idle()


