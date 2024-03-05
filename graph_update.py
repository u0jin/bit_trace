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
import plotly.graph_objects as go


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
                sending_wallets = set()
                # 입력 주소 기반으로 발신자 주소 세트 생성
                for input_tx in tx.get('inputs', []):
                    if 'prev_out' in input_tx and 'addr' in input_tx['prev_out']:
                        sending_wallets.add(input_tx['prev_out']['addr'])

                # 각 발신자 주소에 대해 수신자 주소와 연결
                for output in tx['out']:
                    if 'addr' in output:
                        receiving_wallet = output['addr']
                        transaction_amount = output['value'] / 1e8  # satoshi to bitcoin
                        for sending_wallet in sending_wallets:
                            # 파일에 트랜잭션 데이터 기록
                            transaction_data = {
                                'tx_hash': tx['hash'],
                                'sending_wallet': sending_wallet,
                                'receiving_wallet': receiving_wallet,
                                'transaction_amount': transaction_amount,
                                'coin_type': 'BTC',
                                'date_sent': datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d'),
                                'time_sent': datetime.fromtimestamp(tx['time']).strftime('%H:%M:%S')
                            }
                            write_transaction_to_file(transaction_data, output_filename)
                            # 그래프에 노드와 엣지 추가
                            G.add_edge(sending_wallet, receiving_wallet, weight=transaction_amount)

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

def visualize_graph(G,hacker_address):
    pos = nx.spring_layout(G)  # 노드의 위치 결정

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            color=list(dict(G.degree()).values()),
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2),
        text=node_text)

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Network graph made with Python',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                     )
    fig.show()


    # 그래프 저장 (필요한 경우)
    fig.write_html(f"{hacker_address}_transaction_graph.html")

def main():
    # 하나의 해커 주소 데이터만 로드합니다.
    hackers_data = load_hackers_data(DATA_FILE_PATH)
    if not hackers_data:
        print("해커 데이터가 없습니다.")
        return

    # 첫 번째 해커 주소에 대해서만 트랜잭션 추적을 수행합니다.
    hacker_data = hackers_data[0]
    G = get_transactions(hacker_data['hacker_address'], hacker_data['report_type'])

    # 추적 완료된 그래프 시각화를 위한 함수 호출
    visualize_graph(G, hacker_data['hacker_address'])


if __name__ == '__main__':
    main()