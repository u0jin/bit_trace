import os
import json
import numpy as np
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from py2neo import Graph, Node, Relationship, NodeMatcher
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from bitcoinrpc.authproxy import AuthServiceProxy

# 데이터베이스 및 RPC 연결 정보
graph_uri = "bolt://localhost:7687"
graph_auth = ("ujin", "tryit5826")
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'

# 파일 경로 설정
data_dir = '/home/ujin/Desktop/bitcoin/bit_trace/'

def load_csv(file_path):
    data = {}
    try:
        with open(file_path, mode='r') as infile:
            reader = csv.reader(infile)
            headers = next(reader)  # 헤더 스킵
            for row in reader:
                if len(row) == 2:
                    data[row[0]] = row[1]
                else:
                    print(f"Skipping invalid row: {row}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    return data

def connect_to_graph(uri, auth):
    return Graph(uri, auth=auth)

def connect_to_bitcoin_rpc(user, password, host, port):
    return AuthServiceProxy(f"http://{user}:{password}@{host}:{port}")

def hybrid_clustering(data, initial_clusters=3, refined_clusters=2):
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    kmeans = KMeans(n_clusters=initial_clusters, n_init=10)
    initial_labels = kmeans.fit_predict(data_scaled)
    final_labels = np.copy(initial_labels)
    for k in range(initial_clusters):
        cluster_data = data_scaled[initial_labels == k]
        if len(cluster_data) > 1:
            agglom = AgglomerativeClustering(n_clusters=min(refined_clusters, len(cluster_data)), linkage='ward')
            refined_labels = agglom.fit_predict(cluster_data)
            final_labels[initial_labels == k] = refined_labels + k * refined_clusters
    return final_labels

def visualize_clustering(data, labels):
    df = pd.DataFrame(data, columns=['Frequency', 'AvgAmount', 'NumConnections'])
    df['Cluster'] = labels
    sns.pairplot(df, hue='Cluster', palette='deep')
    plt.suptitle('Hybrid Clustering Visualization', verticalalignment='top')
    plt.show()

def fetch_address_details(address_node):
    return {
        'address': address_node['address'],
        'total_received': address_node['total_received'],
        'total_sent': address_node['total_sent'],
        'balance': address_node['total_received'] - address_node['total_sent'],
        'num_transactions': address_node['num_transactions']
    }
def fetch_real_addresses(graph):
    matcher = NodeMatcher(graph)
    return list(matcher.match("Address"))

def process_addresses(graph, rpc_connection):
    addresses = fetch_real_addresses(graph)
    data = []
    for address_node in addresses:
        details = fetch_address_details(address_node)
        data.append([details['frequency'], details['avg_amount'], details['num_connections']])
    
    labels = hybrid_clustering(np.array(data))
    visualize_clustering(data, labels)

def main():
    graph = connect_to_graph(graph_uri, graph_auth)
    rpc_connection = connect_to_bitcoin_rpc(rpc_user, rpc_password, rpc_host, rpc_port)
    process_addresses(graph, rpc_connection)

if __name__ == "__main__":
    main()
