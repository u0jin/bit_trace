import os
import time
import random
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

DATA_FILE_PATH = '/home/ujin/Desktop/bitcoin/trace_code/hacker_addresses.csv'

def create_rpc_connection():
    rpc_user = 'ujin'
    rpc_password = '7749'
    rpc_host = '127.0.0.1'
    rpc_port = '8332'
    return AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

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


def get_transactions(hacker_address, report_type, rpc_client):
    hacker_transactions = []
    delay = 30
    max_delay = 60
    repeated_addresses_filename = 'repeated_addresses.txt'
    output_filename = f"{report_type}.Transaction_{hacker_address}.csv"
    processed_addresses = set()

    try:
        address_transactions = rpc_client.listtransactions("*", 10000, 0, True)
        for tx in address_transactions:
            if 'address' in tx and tx['address'] == hacker_address:
                transaction_data = {
                    'tx_hash': tx['txid'],
                    'sending_wallet': hacker_address,
                    'receiving_wallet': tx['address'],
                    'transaction_amount': tx['amount'],
                    'coin_type': 'BTC',
                    'date_sent': datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d'),
                    'time_sent': datetime.fromtimestamp(tx['time']).strftime('%H:%M:%S')
                }
                hacker_transactions.append(transaction_data)
                write_transaction_to_file(transaction_data, output_filename)
                if tx['address'] not in processed_addresses:
                    processed_addresses.add(tx['address'])

        repeated_address = check_repeated_address(hacker_transactions)
        if repeated_address:
            with open(repeated_addresses_filename, 'a') as f:
                f.write(f"{repeated_address}\n")
    except JSONRPCException as e:
        print(f"RPC error: {e}")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)

def main():
    rpc_client = create_rpc_connection()
    hackers_data = load_hackers_data(DATA_FILE_PATH)
    for hacker_data in hackers_data:
        get_transactions(hacker_data['hacker_address'], hacker_data['report_type'], rpc_client)

if __name__ == '__main__':
    main()
