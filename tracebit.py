from py2neo import Graph, NodeMatcher, RelationshipMatcher

def trace_hacker_funds(hacker_address, depth_limit=3):
    graph = Graph("bolt://localhost:7687", auth=("ujin", "tryit5826"))
    node_matcher = NodeMatcher(graph)
    relationship_matcher = RelationshipMatcher(graph)

    # 해커 주소 노드 찾기
    hacker_node = node_matcher.match("HackerAddress", address=hacker_address).first()

    if hacker_node is None:
        print(f"No hacker address found for: {hacker_address}")
        return

    # 추적 결과를 저장할 리스트 초기화
    trace_result = []

    # 추적 함수
    def trace_transactions(node, depth=0, visited=None):
        if visited is None:
            visited = set()

        if node in visited:
            return

        visited.add(node)
        trace_result.append(node)

        # 최대 추적 깊이 제한
        if depth >= depth_limit:
            return

        # 연결된 트랜잭션 관계 찾기
        tx_relationships = relationship_matcher.match(nodes=[node], r_type="OUTPUTS")

        for rel in tx_relationships:
            tx_node = rel.end_node
            trace_result.append(rel)
            trace_result.append(tx_node)

            # 트랜잭션에서 연결된 주소 관계 찾기
            address_relationships = relationship_matcher.match(nodes=[tx_node], r_type="OUTPUTS")

            for rel2 in address_relationships:
                address_node = rel2.end_node
                trace_transactions(address_node, depth + 1, visited)

    # 해커 주소 노드에서 추적 시작
    trace_transactions(hacker_node)

    # 추적 결과 출력 또는 저장
    print(f"Trace Result for Hacker Address: {hacker_address}")
    for item in trace_result:
        if isinstance(item, dict):
            print(f"Node: {item}")
        else:
            print(f"Relationship: {item}")

    # 추적 결과를 파일로 저장
    with open(f"trace_result_{hacker_address}.txt", "w") as file:
        for item in trace_result:
            file.write(str(item) + "\n")

    print(f"Trace result saved to file: trace_result_{hacker_address}.txt")

# 해커 주소 리스트
hacker_addresses = [
    # 예시로 하나만 넣어봄
    "155Yv6Hmzs5RT8j6uZAzfWzecvV9FDyu6k"

]

# 해커 주소별로 자금 추적
for address in hacker_addresses:
    print("------------------------")
    print(f"Tracing funds for hacker address: {address}")
    trace_hacker_funds(address)