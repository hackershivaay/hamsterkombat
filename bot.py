from telegram.ext import Updater, CommandHandler, MessageHandler
import os

TOKEN = 'YOUR_BOT_TOKEN'

def start_program(update, context):
    os.system('python your_program.py')

def stop_program(update, context):
    os.system('pkill your_program')

def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start_program))
    dp.add_handler(CommandHandler('stop', stop_program))

    updater.start_polling()
    updater.idle()

if name == 'main':
    main()
