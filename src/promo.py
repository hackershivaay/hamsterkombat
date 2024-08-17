from sqlalchemy import create_engine, Column, String, Table, MetaData, update, select
from sqlalchemy.orm import sessionmaker
from collections import defaultdict
from datetime import datetime
import requests
from src.utils import get_headers
from src.__init__ import countdown_timer, log, hju, kng, mrh, pth, bru, read_config


config = read_config()

def create_db_engine(db_config):
    return create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")

def load_promo_from_file(filename='./data/promo.txt'):
    with open(filename, 'r') as file:
        promo_codes = [line.strip() for line in file]
    promo_dict = defaultdict(list)
    for code in promo_codes:
        code_type = code.split('-')[0]
        promo_dict[code_type].append(code)
    return promo_dict

def load_promo_from_db(db_config):
    engine = create_db_engine(db_config)
    metadata = MetaData()
    records_table = Table('records', metadata, autoload_with=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    promo_dict = defaultdict(list)
    try:
        stmt = select(records_table.c.content).where(records_table.c.user_id == None)
        promo_codes = session.execute(stmt).fetchall()
        for code in promo_codes:
            code_type = code[0].split('-')[0]
            promo_dict[code_type].append(code[0])
    except Exception as e:
        log(mrh + f"Database error: {e}")
    finally:
        session.close()

    return promo_dict


def save_promo(promo_dict, filename='./data/promo.txt'):
    with open(filename, 'w') as file:
        for code_list in promo_dict.values():
            for code in code_list:
                file.write(code + '\n')

def update_promo_code_in_db(db_config, promo_code, user_id):
    engine = create_db_engine(db_config)
    metadata = MetaData()
    records_table = Table('records', metadata, autoload_with=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        stmt = update(records_table).where(records_table.c.content == promo_code).values(user_id=user_id, date_sent=current_date)
        session.execute(stmt)
        session.commit()
    except Exception as e:
        log(mrh + f"Database update error: {e}")
    finally:
        session.close()


def redeem_promo(token, user_id):
    if config.get('read_from_db', False):
        promo_dict = load_promo_from_db(config['db_config'])
    else:
        promo_dict = load_promo_from_file()

    if not promo_dict:
        log(mrh + f"No codes available in {pth}promo.txt.")
        return

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
                        update_promo_code_in_db(config['db_config'], promo_code, user_id=user_id)
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
                try:
                    error_data = res.json()
                    if error_data.get('error_code') == "MaxKeysReceived":
                        log(pth + f"{code_type} {hju}Max keys received for today.")
                        attempts_tracker[code_type] = max_attempts
                    else:
                        log(kng + f"Error applying {pth}{promo_code}: {error_data.get('error_message')}")
                        http_error_tracker[code_type] += 1
                        if http_error_tracker[code_type] >= max_http_errors:
                            log(pth + f"{code_type} {hju}Assuming maximum redemption")
                            codes.pop(0)
                            if config.get('read_from_db', False):
                                update_promo_code_in_db(config['db_config'], promo_code, user_id=user_id)
                            else:
                                save_promo(promo_dict)
                            attempts_tracker[code_type] = max_attempts
                except ValueError:
                    log(kng + f"Error applying {pth}{promo_code}")
                    http_error_tracker[code_type] += 1
                    if http_error_tracker[code_type] >= max_http_errors:
                        log(pth + f"{code_type} {hju}Assuming maximum redemption")
                        codes.pop(0)

                        if config.get('read_from_db', False):
                            update_promo_code_in_db(config['db_config'], promo_code, user_id=user_id)
                        else:
                            save_promo(promo_dict)
                        attempts_tracker[code_type] = max_attempts

            except Exception as err:
                log(mrh + f"Error: {err}. Promo code: {promo_code}")
                codes.pop(0)
                if config.get('read_from_db', False):
                    update_promo_code_in_db(config['db_config'], promo_code, user_id=user_id)
                else:
                    save_promo(promo_dict)

        if all(attempts >= max_attempts or not codes for attempts, codes in zip(attempts_tracker.values(), promo_dict.values())):
            break

    if all(attempts >= max_attempts for attempts in attempts_tracker.values()):
        log(bru + "Max reached for all promo types.")
