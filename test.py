import re
import json
import requests
import pandas as pd
import os
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import networkx as nx


BLOCKCHAIN_API_BASE = 'https://blockchain.info'

DATA_FILE_PATH = '/home/ujin/Desktop/bitcoin/bit_trace/sextortion_addresses.csv'


def load_hackers_data(file_path):
    hackers_data = []

    if not os.path.exists(file_path):
        print("File not found.")
        return hackers_data

    with open(file_path, 'r') as file:
        for line in file.readlines():
            hacker_address = line.strip()
            hackers_data.append({'hacker_address': hacker_address, 'report_type': "sextortion"})

    return hackers_data

def check_repeated_address(transactions, threshold=1):
    address_counts = {}
    for transaction in transactions:
        receiving_wallet = transaction['receiving_wallet']
        if receiving_wallet in address_counts:
            address_counts[receiving_wallet] += 1
        else:
            address_counts[receiving_wallet] = 1

    for address, count in address_counts.items():
        if count > threshold:
            return address

    return None
def write_transaction_to_file(transaction_data, output_filename):
    if not os.path.exists(output_filename):
        with open(output_filename, 'w') as f:
            f.write(','.join(transaction_data.keys()) + '\n')

    with open(output_filename, 'a') as f:
        f.write(','.join(str(value) for value in transaction_data.values()) + '\n')


def get_transactions(hacker_address, report_type):
    hacker_transactions = []
    delay = 30
    max_delay = 60
    repeated_addresses_filename = 'repeated_addresses.txt'
    hacker_addresses_queue = [hacker_address]
    initial_hacker_addresses = {hacker_address}
    offset = 0
    node = BLOCKCHAIN_API_BASE
    output_filename = f"{report_type}.Transaction_{hacker_address}.csv"
    hacker_addresses_queue = [hacker_address]
    processed_addresses = set()

    while hacker_addresses_queue:
        current_hacker_address = hacker_addresses_queue.pop(0)
        retry_count = 3
        while retry_count > 0:
            try:
                response = requests.get(f'{node}/rawaddr/{current_hacker_address}?offset={offset}')
                response.raise_for_status()
                data = response.json()
                break
            except (ChunkedEncodingError, requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Error occurred: {e}, Retrying... {retry_count} attempts left", file=sys.stderr)
                retry_count -= 1
                if retry_count <= 0:
                    print("Giving up after 3 retries.", file=sys.stderr)
                    continue
                time.sleep(delay)
                delay = min(delay * 2, max_delay)

        if response.status_code == 200:
            print("Connected...")
            print("AD:", current_hacker_address)

            if 'txs' in data:
                for tx in data['txs']:
                    for output in tx['out']:
                        if 'addr' in output:
                            receiving_wallet = output['addr']
                            transaction_amount = output['value'] / 1e8
                            
                            transaction_data = {
                                    'tx_hash': tx['hash'],
                                    'sending_wallet': current_hacker_address,
                                    'receiving_wallet': receiving_wallet,
                                    'transaction_amount': transaction_amount,
                                    'coin_type': 'BTC',
                                    'date_sent': datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d'),
                                    'time_sent': datetime.fromtimestamp(tx['time']).strftime('%H:%M:%S')
                                }
                            hacker_transactions.append(transaction_data)
                            write_transaction_to_file(transaction_data, output_filename)
                            if receiving_wallet not in processed_addresses:
                                hacker_addresses_queue.append(receiving_wallet)
                                processed_addresses.add(receiving_wallet)
                            else :
                                break  
                            print(transaction_amount)
                            if transaction_amount == 0:
                                break

                repeated_address = check_repeated_address(hacker_transactions)
                if repeated_address:
                    with open(repeated_addresses_filename, 'a') as f:
                        f.write(f"{repeated_address}\n")

                    hacker_addresses_queue.append(repeated_address)
                offset += 50
            else:
                break

        else:
            if response.status_code == 429:
                delay = min(delay * 2, max_delay)
                time.sleep(delay)

        offset = 0 
        time.sleep(delay + random.uniform(0, 3))

    return hacker_transactions

def get_next_hacker_address(transactions):
    if transactions:
        last_transaction = transactions[-1]
        return last_transaction['receiving_wallet']
    return None

def process_hacker_data(hacker_data, node):
    hacker_address = hacker_data['hacker_address']
    report_type = hacker_data['report_type']
    
    receiving_wallet = hacker_transactions['receiving_wallet']

    output_filename = f"{report_type}.Transaction_{hacker_address}.csv"
    hacker_transactions = get_transactions(hacker_address, node, output_filename)
    output_filename = f"{report_type}.Transaction_{hacker_address}_trace{receiving_wallet}.csv"


def main():
    hackers_data = load_hackers_data(DATA_FILE_PATH)
    for hacker_data in hackers_data:
        get_transactions(hacker_data['hacker_address'], hacker_data['report_type'])


if __name__ == '__main__':
    main()
