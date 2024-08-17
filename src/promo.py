import requests
from collections import defaultdict
from src.utils import get_headers
from src.__init__ import countdown_timer, log, hju, kng, mrh, pth, bru, read_config
import mysql.connector
from datetime import datetime

config = read_config()

def load_promo_from_file(filename='./data/promo.txt'):
    with open(filename, 'r') as file:
        promo_codes = [line.strip() for line in file]
    promo_dict = defaultdict(list)
    for code in promo_codes:
        code_type = code.split('-')[0]
        promo_dict[code_type].append(code)
    return promo_dict

def load_promo_from_db(db_config):
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    cursor = connection.cursor()
    cursor.execute("SELECT content FROM records WHERE user_id IS NULL")
    promo_codes = cursor.fetchall()
    cursor.close()
    connection.close()

    promo_dict = defaultdict(list)
    for code in promo_codes:
        code_type = code[0].split('-')[0]
        promo_dict[code_type].append(code[0])

    return promo_dict

def save_promo(promo_dict, filename='./data/promo.txt'):
    with open(filename, 'w') as file:
        for code_list in promo_dict.values():
            for code in code_list:
                file.write(code + '\n')

def update_promo_code_in_db(db_config, promo_code, user_id):
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    cursor = connection.cursor()
    update_query = """
    UPDATE records
    SET user_id = %s, date_sent = %s
    WHERE content = %s
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(update_query, (user_id, current_date, promo_code))
    connection.commit()
    cursor.close()
    connection.close()

def redeem_promo(token):
    if config.get('read_from_db', False):
        promo_dict = load_promo_from_db(config['db_config'])
    else:
        promo_dict = load_promo_from_file()

    if not promo_dict:
        log(mrh + f"No codes available in {pth}promo.txt.")
        return

    user_id = "66666666"
    if not user_id:
        log(mrh + "User ID not found.")
        return

    max_attempts = 4
    attempts_tracker = defaultdict(int)
    http_error_tracker = defaultdict(int)
    max_http_errors = 2

    while promo_dict:
        for code_type, codes in list(promo_dict.items()):
            if attempts_tracker[code_type] >= max_attempts:
                if codes:
                    log(hju + f"4/4 {pth}{code_type} {kng}have been applied today.")
                continue

            promo_code = codes[0]
            url = 'https://api.hamsterkombatgame.io/clicker/apply-promo'
            headers = get_headers(token)
            payload = {"promoCode": promo_code}

            try:
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()

                if res.status_code == 200:
                    log(hju + f"Applied Promo {pth}{promo_code}")
                    codes.pop(0)
                    if config.get('read_from_db', False):
                        update_promo_code_in_db(config['db_config'], promo_code, user_id='66666666')
                    else:
                        save_promo(promo_dict)
                    countdown_timer(5)
                    attempts_tracker[code_type] += 1
                    http_error_tracker[code_type] = 0
                else:
                    log(kng + f"Failed to apply {pth}{promo_code}")
                    codes.pop(0)
                    save_promo(promo_dict)

            except requests.exceptions.HTTPError as e:
                log(kng + f"Error applying {pth}{promo_code}")
                if config.get('read_from_db', False):
                    update_promo_code_in_db(config['db_config'], promo_code, user_id='66666666')
                http_error_tracker[code_type] += 1
                if http_error_tracker[code_type] >= max_http_errors:
                    log(pth + f"{code_type} {hju}Assuming maximum redemption")
                    codes.pop(0)
                    save_promo(promo_dict)
                    attempts_tracker[code_type] = max_attempts
            except Exception as err:
                log(mrh + f"Error: {err}. Promo code: {promo_code}")
                codes.pop(0)
                save_promo(promo_dict)

        if all(attempts >= max_attempts or not codes for attempts, codes in zip(attempts_tracker.values(), promo_dict.values())):
            break

    if all(attempts >= max_attempts for attempts in attempts_tracker.values()):
        log(bru + "Max reached for all promo types.")
