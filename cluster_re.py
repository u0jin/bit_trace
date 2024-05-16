import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.preprocessing import StandardScaler

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
            # 가상의 수치형 데이터 추가
            data.append([row['hacker_address'], row['report_type'], 
                         np.random.randint(1, 1000),  # total_received
                         np.random.randint(1, 1000),  # total_sent
                         np.random.randint(1, 100)    # num_transactions
                        ])
    return data

def sample_data_by_type(data, sample_size=100):
    df = pd.DataFrame(data, columns=['Address', 'ReportType', 'TotalReceived', 'TotalSent', 'NumTransactions'])
    sampled_df = df.groupby('ReportType').apply(lambda x: x.sample(n=min(len(x), sample_size)))
    return sampled_df.reset_index(drop=True).values.tolist()

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
    df = pd.DataFrame(data, columns=['Address', 'ReportType', 'TotalReceived', 'TotalSent', 'NumTransactions'])
    df = pd.get_dummies(df, columns=['ReportType'])  # 'ReportType'을 원-핫 인코딩
    addresses = df['Address'].values
    data_values = df.drop(columns=['Address']).values  # 클러스터링에 필요한 값들
    
    scaler = StandardScaler()  # 데이터 표준화
    data_scaled = scaler.fit_transform(data_values)  # 주소를 제외한 데이터를 표준화
    kmeans = MiniBatchKMeans(n_clusters=initial_clusters, batch_size=1000)  # 미니 배치 K-Means
    initial_labels = kmeans.fit_predict(data_scaled)
    final_labels = np.copy(initial_labels)
    
    for k in range(initial_clusters):
        cluster_data = data_scaled[initial_labels == k]
        if len(cluster_data) > 1:  # 더 작은 클러스터 생성
            mini_kmeans = MiniBatchKMeans(n_clusters=min(refined_clusters, len(cluster_data)), batch_size=100)
            refined_labels = mini_kmeans.fit_predict(cluster_data)
            for idx, label in enumerate(refined_labels):
                address = addresses[initial_labels == k][idx]
                if reuse_map[address]:
                    final_labels[initial_labels == k] = refined_labels + k * refined_clusters
                    
    return final_labels

def visualize_clustering(data, labels):
    df = pd.DataFrame(data, columns=['Address', 'ReportType', 'TotalReceived', 'TotalSent', 'NumTransactions'])
    df['Cluster'] = labels
    
    # 클러스터링 결과 시각화
    sns.pairplot(df, vars=['TotalReceived', 'TotalSent', 'NumTransactions'], hue='Cluster', palette='deep')
    plt.suptitle('Hybrid Clustering Visualization', verticalalignment='top')
    plt.show()
    
    # 유형별 클러스터링 결과 시각화
    for t in df['ReportType'].unique():
        sns.pairplot(df[df['ReportType'] == t], vars=['TotalReceived', 'TotalSent', 'NumTransactions'], hue='Cluster', palette='deep')
        plt.suptitle(f'Clustering Visualization for Type: {t}', verticalalignment='top')
        plt.show()

def main():
    file_path = 'hacker_addresses.csv'  # 절대 경로 대신 상대 경로 사용
    preview_csv(file_path)
    data = load_data_from_csv(file_path)
    sampled_data = sample_data_by_type(data, sample_size=100)
    reuse_map = address_reuse_heuristic(sampled_data)
    labels = hybrid_clustering(sampled_data, reuse_map=reuse_map)
    visualize_clustering(sampled_data, labels)

if __name__ == "__main__":
    main()
