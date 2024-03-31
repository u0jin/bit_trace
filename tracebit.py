import pandas as pd
from py2neo import Graph, NodeMatcher, RelationshipMatcher

def trace_hacker_funds(hacker_addresses_csv):
    # 네오4j 데이터베이스 연결 설정
    graph = Graph("bolt://localhost:7687", auth=("ujin", "tryit5826"))
    node_matcher = NodeMatcher(graph)
    relationship_matcher = RelationshipMatcher(graph)

    # CSV 파일에서 해커 주소 목록을 읽어옵니다.
    df = pd.read_csv(hacker_addresses_csv)
    
    # 지갑 주소별로 거래 ID를 그룹화합니다.
    grouped_transactions = df.groupby('hacker_address')['tx_id'].apply(list).reset_index()
    
    for index, row in grouped_transactions.iterrows():
        hacker_address = row['hacker_address']
        transaction_ids = row['tx_id']
        
        # 해커 주소 노드를 찾습니다.
        hacker_node = node_matcher.match("HackerAddress", address=hacker_address).first()
        if not hacker_node:
            print(f"No hacker address found for: {hacker_address}")
            continue
        
        print(f"Tracing funds for hacker address: {hacker_address}")
        
        # 각 거래 ID에 대해 자금 흐름을 분석합니다.
        for tx_id in transaction_ids:
            # 해당 거래 ID에 대한 노드를 찾습니다.
            tx_node = node_matcher.match("Transaction", tx_id=tx_id).first()
            if not tx_node:
                print(f"No transaction found for: {tx_id}")
                continue
            
            # 거래에서 출력된 주소를 찾습니다.
            address_relationships = relationship_matcher.match(nodes=[tx_node], r_type="OUTPUTS")
            for rel in address_relationships:
                # 출력된 주소 노드와의 관계를 출력합니다.
                address_node = rel.end_node
                print(f"Transaction {tx_id} outputs to address: {address_node['address']}")
                
                # 추가 분석을 위한 코드를 여기에 추가할 수 있습니다.
                
if __name__ == "__main__":
    trace_hacker_funds("vout_matching_transactions.csv")
