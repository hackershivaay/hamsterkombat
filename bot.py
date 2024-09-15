from telegram.ext import Updater, CommandHandler, MessageHandler
import os
import socket

# Define the port you want to listen on
PORT = 5000

# Create a socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('', PORT))
    # Rest of your application logic here

TOKEN = '7517151300:AAH5_Sz4LGsI-Wz3NS7xt-xvfb-PqKHhB8M'

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


