import sys
import time
import locale
import requests
from colorama import *
from src.utils import load_tokens
from src.auth import get_token, authenticate
from src.exceptions import upgrade_passive, claim_daily, execute, boost, clicker_config
from src.exceptions import _sync, exhausted, execute_combo, claim_cipher

from src.__init__ import (
    mrh, pth, hju, kng, htm, bru,  reset, 
    read_config, _number, countdown_timer, log, 
    log_line, _banner, _clear
    )

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
init(autoreset=True)
config = read_config()

def get_status(status):
    return Fore.GREEN + "ON" + Style.RESET_ALL if status else Fore.RED + "OFF" + Style.RESET_ALL

def show_menu(auto_upgrade, combo_upgrade, daily_cipher_on, tasks_on):
    _clear()
    _banner()
    menu = f"""
{kng} Configurations :{reset}
{kng}  1.{reset} Auto Buy Upgrade           : {get_status(auto_upgrade)}
{kng}  2.{reset} Auto Complete Combo        : {get_status(combo_upgrade)}
{kng}  3.{reset} Auto Complete Cipher       : {get_status(daily_cipher_on)}
{kng}  4.{reset} Auto Complete Tasks        : {get_status(tasks_on)}
{kng}  5.{reset} {hju}Start Bot {kng}(default){reset}
{kng}  6.{reset} {mrh}Exit{reset}

{kng} [INFO]{reset} By default will do {hju}taps, boost & streak{reset}
    """
    print(menu)
    choice = input(" Enter your choice (1/2/3/4/5/6): ")
    log_line()
    return choice

def show_upgrade_menu():
    _clear()
    _banner()
    config = read_config()
    max_price = config.get('max_price', 10000000)
    menu = f"""
{hju} Active Menu {kng}'Auto Buy Upgrade'{reset}
{htm} {'~' * 50}{reset}
{kng} Upgrade Method:{reset}
{kng} 1. {pth}highest profit{reset}
{kng} 2. {pth}lowest price{reset}
{kng} 3. {pth}price less than balance{reset}
{kng} 4. {pth}max profit/price ratio{reset}
{kng} 5. {pth}back to {bru}main menu{reset}

{kng} [INFO]{reset} you set Max Price to : {pth}{_number(max_price)}{reset}
    """
    print(menu)
    choice = input(" Enter your choice (1/2/3/4/5): ")
    return choice

def main():
    auto_upgrade = False
    combo_upgrade = False
    daily_cipher_on = False
    tasks_on = False

    cek_task_dict = {}
    countPerAccount = config.get('DelayPerAccount', 3)
    loop = config.get('loop', 3600)

    while True:
        try:
            choice = show_menu(auto_upgrade, combo_upgrade, daily_cipher_on, tasks_on)
            if choice == '1':
                auto_upgrade = not auto_upgrade
                if auto_upgrade:
                    _method = show_upgrade_menu()
                    if _method not in ['1', '2', '3', '4']:
                        auto_upgrade = False
            elif choice == '2':
                combo_upgrade = not combo_upgrade
            elif choice == '3':
                daily_cipher_on = not daily_cipher_on
            elif choice == '4':
                tasks_on = not tasks_on
            elif choice == '5':
                while True:
                    init_data_list = load_tokens('tokens.txt')
                    
                    for init_data in init_data_list:
                        token = get_token(init_data)
                        if token:
                            try:
                                res = authenticate(token)
                                if res.status_code == 200:
                                    user_data = res.json()
                                    username = user_data.get('telegramUser', {}).get('username', 'Please set username first')
                                    log(kng + f"Login as {pth}{username}")    
                                    clicker_config(token)
                                    clicker_data = _sync(token)
                                    if 'clickerUser' in clicker_data:
                                        user_info = clicker_data['clickerUser']
                                        balance_coins = user_info['balanceCoins']
                                        earn_passive_per_hour = user_info['earnPassivePerHour']
                                        exchange_name = user_info['exchangeId']
                                        
                                        log(hju + f"Balance: {pth}{_number(balance_coins)}")
                                        log(hju + f"Income: {pth}{_number(earn_passive_per_hour)}/h")
                                        log(hju + f"CEO of {pth}{exchange_name} {hju}exchange")
                                    claim_daily(token)
                                    while True:
                                        exhausted(token)
                                        if not boost(token):
                                            break
                                    if tasks_on:
                                        execute(token, cek_task_dict)
                                    if daily_cipher_on:
                                        claim_cipher(token)
                                    if combo_upgrade:
                                        execute_combo(token)
                                    if auto_upgrade:
                                        upgrade_passive(token, _method)  
                                log_line()
                                countdown_timer(countPerAccount)
                            except requests.RequestException as e:
                                log(mrh + f"Request exception for token {pth}{token[:4]}****: {str(e)}")
                        else:
                            log(mrh + f"Failed to login token {pth}{token[:4]}*********\n", flush=True)
                    countdown_timer(loop)
            elif choice == '6':
                log(mrh + f"Successfully logged out of the bot\n")
                sys.exit()
            else:
                log("Invalid choice. Please try again.")
            time.sleep(1)
        except Exception as e:
            log(mrh + f"An error occurred in the main loop: {kng}{str(e)}")
            countdown_timer(10)

if __name__ == '__main__':
    main()
