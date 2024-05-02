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

def connect_to_graph(uri, auth):
    return Graph(uri, auth=auth)

def connect_to_bitcoin_rpc(user, password, host, port):
    return AuthServiceProxy(f"http://{user}:{password}@{host}:{port}")

def address_reuse_heuristic(graph): # 어떤 주소가 자주 사용되었는지 파악가능
    matcher = NodeMatcher(graph)
    addresses = list(matcher.match("Address"))
    reuse_map = {}
    for address in addresses:
        transactions = list(graph.relationships(address, "PARTICIPATES_IN"))
        if len(transactions) > 1:
            reuse_map[address['address']] = True # 두번 이상 사용된다면 true로 표시
        else:
            reuse_map[address['address']] = False # 한번 사용
    return reuse_map

def hybrid_clustering(data, initial_clusters=3, refined_clusters=2, reuse_map=None):
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data) # 균등 분산
    kmeans = KMeans(n_clusters=initial_clusters, n_init=10) # 몇개의 큰 그룹으로 정렬
    initial_labels = kmeans.fit_predict(data_scaled)
    final_labels = np.copy(initial_labels)
    for k in range(initial_clusters):
        cluster_data = data_scaled[initial_labels == k]
        if len(cluster_data) > 1: # 더 작은 그룹을 만들기 위함
            agglom = AgglomerativeClustering(n_clusters=min(refined_clusters, len(cluster_data)), linkage='ward')
            refined_labels = agglom.fit_predict(cluster_data)
            for idx, label in enumerate(refined_labels):
                address = data[initial_labels == k][idx][0]
                if reuse_map[address]:
                    final_labels[initial_labels == k] = refined_labels + k * refined_clusters
    return final_labels

def visualize_clustering(data, labels):
    df = pd.DataFrame(data, columns=['Address', 'TotalReceived', 'TotalSent', 'Balance', 'NumTransactions'])
    df['Cluster'] = labels
    sns.pairplot(df, vars=['TotalReceived', 'TotalSent', 'Balance', 'NumTransactions'], hue='Cluster', palette='deep')
    plt.suptitle('Hybrid Clustering Visualization', verticalalignment='top')
    plt.show()

def process_addresses(graph, rpc_connection):
    addresses = fetch_real_addresses(graph)
    data = []
    reuse_map = address_reuse_heuristic(graph)
    for address_node in addresses:
        details = fetch_address_details(address_node)
        data.append([details['address'], details['total_received'], details['total_sent'], details['balance'], details['num_transactions']])
    
    labels = hybrid_clustering(np.array(data), reuse_map=reuse_map)
    visualize_clustering(data, labels)

def main():
    graph = connect_to_graph(graph_uri, graph_auth)
    rpc_connection = connect_to_bitcoin_rpc(rpc_user, rpc_password, rpc_host, rpc_port)
    process_addresses(graph, rpc_connection)

if __name__ == "__main__":
    main()
