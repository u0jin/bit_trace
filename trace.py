import os
import time
import random
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

DATA_FILE_PATH = '/home/ujin/Desktop/bitcoin/bit_trace/hacker_addresses.csv'

def create_rpc_connection():
    rpc_user = 'ujin'
    rpc_password = '7749'
    rpc_host = '127.0.0.1'
    rpc_port = '8332'
    wallet_name = 'ujin' 
    print(f"Connecting to RPC server at {rpc_host}:{rpc_port}")
    try:
        connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}/wallet/{wallet_name}")
        print("Successfully connected to RPC server.")
        return connection
    except Exception as e:
        print(f"Failed to connect to RPC server: {e}")

def load_hackers_data(file_path):
    hackers_data = []

    if not os.path.exists(file_path):
        print("File not found:", file_path)
        return hackers_data
    print(f"Loading hacker data from {file_path}")

    with open(file_path, 'r') as file:
        # Skip the header line
        next(file)
        for line in file.readlines():
            # Split by comma and strip whitespace
            hacker_address, report_type = line.strip().split(',')
            hackers_data.append({'hacker_address': hacker_address, 'report_type': report_type})
    for hacker in hackers_data:
        print("Loaded address:", hacker['hacker_address'])
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

def get_transactions(hacker_address, rpc_client):
    try:
        # 주소와 관련된 모든 트랜잭션 ID를 조회
        txids = rpc_client.getaddresstxids({"addresses": [hacker_address]})
        
        hacker_transactions = []
        for txid in txids:
            # 각 트랜잭션 ID에 대한 트랜잭션 정보 조회
            transaction = rpc_client.getrawtransaction(txid, 1)  # 1은 디코딩된 트랜잭션을 반환하도록 지정

            # 필요한 데이터만 추출
            transaction_data = {
                'txid': transaction['txid'],
                'time': datetime.fromtimestamp(transaction['time']).strftime('%Y-%m-%d %H:%M:%S'),
                'details': transaction['details']
            }
            hacker_transactions.append(transaction_data)

        # 관련 트랜잭션 출력
        print(f"Found {len(hacker_transactions)} transactions related to the address.")
        for transaction in hacker_transactions:
            print(transaction)
    except Exception as e:
        print(f"Error: {e}")
        
def main():
    print("Starting the script...")
    rpc_client = create_rpc_connection()
    hackers_data = load_hackers_data(DATA_FILE_PATH)
    if not hackers_data:
        print("No hacker data to process. Exiting.")
        return
    for hacker_data in hackers_data:
        get_transactions(hacker_data['hacker_address'], rpc_client)

if __name__ == '__main__':
    main()