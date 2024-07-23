import json
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
    _number, countdown_timer
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
            min_tap = config.get('min_tap', 0)
            max_tap = config.get('max_tap', max_taps)
            tapDelay = config.get('tapDelay', False)
            log(hju + f"Total {pth}{available_taps:>2,} {hju}Energy available\r")
            while available_taps > 100:
                tap_count = randint(min_tap, max_tap)
                
                if tap_count > available_taps:
                    tap_count = available_taps

                res = tap(token, tap_count, available_taps) 

                if res.status_code == 200:
                    available_taps -= tap_count
                    log(hju + f"Tapping {kng}{tap_count:>4,}, {bru}remaining {pth}{available_taps:<4,}", flush=True)

                    if tapDelay:
                        countdown_timer(randint(1, 4))
                    else:
                        time.sleep(0.1)
                else:
                    log("Failed to make a tap\r")
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
    data = json.dumps({"taskId": "streak_days"})
    res = requests.post(url, headers=headers, data=data)
    data = res.json()
    if res.status_code == 200:
        if data['task']['completedAt']:
            log(f"{hju}Daily streaks {pth}already claimed\r" + Style.RESET_ALL)
        else:
            log(f"{hju}Daily streaks {pth}claimed successfully\r" + Style.RESET_ALL)
    else:
        log(f"{mrh}Daily streaks", data.get('error', 'Unknown error') + Style.RESET_ALL)
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
                            log(f"{hju}Claim success get {pth}+{task['rewardCoins']} coin\r", flush=True)
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
            cooldown = res_data['cooldownSeconds']
            log(f"{kng}Boost cooldown: {kng}{cooldown} seconds remaining.")
            return False
        else:
            log(f"{hju}Boost {kng}successfully applied!")
            time.sleep(1)
            return True
    else:
        log(f"{kng}boost on cooldown or unavailable")
        time.sleep(1)
        return False

def available_upgrades(token):
    url = 'https://api.hamsterkombatgame.io/clicker/upgrades-for-buy'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        return res.json()['upgradesForBuy']
    else:
        log(mrh + f"Failed to get upgrade list: {res.json()}\r", flush=True)
        return []

def upgrade_passive(token, _method):
    max_price = config.get('max_price', 10000000)

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

    log(bru + f"Total upgrades available: {pth}{len(upgrades)}", flush=True)

    if _method == '1':
        upg_sort = sorted(
            [u for u in upgrades if u['price'] <= max_price],
            key=lambda x: -x['profitPerHour']
        )
    elif _method == '2':
        upg_sort = sorted(
            [u for u in upgrades if u['price'] <= max_price],
            key=lambda x: x['price']
        )
    elif _method == '3':
        upg_sort = [u for u in upgrades if u['price'] <= balance_coins and u['price'] <= max_price]
        if not upg_sort:
            log(mrh + f"No upgrade available less than balance\r", flush=True)
            return
    elif _method == '4':
        ## sort by max 'profitPerHourDelta' for minimal 'price' 
        upg_sort = [u for u in upgrades if u['price'] <= balance_coins and u['price'] <= max_price]
        upg_sort = sorted(
            [u for u in upg_sort if u['price'] <= max_price],
            key=lambda x: 0 if x['price']<=0 else -x['profitPerHourDelta']/x['price']
        )

    else:
        log(mrh + "Invalid option please try again", flush=True)
        return

    if not upg_sort:
        log(kng + f"No upgrades available under the Max Price\r", flush=True)
        return

    upgrades_purchased = False

    for upgrade in upg_sort:
        if upgrade['isAvailable'] and not upgrade['isExpired']:
            log(f"{hju}Trying to upgrade {pth}{upgrade['name']}", flush=True, end='\r')

            status = buy_upgrade(
                token, 
                upgrade['id'], 
                upgrade['name'], 
                upgrade['level'], 
                upgrade['profitPerHour'], 
                upgrade['price']
                )
            
            if status == 'insufficient_funds':
                break
            elif status == 'success':
                upgrades_purchased = True
                continue
            else:
                continue
    if not upgrades_purchased:
        log(bru + f"Not available under max price of {max_price}\r", flush=True)


def buy_upgrade(token: str, upgrade_id: str, upgrade_name: str, level: int, profitPerHour: float, price: float) -> str:
    url = 'https://api.hamsterkombatgame.io/clicker/buy-upgrade'
    headers = get_headers(token)
    data = json.dumps({"upgradeId": upgrade_id, "timestamp": int(time.time())})
    res = requests.post(url, headers=headers, data=data)
    delayUpgrade = config.get('delayUpgrade', 3)
    log(bru + f"Card {hju}name {pth}{upgrade_name}           \r", flush=True)
    log(bru + f"Card {hju}price{pth} {_number(price)}          \r", flush=True)
    if res.status_code == 200:
        log(hju + f"Success {bru}| Level {pth}+{level} | +{kng}{_number(profitPerHour)}{pth}/h         \r", flush=True)
        time.sleep(delayUpgrade)
        return 'success'
    else:
        time.sleep(delayUpgrade)
        error_res = res.json()
        if error_res.get('error_code') == 'INSUFFICIENT_FUNDS':
            log(mrh + f"Insufficient {kng}funds for this card       ", flush=True)
            return 'insufficient_funds'
        elif error_res.get('error_code') == 'UPGRADE_COOLDOWN':
            cooldown_time = error_res.get('cooldownSeconds')
            log(bru + f"Card {kng}cooldown for {pth}{cooldown_time} {kng}seconds.          ", flush=True)
            return 'cooldown'
        elif error_res.get('error_code') == 'UPGRADE_MAX_LEVEL':
            log(bru + f"Card {kng}is already on max level  ", flush=True)
            return 'max_level'
        elif error_res.get('error_code') == 'UPGRADE_NOT_AVAILABLE':
            log(bru + f"Card {mrh}not meet requirements    ", flush=True)
            return 'not_available'
        elif error_res.get('error_code') == 'UPGRADE_HAS_EXPIRED':
            log(bru + f"Card {kng}has expired you'are late      ", flush=True)
            return 'expired'
        else:
            log(kng + f"{res.json()}       ", flush=True)
            return 'error'
   
def claim_daily_combo(token: str) -> dict:
    url = 'https://api.hamsterkombatgame.io/clicker/claim-daily-combo'
    headers = get_headers(token)
    res = requests.post(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        bonus_coins = data.get('dailyCombo', {}).get('bonusCoins', 0)
        log(hju + f"Daily combo reward {pth}+{bonus_coins}")
        return data
    elif res.status_code == 400:
        error_res = res.json()
        error_code = error_res.get('error_code')
        if error_code == 'DAILY_COMBO_NOT_READY':
            time.sleep(1)
        elif error_code == 'DAILY_COMBO_DOUBLE_CLAIMED':
            log(kng + "Combo has already been claimed before")
        else:
            log(mrh + f"Failed to claim daily combo {error_res}\r")
        return error_res
    else:
        log(mrh + f"Failed to claim daily combo {res.json()}\r")
        return None

def get_combo_cards() -> dict:
    url = 'https://api21.datavibe.top/api/GetCombo'
    payload = {}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        current_date = datetime.now().strftime('%d-%m-%y')
        data['date'] = current_date
        return data
    except requests.exceptions.RequestException as e:
        log(f"Failed getting Combo Cards. Error: {e}")
        return None

def execute_combo(token: str):
    combo_data = get_combo_cards()
    if not combo_data:
        log("Failed to retrieve combo data.")
        return None

    daily_combo_data = claim_daily_combo(token)
    if daily_combo_data and 'error_code' in daily_combo_data and daily_combo_data['error_code'] == 'DAILY_COMBO_DOUBLE_CLAIMED':
        return

    if daily_combo_data and 'error_code' in daily_combo_data and daily_combo_data['error_code'] == 'DAILY_COMBO_NOT_READY':
        not_ready_combo = daily_combo_data['error_message'].split(':')[-1].strip()
        not_ready_combo = not_ready_combo.split(',')
    else:
        not_ready_combo = []

    combo = combo_data.get('combo', [])
    if not combo:
        log("No combo data available.")
        return None

    upgrades = available_upgrades(token)
    combo_purchased = True

    for combo_item in combo:
        if combo_item in not_ready_combo:
            log(bru + f"Already {kng}executed {pth}{combo_item}")
            continue

        upgrade_details = next((u for u in upgrades if u['id'] == combo_item), None)

        if upgrade_details is None:
            log(f"Failed to find details {combo_item}")
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
            log(hju +  f"Executed {kng}combo {pth}{combo_item}")
            time.sleep(1)
        else:
            log(mrh + f"Fail {kng}execute {pth}{combo_item}")
            combo_purchased = False
            break

    if combo_purchased:
        claim_result = claim_daily_combo(token)
        if claim_result.get("status") == "success":
            log(hju + f"Successfully claimed daily combo.")
        else:
            log(mrh + "Failed to claim daily combo.")
    else:
        log(mrh + "Failed to complete combo purchases.")
        time.sleep(3)

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
    log(f"{hju}Today morse is {pth}'{decoded_cipher}'\r", flush=True)

    res_claim = requests.post(url, headers=headers, json=data)
    
    if res_claim.status_code == 200:
        if res_claim.json().get('dailyCipher', {}).get('isClaimed', True):
            log(f"{hju}Successfully claimed morse.", flush=True)
            return True
        else:
            log(f"{mrh}Failed to claim morse.", flush=True)
    else:
        log(f"{kng}Failed to claim daily morse. Status code: {res_claim.status_code}", flush=True)
    
    return False