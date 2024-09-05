import os
import json
import random
import time
import base64
from random import randint
from datetime import datetime
import requests
from colorama import *
from src.utils import get_headers

from src.__init__ import (
    read_config, 
    mrh, pth, hju, kng, bru, reset, htm, log, log_line,
    _number, countdown_timer, load_fake_file
    )

config = read_config()

def clicker_config(token):
    url = 'https://api.hamsterkombatgame.io/clicker/config'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        return {}
    
def _sync(token):
    url = 'https://api.hamsterkombatgame.io/clicker/sync'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        return {}

def _list(token):
    url = 'https://api.hamsterkombatgame.io/clicker/list-tasks'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    return res

def _check(token, task_id):
    url = 'https://api.hamsterkombatgame.io/clicker/check-task'
    headers = get_headers(token)
    headers['accept'] = 'application/json'
    headers['content-type'] = 'application/json'
    data = json.dumps({"taskId": task_id})
    res = requests.post(url, headers=headers, data=data)
    return res

def tap(token, tap_count, available_taps):
    url = 'https://api.hamsterkombatgame.io/clicker/tap'
    headers = get_headers(token)
    headers['accept'] = 'application/json'
    headers['content-type'] = 'application/json'
    data = json.dumps({"count": tap_count, "availableTaps": available_taps, "timestamp": int(time.time())})
    res = requests.post(url, headers=headers, data=data)
    return res

def exhausted(token):
    while True:
        clicker_data = _sync(token)

        if 'clickerUser' in clicker_data:
            user_info = clicker_data['clickerUser']
            available_taps = user_info['availableTaps']
            max_taps = user_info['maxTaps']
            TAP_DELAY = config.get('TAP_DELAY', False)
            MIN_TAP_DELAY = config.get('MIN_TAP_DELAY', 0)
            MAX_TAP_DELAY = config.get('MAX_TAP_DELAY', max_taps)
            MINIMUM_TAP = config.get('MINIMUM_TAP',0)
            MAXIMUM_TAP = config.get('MAXIMUM_TAP',1)
            log(hju + f"Total {pth}{available_taps:>2,} {hju}Energy available\r")
            while available_taps > 100:
                tap_count = randint(MINIMUM_TAP, MAXIMUM_TAP)
                
                if tap_count > available_taps:
                    tap_count = available_taps

                res = tap(token, tap_count, available_taps) 

                if res.status_code == 200:
                    available_taps -= tap_count
                    log(hju + f"Tapping {kng}{tap_count:>4,}, {bru}remaining {pth}{available_taps:<4,}", flush=True)

                    if TAP_DELAY:
                        countdown_timer(randint(MIN_TAP_DELAY, MAX_TAP_DELAY))
                    else:
                        time.sleep(0.1)
                else:
                    log(mrh + "Failed to make a tap\r")
                    break
            break
        else:
            log("Error Unable to retrieve clicker data\r")
            break

def claim_daily(token):
    url = 'https://api.hamsterkombatgame.io/clicker/check-task'
    headers = get_headers(token)
    headers['accept'] = 'application/json'
    headers['content-type'] = 'application/json'
    data = json.dumps({"taskId": "streak_days_special"})
    res = requests.post(url, headers=headers, data=data)
    data = res.json()
    
    if res.status_code == 200:
        if data['task']['completedAt']:
            log(f"{hju}Daily streaks {pth}already claimed")
        else:
            log(f"{hju}Daily streaks {pth}claimed successfully")
    else:
        # Gabungkan pesan dan error dalam satu string
        error_message = data.get('error', 'Unknown error')
        log(f"{mrh}Daily streaks: {error_message}")
        
    return res

def execute(token, cek_task_dict):
    if token not in cek_task_dict:
        cek_task_dict[token] = False
    if not cek_task_dict[token]:
        res = _list(token)
        cek_task_dict[token] = True
        if res.status_code == 200:
            tasks = res.json()['tasks']
            all_completed = all(task['isCompleted'] or task['id'] == 'invite_friends' for task in tasks)
            if all_completed:
                log(f"{kng}All task has been claimed successfully\r", flush=True)
            else:
                for task in tasks:
                    if not task['isCompleted']:
                        res = _check(token, task['id'])
                        if res.status_code == 200 and res.json()['task']['isCompleted']:
                            log(f"{hju}Tasks {pth}{task['id']}\r", flush=True)
                            log(f"{hju}Succesfully Claimed this Taks Rewards\r", flush=True)
                        else:
                            log(f"{hju}Tasks {mrh}failed {pth}{task['id']}\r", flush=True)
        else:
            log(f"{hju}Tasks {mrh}failed to get list {pth}{res.status_code}\r", flush=True)

def apply_boost(token, boost_type):
    url = 'https://api.hamsterkombatgame.io/clicker/buy-boost'
    headers = get_headers(token)
    headers['accept'] = 'application/json'
    headers['content-type'] = 'application/json'
    data = json.dumps({"boostId": boost_type, "timestamp": int(time.time())})
    res = requests.post(url, headers=headers, data=data)
    return res

def boost(token):
    boost_type = "BoostFullAvailableTaps"
    res = apply_boost(token, boost_type)
    if res.status_code == 200:
        res_data = res.json()
        if 'cooldownSeconds' in res_data:
            return False
        else:
            log(f"{hju}Boost {kng}successfully applied!")
            time.sleep(1)
            return True
    else:
        log(f"{kng}boost on cooldown or unavailable")
        time.sleep(1)
        return False

def upgrade_passive(token, _method):
    MAXIMUM_PRICE = config.get('MAXIMUM_PRICE', 10000000)

    clicker_data = _sync(token)
    if 'clickerUser' in clicker_data:
        user_info = clicker_data['clickerUser']
        balance_coins = user_info['balanceCoins']
    else:
        log(mrh + f"Failed to get user data\r", flush=True)
        return

    upgrades = available_upgrades(token)
    if not upgrades:
        log(mrh + f"\rFailed to get data or no upgrades available\r", flush=True)
        return

    log(bru + f"Total card available: {pth}{len(upgrades)}", flush=True)

    if _method == '1':
        upg_sort = sorted(
            [u for u in upgrades if u['price'] <= MAXIMUM_PRICE and u['price'] > 0],
            key=lambda x: -x['profitPerHour'] / x['price'] if x['price'] > 0 else 0,
            reverse=False
        )
    elif _method == '2':
        upg_sort = sorted(
            [u for u in upgrades if u['price'] <= MAXIMUM_PRICE and u['profitPerHour'] > 0 and u.get("price", 0) > 0],
            key=lambda x: x['price'] / x["profitPerHour"] if x['profitPerHour'] > 0 else float('inf'),
            reverse=False
        )
    elif _method == '4':
        upg_sort = sorted(
            [u for u in upgrades if u['price'] <= MAXIMUM_PRICE and u['price'] > 0 and u.get("profitPerHour", 0) > 0],
            key=lambda x: x["profitPerHour"] / x["price"] if x['profitPerHour'] > 0 else float('inf'),
            reverse=True
        )
    elif _method == '3':
        upg_sort = [u for u in upgrades if u['price'] <= balance_coins and u['price'] <= MAXIMUM_PRICE]
        if not upg_sort:
            log(mrh + f"No upgrade available less than balance\r", flush=True)
            return
    else:
        log(mrh + "Invalid option, please try again", flush=True)
        return

    if not upg_sort:
        log(bru + f"No {pth}item {bru}available under {pth}{_number(MAXIMUM_PRICE)}\r", flush=True)
        return

    any_upgrade_attempted = False
    upgrades_purchased = False
    while True:
        for upgrade in upg_sort:
            if upgrade['isAvailable'] and not upgrade['isExpired']:
                status = buy_upgrade(
                    token, 
                    upgrade['id'], 
                    upgrade['name'], 
                    upgrade['level'], 
                    upgrade['profitPerHour'], 
                    upgrade['price']
                )
                
                if status == 'insufficient_funds':
                    clicker_data = _sync(token)
                    if 'clickerUser' in clicker_data:
                        user_info = clicker_data['clickerUser']
                        balance_coins = user_info['balanceCoins']
                        log(mrh + f"Balance after : {pth}{_number(balance_coins)}")
                    return
                elif status == 'success':
                    upgrades_purchased = True
                    continue
                else:
                    continue
        
        if not any_upgrade_attempted:
            log(bru + f"No {pth}item {bru}available under {pth}{_number(MAXIMUM_PRICE)}\r", flush=True)
            break
        elif not upgrades_purchased:
            any_upgrade_attempted = True

def claim_daily_combo(token: str) -> dict:
    url = 'https://api.hamsterkombatgame.io/clicker/claim-daily-combo'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        bonus_coins = data.get('dailyCombo', {}).get('bonusCoins', 0)
        log(hju + f"Daily combo reward {pth}+{_number(bonus_coins)}")
        return data
    else:
        error_res = res.json()
        error_code = error_res.get('error_code')
        if error_code == 'DAILY_COMBO_NOT_READY':
            log(mrh + "Daily combo not ready.")
        elif error_code == 'DAILY_COMBO_DOUBLE_CLAIMED':
            log(kng + "Combo has already been claimed")
        else:
            log(mrh + f"Failed to claim daily combo {error_res}")
        return error_res

def get_combo_cards() -> dict:
    url = 'https://api21.datavibe.top/api/GetCombo'
    try:
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()
        data['date'] = datetime.now().strftime('%d-%m-%y')
        return data
    except requests.exceptions.RequestException as e:
        log(f"Failed getting Combo Cards. Error: {e}")
        return None

def available_upgrades(token):
    url = 'https://api.hamsterkombatgame.io/clicker/upgrades-for-buy'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        return res.json()['upgradesForBuy']
    else:
        log(mrh + f"Failed to get upgrade list: {res.json()}\r", flush=True)
        return []

def buy_upgrade(token: str, upgrade_id: str, upgrade_name: str, level: int, profitPerHour: float, price: float) -> str:
    url = 'https://api.hamsterkombatgame.io/clicker/buy-upgrade'
    headers = get_headers(token)
    data = json.dumps({"upgradeId": upgrade_id, "timestamp": int(time.time())})
    res = requests.post(url, headers=headers, data=data)
    DELAY_UPGRADE = config.get('DELAY_UPGRADE', False)
    MIN_DELAY_UPGRADE = config.get('MIN_DELAY_UPGRADE',0)
    MAX_DELAY_UPGRADE = config.get('MAX_DELAY_UPGRADE',1)
    log(bru + f"Card {hju}name {pth}{upgrade_name}    \r", flush=True)
    log(bru + f"Card {hju}price{pth} {_number(price)}       \r", flush=True)
    if res.status_code == 200:
        log(hju + f"Success {bru}| Level {pth}+{level} | +{kng}{_number(profitPerHour)}{pth}/h         \r", flush=True)
        if DELAY_UPGRADE:
            countdown_timer(randint(MIN_DELAY_UPGRADE, MAX_DELAY_UPGRADE))
        else:
            time.sleep(0.3)
        return 'success'
    else:
        error_res = res.json()
        if error_res.get('error_code') == 'INSUFFICIENT_FUNDS':
            log(mrh + f"Insufficient {kng}funds for this card       ", flush=True)
            return 'insufficient_funds'
        elif error_res.get('error_code') == 'UPGRADE_COOLDOWN':
            cooldown_time = error_res.get('cooldownSeconds')
            log(bru + f"Card {kng}cooldown for {pth}{cooldown_time} {kng}seconds.       ", flush=True)
            return 'cooldown'
        elif error_res.get('error_code') == 'UPGRADE_MAX_LEVEL':
            log(bru + f"Card {kng}is already on max level  ", flush=True)
            return 'max_level'
        elif error_res.get('error_code') == 'UPGRADE_NOT_AVAILABLE':
            log(bru + f"Not Meet{mrh} requirements to buy card", flush=True)
            return 'not_available'
        elif error_res.get('error_code') == 'UPGRADE_HAS_EXPIRED':
            log(bru + f"Card {kng}has expired you'are late      ", flush=True)
            return 'expired'
        else:
            log(kng + f"{res.json()}       ", flush=True)
            return 'error'

def execute_combo(token: str):
    combo_data = get_combo_cards()
    combo_purchased = True
    MAXIMUM_PRICE = config.get('MAXIMUM_PRICE',1000000)
    if not combo_data:
        log(mrh + f"Failed to retrieve combo data.")
        return

    not_ready_combo = []
    daily_combo_data = claim_daily_combo(token)
    if daily_combo_data and 'error_code' in daily_combo_data:
        if daily_combo_data['error_code'] == 'DAILY_COMBO_NOT_READY':
            not_ready_combo = daily_combo_data['error_message'].split(':')[-1].strip().split(',')
        elif daily_combo_data['error_code'] == 'DAILY_COMBO_DOUBLE_CLAIMED':
            return

    combo = combo_data.get('combo', [])
    if not combo:
        log(mrh + "No combo data available.")
        return

    upgrades = available_upgrades(token)
    for combo_item in combo:
        if combo_item in not_ready_combo:
            log(bru + f"Has executed {pth}{combo_item}", flush=True)
            continue

        upgrade_details = next((u for u in upgrades if u['id'] == combo_item), None)
        upgrade_price_dict = next((u for u in upgrades if u['price']), None)
        if upgrade_price_dict:
            upgrade_price = upgrade_price_dict['price']
            if upgrade_price > MAXIMUM_PRICE:
                log(kng + f"Price combo is over max price")
                return
        if upgrade_details is None:
            log(mrh + f"Failed to find details {combo_item}", flush=True)
            continue

        status = buy_upgrade(
            token, 
            combo_item, 
            combo_item, 
            upgrade_details['level'], 
            upgrade_details['profitPerHour'], 
            upgrade_details['price']
        )
        if status == 'success':
            time.sleep(1)
        else:
            combo_purchased = False
            time.sleep(1)
            break
    if combo_purchased:
        claim_daily_combo(token)
    else:
        log(kng + f"Combo not fully purchased ", flush=True)

def decode_cipher(cipher: str):
    encoded = cipher[:3] + cipher[4:]
    return base64.b64decode(encoded).decode('utf-8')
  
def claim_cipher(token):
    url = 'https://api.hamsterkombatgame.io/clicker/claim-daily-cipher'
    headers = get_headers(token)
    game_config = clicker_config(token)
    daily_cipher = game_config.get('dailyCipher')
    
    if not daily_cipher or daily_cipher.get('isClaimed', True) or not daily_cipher.get('cipher'):
        log(f"{kng}No valid cipher or already claimed.", flush=True)
        return False

    decoded_cipher = decode_cipher(cipher=daily_cipher['cipher'])
    data = {"cipher": decoded_cipher}
    res_claim = requests.post(url, headers=headers, json=data)
    
    if res_claim.status_code == 200:
        if res_claim.json().get('dailyCipher', {}).get('isClaimed', True):
            log(f"{hju}Successfully claim morse {pth}'{decoded_cipher}'", flush=True)
            return True
        else:
            log(f"{mrh}Failed to claim morse.", flush=True)
    else:
        log(f"{kng}Failed to claim daily morse. Status code: {res_claim.status_code}", flush=True)
    
    return False

def claim_key(token):
    headers = get_headers(token)
    CLAIM_KEY_DELAY = config.get('CLAIM_KEY_DELAY', False)
    MIN_CLAIM_KEY_DELAY = config.get('MIN_CLAIM_KEY_DELAY',0)
    MAX_CLAIM_KEY_DELAY = config.get('MAX_CLAIM_KEY_DELAY',1)
    sync_response = requests.post("https://api.hamsterkombatgame.io/clicker/sync", headers=headers)
    user_id = str(sync_response.json()["clickerUser"]["id"])
    encoded_cipher = base64.b64encode(f"0300000000|{user_id}".encode()).decode()
    start_response = requests.post("https://api.hamsterkombatgame.io/clicker/start-keys-minigame", headers=headers)
    
    if start_response.status_code == 400:
        error_response = start_response.json()
        if error_response.get("error_code") == "KEYS-MINIGAME_WAITING":
            log(kng + f"Likely you have claimed key's before")
            return
        else:
            log(mrh + f"Failed to start minigame: {start_response.status_code}, {start_response.text}")
            return

    log(hju + f"Checking Minigame {pth}please wait..")
    if CLAIM_KEY_DELAY:
        countdown_timer(randint(MIN_CLAIM_KEY_DELAY, MAX_CLAIM_KEY_DELAY))
    else:
        time.sleep(0.3)
    
    claim_response = requests.post(
        "https://api.hamsterkombatgame.io/clicker/claim-daily-keys-minigame",
        headers=headers,
        json={"cipher": encoded_cipher}
    )
    if claim_response.status_code == 200:
        response_json = claim_response.json()
        balance_keys = response_json['clickerUser']['balanceKeys']
        bonus_keys = response_json['dailyKeysMiniGame']['bonusKeys']
        log(hju + f"Solved minigame : {pth}+{bonus_keys} bonus keys")
        log(hju + f"Balance keys : {pth}{balance_keys}")
        return
    elif claim_response.status_code == 400:
        log(kng + f"Already claimed keys before")
        return
    else:
        error_message = claim_response.json().get("error_message", "Unknown Error")
        log(mrh + f"Failed to claim minigame: {claim_response.status_code}, {error_message}")
        return

FAKE_IPS_FILE = './data/isp_code.json'
IP_INFO_FILE = './data/accounts_info.json'

def gen_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def gen_info(fake_ips):
    entry = random.choice(fake_ips)
    info = {
        'ip': gen_ip(),
        'country_code': entry.get('country_code', 'XX'),
        'city_name': entry.get('city_name', 'Fake City'),
        'latitude': entry.get('latitude', f"{random.uniform(-90.0, 90.0):.5f}"),
        'longitude': entry.get('longitude', f"{random.uniform(-180.0, 180.0):.5f}"),
        'asn': entry.get('asn', f"{random.randint(1000, 99999)}"),
        'asn_org': entry.get('asn_org', 'Fake ISP Org')
    }
    return info

def load_all_info():
    if os.path.exists(IP_INFO_FILE):
        with open(IP_INFO_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_all_info(info_dict):
    with open(IP_INFO_FILE, 'w') as f:
        json.dump(info_dict, f, indent=4)

def faking_info(token, account, use_fake=False, info_dict=None):
    if account in info_dict:
        return info_dict[account]

    if use_fake:
        fake_ips = load_fake_file(FAKE_IPS_FILE)
        info = gen_info(fake_ips)
        info_dict[account] = info
        save_all_info(info_dict)
        return info

    url = 'https://api.hamsterkombatgame.io/ip'
    headers = get_headers(token)

    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        try:
            info = res.json()
            info_dict[account] = info
            save_all_info(info_dict)
            return info
        except json.JSONDecodeError:
            return None
    else:
        print(f"Failed with status code: {res.status_code}", flush=True)
        return None
