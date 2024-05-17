import os
import json
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
import time

# JSON 파일이 있는 디렉토리 경로
tx_directory_path = '/media/ujin/Bitcoin/txDetail'
csv_file_path = 'sampled_hacker_addresses.csv'

# 잔금이 많은 주소의 기준 (예: 1000 비트코인 이상)
large_balance_threshold = 1000

# 트랜잭션의 최대 출력 주소 수
max_output_addresses = 100

# 병렬 처리 워커 수
max_workers = 4  # 시스템 메모리에 따라 조정 가능

def preview_csv(file_path, num_lines=5):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            if i == num_lines:
                break
            print(row)

def load_data_from_csv(file_path):
    data = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append([row['hacker_address'], row['report_type']])
    return data

def sample_data_by_type(data, sample_size=100):
    df = pd.DataFrame(data, columns=['Address', 'ReportType'])
    sampled_df = df.groupby('ReportType').apply(lambda x: x.sample(n=min(len(x), sample_size)))
    return sampled_df.reset_index(drop=True)

def load_tx_details(txid, tx_directory_path):
    try:
        with open(os.path.join(tx_directory_path, f"{txid}.json"), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {txid}: {e}")
        return None

def is_large_balance_transaction(tx_data, threshold):
    total_sent = sum(vout['value'] for vout in tx_data.get('vout', []))
    return total_sent >= threshold

def has_many_output_addresses(tx_data, max_addresses):
    return len(tx_data.get('vout', [])) > max_addresses

def process_transaction_file(file_path, current_address, visited, writer):
    transactions = []
    try:
        with open(file_path, 'r') as f:
            tx_data = json.load(f)
        addresses = [addr for vout in tx_data.get('vout', []) for addr in vout['scriptPubKey'].get('addresses', [])]
        if current_address in addresses:
            transactions.append(tx_data)
            writer.writerow([current_address, tx_data['txid'], json.dumps(tx_data)])
            if is_large_balance_transaction(tx_data, large_balance_threshold) or has_many_output_addresses(tx_data, max_output_addresses):
                return transactions
            for vin in tx_data.get('vin', []):
                vin_txid = vin.get('txid')
                if vin_txid and vin_txid not in visited:
                    visited.add(vin_txid)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return transactions

def bfs_track_transactions(start_addresses, tx_directory_path, output_dir, max_depth=3):
    visited = set()
    queue = deque([(addr, 0) for addr in start_addresses])
    transactions = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while queue:
            current_address, depth = queue.popleft()
            if depth > max_depth:
                continue

            visited.add(current_address)
            address_output_file = os.path.join(output_dir, f'{current_address}.csv')
            with open(address_output_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if os.stat(address_output_file).st_size == 0:
                    writer.writerow(['Address', 'TxID', 'TxData'])
                futures = []
                for filename in os.listdir(tx_directory_path):
                    file_path = os.path.join(tx_directory_path, filename)
                    future = executor.submit(process_transaction_file, file_path, current_address, visited, writer)
                    futures.append(future)
                    print(f"Scheduled processing for file: {filename}")

                for future in as_completed(futures):
                    try:
                        transactions.extend(future.result())
                    except Exception as e:
                        print(f"Error processing transaction: {e}")

    return transactions

def extract_transaction_features(transactions):
    features = []
    for tx in transactions:
        total_received = sum(vout['value'] for vout in tx.get('vout', []))
        total_sent = sum(vin.get('value', 0) for vin in tx.get('vin', []))
        num_transactions = len(tx.get('vin', [])) + len(tx.get('vout', []))
        features.append([tx.get('txid'), total_received, total_sent, num_transactions])
    return pd.DataFrame(features, columns=['TxID', 'TotalReceived', 'TotalSent', 'NumTransactions'])

def address_reuse_heuristic(data):
    reuse_map = {}
    address_count = {}
    
    for entry in data:
        address = entry[0]
        if address in address_count:
            address_count[address] += 1
        else:
            address_count[address] = 1
    
    for address, count in address_count.items():
        reuse_map[address] = count > 1
        
    return reuse_map

def hybrid_clustering(data, initial_clusters=3, refined_clusters=2, reuse_map=None):
    df = pd.DataFrame(data, columns=['TxID', 'TotalReceived', 'TotalSent', 'NumTransactions'])
    data_values = df.drop(columns=['TxID']).values
    
    scaler = StandardScaler()  # 데이터 표준화
    data_scaled = scaler.fit_transform(data_values)
    kmeans = MiniBatchKMeans(n_clusters=initial_clusters, batch_size=1000)  # 미니 배치 K-Means
    initial_labels = kmeans.fit_predict(data_scaled)
    final_labels = np.copy(initial_labels)
    
    for k in range(initial_clusters):
        cluster_data = data_scaled[initial_labels == k]
        if len(cluster_data) > 1:
            mini_kmeans = MiniBatchKMeans(n_clusters=min(refined_clusters, len(cluster_data)), batch_size=100)
            refined_labels = mini_kmeans.fit_predict(cluster_data)
            for idx, label in enumerate(refined_labels):
                txid = data[initial_labels == k][idx][0]
                if reuse_map.get(txid, False):
                    final_labels[initial_labels == k] = refined_labels + k * refined_clusters
                    
    return final_labels

def visualize_clustering(data, labels, report_type):
    df = pd.DataFrame(data, columns=['TxID', 'TotalReceived', 'TotalSent', 'NumTransactions'])
    df['Cluster'] = labels
    
    sns.pairplot(df, vars=['TotalReceived', 'TotalSent', 'NumTransactions'], hue='Cluster', palette='deep')
    plt.suptitle(f'Hybrid Clustering Visualization for {report_type}', verticalalignment='top')
    plt.savefig(f'clustering_{report_type}.png')
    plt.show()

def save_results(features, labels, report_type, summary_file_prefix='cluster_summary'):
    # 각 트랜잭션에 대한 클러스터 레이블 추가
    features['Cluster'] = labels
    
    # 각 클러스터별 통계 요약
    cluster_summary = features.groupby('Cluster').agg(
        TotalTransactions=('TxID', 'count'),
        TotalReceived=('TotalReceived', 'sum'),
        TotalSent=('TotalSent', 'sum'),
        AvgReceived=('TotalReceived', 'mean'),
        AvgSent=('TotalSent', 'mean'),
        AvgNumTransactions=('NumTransactions', 'mean')
    ).reset_index()
    
    # 요약 정보를 CSV 파일로 저장
    summary_file = f'{summary_file_prefix}_{report_type}.csv'
    cluster_summary.to_csv(summary_file, index=False)
    print(f"Cluster summary saved to {summary_file}")

def analyze_hacking_patterns(transactions_df):
    grouped = transactions_df.groupby('ReportType').agg({
        'TotalReceived': ['mean', 'median', 'std'],
        'TotalSent': ['mean', 'median', 'std'],
        'NumTransactions': ['mean', 'median', 'std']
    }).reset_index()
    grouped.to_csv('hacking_patterns_summary.csv', index=False)
    print("Hacking patterns analysis saved to hacking_patterns_summary.csv")
    return grouped

def analyze_time_distribution(transactions_df):
    transactions_df['Time'] = pd.to_datetime(transactions_df['Time'], unit='s')
    transactions_df['Hour'] = transactions_df['Time'].dt.hour
    time_distribution = transactions_df.groupby(['ReportType', 'Hour']).size().unstack().fillna(0)
    time_distribution.to_csv('time_distribution_summary.csv', index=False)
    print("Time distribution analysis saved to time_distribution_summary.csv")
    return time_distribution

def analyze_correlations(transactions_df):
    correlations = transactions_df[['TotalReceived', 'TotalSent', 'NumTransactions']].corr()
    correlations.to_csv('correlations_summary.csv')
    print("Correlation analysis saved to correlations_summary.csv")
    return correlations

def plot_hacking_patterns(hacking_patterns):
    hacking_patterns.plot(kind='bar', subplots=True, layout=(3, 1), figsize=(10, 15), title='Hacking Patterns by Type')
    plt.tight_layout()
    plt.savefig('hacking_patterns.png')
    plt.show()

def main():
    preview_csv(csv_file_path)
    data = load_data_from_csv(csv_file_path)
    sampled_data = sample_data_by_type(data, sample_size=100)

    print("Data sampling completed.")
    
    all_transactions_df = pd.DataFrame()

    # 신고 유형별로 처리
    for report_type, group in sampled_data.groupby('ReportType'):
        print(f"Processing report type: {report_type}")
        start_time = time.time()
        
        hacker_addresses = group['Address'].tolist()
        output_dir = f'transactions_{report_type}'
        
        # 신고 유형별 디렉토리 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # BFS 알고리즘을 사용하여 트랜잭션 추적 및 실시간 저장
        transactions = bfs_track_transactions(hacker_addresses, tx_directory_path, output_dir)
        print(f"Transaction tracking completed for {report_type}. Time taken: {time.time() - start_time:.2f} seconds")
        
        # 트랜잭션 특징 추출
        all_transactions = []
        for address in hacker_addresses:
            address_file = os.path.join(output_dir, f'{address}.csv')
            with open(address_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # 헤더 스킵
                for row in reader:
                    tx_data = json.loads(row[2])
                    all_transactions.append(tx_data)
        
        print(f"Extracted {len(all_transactions)} transactions for {report_type}.")
        
        features = extract_transaction_features(all_transactions)
        features['ReportType'] = report_type  # ReportType 열 추가
        all_transactions_df = pd.concat([all_transactions_df, features], ignore_index=True)
        
        # 클러스터링
        reuse_map = address_reuse_heuristic(features.values.tolist())
        labels = hybrid_clustering(features.values.tolist(), reuse_map=reuse_map)
        
        # 시각화 및 결과 저장
        visualize_clustering(features.values.tolist(), labels, report_type)
        save_results(features.values.tolist(), labels, report_type)
    
    # 추가 분석 및 시각화
    hacking_patterns = analyze_hacking_patterns(all_transactions_df)
    time_distribution = analyze_time_distribution(all_transactions_df)
    correlations = analyze_correlations(all_transactions_df)
    plot_hacking_patterns(hacking_patterns)

if __name__ == "__main__":
    main()
