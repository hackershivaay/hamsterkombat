import sys
import time
import requests
import argparse
import json
from colorama import *
from src.utils import load_tokens
from src.auth import get_token, authenticate
from src.exceptions import upgrade_passive, claim_daily, execute, boost, clicker_config
from src.exceptions import _sync, exhausted,load_all_info, execute_combo, claim_cipher, claim_key, faking_info
from src.promo import redeem_promo

from src.__init__ import (
    mrh, pth, hju, kng, htm, bru, reset,
    read_config, _number, countdown_timer, log,
    log_line, _banner, _clear, awak, load_fake_file
)

init(autoreset=True)
config = read_config()

def get_status(status):
    return Fore.GREEN + "ON" + Style.RESET_ALL if status else Fore.RED + "OFF" + Style.RESET_ALL

def save_setup(setup_name, setup_data):
    with open(f'./setup/{setup_name}.json', 'w') as file:
        json.dump(setup_data, file, indent=4)
    awak()
    print(hju + f" Setup saved on {kng}setup{pth}/{setup_name}.json")
    with open(f'./setup/{setup_name}.json', 'r') as file:
        setup_content = json.load(file)
        print(f"\n{json.dumps(setup_content, indent=4)}\n")
    print(hju + f" Quick start : {pth}python main.py {htm}--setup {pth}{setup_name}")
    input(f" Press Enter to continue...")

def load_setup_from_file(setup_file):
    with open(setup_file, 'r') as file:
        setup = json.load(file)
    return setup

def show_menu(auto_upgrade, taps_on, combo_upgrade, daily_cipher_on, claim_key_on, tasks_on, promo_on):
    _clear()
    _banner()
    menu = f"""
{kng} Choose Setup :{reset}
{kng}  1.{reset} Auto Buy Upgrade           : {get_status(auto_upgrade)}
{kng}  2.{reset} Auto Taps Taps             : {get_status(taps_on)}
{kng}  3.{reset} Auto Complete Combo        : {get_status(combo_upgrade)}
{kng}  4.{reset} Auto Complete Cipher       : {get_status(daily_cipher_on)}
{kng}  5.{reset} Auto Complete Mini Game    : {get_status(claim_key_on)}
{kng}  6.{reset} Auto Complete Tasks        : {get_status(tasks_on)}
{kng}  7.{reset} Auto Redeem Promo          : {get_status(promo_on)}
{mrh}    {pth} --------------------------------{reset}
{kng}  8.{reset} {kng}Save Setup{reset}
{kng}  9.{reset} {mrh}Reset Setup{reset}
{kng}  0.{reset} {hju}Start Bot {kng}(default){reset}
    """
    print(menu)
    choice = input(" Enter your choice (1/2/3/4/5/6/7/8): ")
    log_line()
    return choice

def show_upgrade_menu():
    _clear()
    _banner()
    config = read_config()
    MAXIMUM_PRICE = config.get('MAXIMUM_PRICE', 1000000)
    menu = f"""
{hju} Active Menu {kng}'Auto Buy Upgrade'{reset}
{htm} {'~' * 50}{reset}
{kng} Upgrade Method:{reset}
{kng} 1. {pth}highest profit{reset}
{kng} 2. {pth}lowest price{reset}
{kng} 3. {pth}price less than balance{reset}
{kng} 4. {pth}upgrade by payback {hju}[ enchanced ]{reset}
{kng} 5. {pth}back to {bru}main menu{reset}

{kng} [INFO]{reset} Current Max Price : {pth}{_number(MAXIMUM_PRICE)}{reset}
    """
    print(menu)
    choice = input(" Enter your choice (1/2/3/4): ")
    return choice

def run_bot(auto_upgrade, taps_on, combo_upgrade, daily_cipher_on, claim_key_on, tasks_on, promo_on, _method):
    cek_task_dict = {}
    DELAY_EACH_ACCOUNT = config.get('DELAY_EACH_ACCOUNT', 0)
    LOOP_COUNTDOWN = config.get('LOOP_COUNTDOWN', 0)
    awak()
    while True:
        try:
            init_data_list = load_tokens('tokens.txt')
            all_info_dict = load_all_info()  # Load all saved info at startup

            for idx, init_data in enumerate(init_data_list):
                account = f"account_{idx + 1}"
                token = get_token(init_data, account)
                if token:
                    try:
                        faking_infos = config.get('FAKE_IP/S_INFO', False)

                        if faking_infos:
                            fake_info = faking_info(token, account, use_fake=True, info_dict=all_info_dict)
                            if fake_info:
                                print(f"IP: {fake_info['ip']} | ISP: {fake_info['asn_org']} | Country: {fake_info['country_code']}")
                                print(f"City: {fake_info['city_name']} | Latitude: {fake_info['latitude']} | Longitude: {fake_info['longitude']}")
                            else:
                                print(mrh + f"Failed to generate fake {pth}IP/ISP {mrh}information", flush=True)
                        else:
                            print(kng + f"Faking information {mrh}not enabled{kng} for account {pth}{account}", flush=True)

                        log_line()
                        res = authenticate(token, account)
                        if res.status_code == 200:
                            user_data = res.json()
                            username = user_data.get('telegramUser', {}).get('username', 'Please set username first')
                            user_id = user_data.get('telegramUser', {}).get('id')
                            log(bru + f"Number : {pth}{account}")
                            log(kng + f"Login as {pth}{username}")
                            clicker_config(token)
                            clicker_data = _sync(token)
                            if 'clickerUser' in clicker_data:
                                user_info = clicker_data['clickerUser']
                                balance_coins = user_info.get('balanceCoins', 0)
                                earn_passive_per_hour = user_info.get('earnPassivePerHour', 0)
                                exchange_name = user_info.get('exchangeId', 'Unknown')
                                key_balance = user_info.get('balanceKeys', 0)

                                log(hju + f"Balance: {pth}{_number(balance_coins)}")
                                log(hju + f"Income: {pth}{_number(earn_passive_per_hour)}/h")
                                log(hju + f"Total Keys: {pth}{_number(key_balance)} KEY")
                                log(hju + f"CEO of {pth}{exchange_name} {hju}exchange")
                                claim_daily(token)
                            if taps_on:
                                while True:
                                    exhausted(token)
                                    if not boost(token):
                                        break
                            if tasks_on:
                                execute(token, cek_task_dict)
                            if daily_cipher_on:
                                claim_cipher(token)
                            if claim_key_on:
                                claim_key(token)
                            if combo_upgrade:
                                execute_combo(token)
                            if auto_upgrade:
                                upgrade_passive(token, _method)
                            if promo_on:
                                redeem_promo(token, user_id)
                        log_line()
                        countdown_timer(DELAY_EACH_ACCOUNT)
                    except requests.RequestException as e:
                        log(mrh + f"Request exception for token {pth}{token[:4]}****: {str(e)}")
                else:
                    log(mrh + f"Failed to login token {pth}{token[:4]}*********\n", flush=True)
            countdown_timer(LOOP_COUNTDOWN)
        except Exception as e:
            log(mrh + f"An error occurred in the main loop: {kng}{str(e)}")
            countdown_timer(10)

def main():
    parser = argparse.ArgumentParser(description="Run the bot with a specified setup.")
    parser.add_argument('--setup', type=str, help='Specify the setup file to load')
    args = parser.parse_args()

    if args.setup:
        setup_file = f'./setup/{args.setup}.json'
        setup_data = load_setup_from_file(setup_file)
        auto_upgrade = setup_data.get('auto_upgrade', False)
        taps_on = setup_data.get('taps_on', False)
        combo_upgrade = setup_data.get('combo_upgrade', False)
        daily_cipher_on = setup_data.get('daily_cipher_on', False)
        claim_key_on = setup_data.get('claim_key_on', False)
        tasks_on = setup_data.get('tasks_on', False)
        promo_on = setup_data.get('promo_on', False)
        _method = setup_data.get('_method', None)
        run_bot(auto_upgrade, taps_on, combo_upgrade, daily_cipher_on, claim_key_on, tasks_on, promo_on, _method)
    else:
        auto_upgrade = False
        taps_on = False
        combo_upgrade = False
        daily_cipher_on = False
        claim_key_on = False
        tasks_on = False
        promo_on = False
        _method = None

        while True:
            try:
                choice = show_menu(auto_upgrade, taps_on, combo_upgrade, daily_cipher_on, claim_key_on, tasks_on, promo_on)
                if choice == '1':
                    auto_upgrade = not auto_upgrade
                    if auto_upgrade:
                        _method = show_upgrade_menu()
                        if _method not in ['1', '2', '3', '4']:
                            auto_upgrade = False
                elif choice == '2':
                    taps_on = not taps_on
                elif choice == '3':
                    combo_upgrade = not combo_upgrade
                elif choice == '4':
                    daily_cipher_on = not daily_cipher_on
                elif choice == '5':
                    claim_key_on = not claim_key_on
                elif choice == '6':
                    tasks_on = not tasks_on
                elif choice == '7':
                    promo_on = not promo_on
                elif choice == '8':
                    setup_name = input(" Enter setup name (without space): ")
                    setup_data = {
                        'auto_upgrade': auto_upgrade,
                        '_method': _method,
                        'taps_on': taps_on,
                        'combo_upgrade': combo_upgrade,
                        'daily_cipher_on': daily_cipher_on,
                        'claim_key_on': claim_key_on,
                        'tasks_on': tasks_on,
                        'promo_on': promo_on,
                    }
                    save_setup(setup_name, setup_data)
                elif choice == '0':
                    run_bot(auto_upgrade, taps_on, combo_upgrade, daily_cipher_on, claim_key_on, tasks_on, promo_on, _method)
                elif choice == '9':
                    break
                else:
                    log(mrh + f"Invalid choice. Please try again.")
                time.sleep(1)
            except Exception as e:
                log(mrh + f"An error occurred in the main loop: {kng}{str(e)}")
                countdown_timer(10)

if __name__ == '__main__':
    main()
