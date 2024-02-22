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
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


BLOCKCHAIN_API_BASE = 'https://blockchain.info'

DATA_FILE_PATH = '/home/ujin/Desktop/bitcoin/bit_trace/sextortion_addresses.csv'
# 한글 폰트 설정
plt.rcParams['font.family'] = 'NanumBarunGothic'  # 예: 'NanumBarunGothic' 등 한글 폰트 이름으로 변경


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
    # 파일 존재 여부 확인 및 헤더 추가
    with open(output_filename, 'a') as f:
        if f.tell() == 0:  # 파일 포인터가 0이면 파일이 비어 있음을 의미
            f.write(','.join(transaction_data.keys()) + '\n')
        f.write(','.join(str(value) for value in transaction_data.values()) + '\n')

def get_transactions(hacker_address, report_type):
    G = nx.DiGraph()  # 방향성 그래프 생성
    delay = 30
    max_delay = 60
    hacker_addresses_queue = [(hacker_address, 0)]  # 초기 깊이 0으로 설정
    processed_addresses = set([hacker_address])  # 초기 해커 주소를 처리된 주소에 추가
    output_filename = f"{report_type}.Transaction_{hacker_address}.csv"  # 파일 이름 설정
    offset = 0

    while hacker_addresses_queue:
        current_hacker_address, current_depth = hacker_addresses_queue.pop(0)
        if current_depth > 10:  # 재귀 깊이가 10을 초과하는 경우 종료
            print("최대 재귀 깊이 초과")
            break

        retry_count = 3

        while retry_count > 0:
            try:
                response = requests.get(f'{BLOCKCHAIN_API_BASE}/rawaddr/{current_hacker_address}?offset={offset}')
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                print(f"Error occurred: {e}, Retrying... {retry_count} attempts left")
                retry_count -= 1
                if retry_count <= 0:
                    print("Giving up after 3 retries.")
                    continue
                time.sleep(delay)
                delay = min(delay * 2, max_delay)

        if response.status_code == 200 and 'txs' in data:
            if data.get('n_tx', 0) >= 3000:  # 수취인 주소가 3000개 이상의 트랜잭션을 가지고 있는 경우 종료
                print(f"슈퍼 노드 발견: {current_hacker_address}")
                break

            for tx in data['txs']:
                for output in tx['out']:
                    if 'addr' in output:
                        receiving_wallet = output['addr']
                        transaction_amount = output['value'] / 1e8
                        
                        # 트랜잭션 데이터 구성 및 파일에 기록
                        transaction_data = {
                            'tx_hash': tx['hash'],
                            'sending_wallet': current_hacker_address,
                            'receiving_wallet': receiving_wallet,
                            'transaction_amount': transaction_amount,
                            'coin_type': 'BTC',
                            'date_sent': datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d'),
                            'time_sent': datetime.fromtimestamp(tx['time']).strftime('%H:%M:%S')
                        }
                        write_transaction_to_file(transaction_data, output_filename)

                        # 그래프에 노드와 에지 추가
                        G.add_node(current_hacker_address)
                        G.add_node(receiving_wallet)
                        if G.has_edge(current_hacker_address, receiving_wallet):
                            G[current_hacker_address][receiving_wallet]['weight'] += transaction_amount
                        else:
                            G.add_edge(current_hacker_address, receiving_wallet, weight=transaction_amount)

                        if receiving_wallet not in processed_addresses:
                            hacker_addresses_queue.append((receiving_wallet, current_depth + 1))
                            processed_addresses.add(receiving_wallet)

            offset += 50  # 다음 트랜잭션 페이지로 이동
        else:
            if response.status_code == 429:  # 요청 제한에 도달한 경우
                time.sleep(delay)
        time.sleep(delay + random.uniform(0, 3))  # API 요청 간 지연 시간

    return G  # 분석 완료된 그래프 반환


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
    # 하나의 해커 주소 데이터만 로드합니다.
    hackers_data = load_hackers_data(DATA_FILE_PATH)
    if not hackers_data:
        print("해커 데이터가 없습니다.")
        return

    # 첫 번째 해커 주소에 대해서만 트랜잭션 추적을 수행합니다.
    hacker_data = hackers_data[0]
    G = get_transactions(hacker_data['hacker_address'], hacker_data['report_type'])

    # 추적 완료된 그래프 시각화
    plt.figure(figsize=(10, 8))  # 시각화 크기 설정
    nx.draw(G, with_labels=True, node_size=700, node_color="skyblue", font_size=10)
    plt.title(f"자금 흐름 그래프: {hacker_data['hacker_address']}")
    plt.show()

    # 그래프 저장 (필요한 경우)
    # nx.write_gexf(G, f"{hacker_data['hacker_address']}_자금_흐름_그래프.gexf")

if __name__ == '__main__':
    main()