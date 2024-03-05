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
    delay = 30  # 초기 지연 시간 설정
    max_delay = 60  # 최대 지연 시간 설정
    hacker_addresses_queue = [(hacker_address, 0)]  # 발신 주소와 깊이를 큐에 추가
    processed_addresses = set([hacker_address])  # 처리된 주소를 저장하는 집합
    output_filename = f"{report_type}_Transaction_{hacker_address}.csv"  # 출력 파일명 설정

    # 파일 헤더 작성
    with open(output_filename, 'w') as f:
        f.write('tx_hash,sending_wallet,receiving_wallet,transaction_amount,coin_type,date_sent,time_sent\n')

    while hacker_addresses_queue:
        current_hacker_address, current_depth = hacker_addresses_queue.pop(0)
        if current_depth > 10:  # 최대 탐색 깊이 제한
            print("Maximum recursion depth exceeded.")
            break

        retry_count = 3  # 재시도 횟수
        while retry_count > 0:
            try:
                response = requests.get(f"{BLOCKCHAIN_API_BASE}/rawaddr/{current_hacker_address}")
                response.raise_for_status()  # 오류 상태 코드가 있을 경우 예외 발생
                data = response.json()
                break
            except Exception as e:
                print(f"Error occurred: {e}, Retrying... {retry_count} attempts left")
                retry_count -= 1
                time.sleep(delay)
                delay = min(delay * 2, max_delay)  # 지연 시간 증가

        if not response.ok:
            print(f"Failed to fetch data for address: {current_hacker_address}")
            continue

        for tx in data['txs']:
            sending_wallets = set(input_tx.get('prev_out', {}).get('addr', '') for input_tx in tx.get('inputs', []))
            for output in tx['out']:
                receiving_wallet = output.get('addr', '')
                transaction_amount = output.get('value', 0) / 1e8  # satoshi to bitcoin
                for sending_wallet in sending_wallets:
                    transaction_data = {
                        'tx_hash': tx.get('hash', ''),
                        'sending_wallet': sending_wallet,
                        'receiving_wallet': receiving_wallet,
                        'transaction_amount': transaction_amount,
                        'coin_type': 'BTC',
                        'date_sent': datetime.fromtimestamp(tx.get('time', 0)).strftime('%Y-%m-%d'),
                        'time_sent': datetime.fromtimestamp(tx.get('time', 0)).strftime('%H:%M:%S')
                    }
                    write_transaction_to_file(transaction_data, output_filename)
                    G.add_edge(sending_wallet, receiving_wallet, weight=transaction_amount, tx_hash=tx.get('hash', ''))

    return G

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

def visualize_graph(G, hacker_address):
    # 노드의 위치 결정
    pos = nx.spring_layout(G)
    
    # 엣지(선)를 그리기 위한 준비
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # 엣지를 그래프에 추가
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    # 노드(점)를 그리기 위한 준비
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    # 노드의 텍스트(주소) 레이블 준비
    node_text = []
    for node in G.nodes():
        node_text.append(node)

    # 노드를 그래프에 추가
    node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=True,
        colorscale='YlGnBu',
        size=10,
        color=[],  # 여기를 빈 리스트로 초기화합니다.
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line_width=2)
)


    # 노드의 색상과 크기를 결정
    node_colors = []  # 색상을 저장할 리스트를 생성합니다.
    for node, adjacencies in enumerate(G.adjacency()):
        node_colors.append(len(adjacencies[1]))  # 리스트에 추가합니다.
        node_info = f"{adjacencies[0]}: {len(adjacencies[1])} connections"
        node_text.append(node_info)

    node_trace.marker.color = node_colors  # 색상 리스트를 마커 색상에 할당합니다.
    node_trace.text = node_text

    # 그래프를 그림
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text="Network graph made with Python",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002)],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                     )

    # 그래프 제목 추가
    fig.update_layout(title_text=f'Network graph for {hacker_address}')
    fig.show()

    # 그래프를 HTML 파일로 저장
    fig.write_html(f"{hacker_address}_transaction_graph.html")


def main():
    # 하나의 해커 주소 데이터만 로드합니다.
    hackers_data = load_hackers_data(DATA_FILE_PATH)
    if not hackers_data:
        print("해커 데이터가 없습니다.")
        return

    # 첫 번째 해커 주소에 대해서만 트랜잭션 추적을 수행합니다.
    for i in range(100):
        hacker_data = hackers_data[i]
        G = get_transactions(hacker_data['hacker_address'], hacker_data['report_type'])

    # 추적 완료된 그래프 시각화를 위한 함수 호출
        visualize_graph(G, hacker_data['hacker_address'])


if __name__ == '__main__':
    main()