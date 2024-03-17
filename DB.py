import os
import json
import csv
import struct
from py2neo import Graph, Node, Relationship
from bitcoinrpc.authproxy import AuthServiceProxy
import hashlib


# Neo4j 데이터베이스 연결 설정
graph = Graph("bolt://localhost:7687", auth=("neo4j", "your_password"))

# Bitcoin RPC 연결 설정
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")
dat_file_path_Str = '/home/ujin/.bitcoin/blocks/blk00000.dat'

# 입력 및 출력 디렉토리 설정
block_hashes_file = '/home/ujin/Desktop/bitcoin/bit_trace/block_hashes.txt'
block_details_dir = '/home/ujin/Desktop/bitcoin/bit_trace/blockDetail'
tx_details_dir = '/home/ujin/Desktop/bitcoin/bit_trace/txDetail'
wallet_add_dir = '/home/ujin/Desktop/bitcoin/bit_trace/walletAdd'
hacker_addresses_csv = '/home/ujin/Desktop/bitcoin/bit_trace/hacker_addresses.csv'

# 해커 주소 로드 함수
def load_hacker_addresses(csv_file):
    hacker_addresses = []
    with open(csv_file, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            hacker_addresses.append(row['hacker_address'])
    return hacker_addresses

def double_sha256(header):
    return hashlib.sha256(hashlib.sha256(header).digest()).digest()

# 블록 해시 추출 및 저장 함수
def extract_and_save_block_hashes():
    with open(dat_file_path_Str, 'rb') as file, open(block_hashes_file, 'w') as output:
        while True:
            magic = file.read(4)
            if not magic:
                break  
            size = struct.unpack('<I', file.read(4))[0]
            header = file.read(80)
            hash = double_sha256(header)[::-1].hex()
            output.write(hash + '\n')
            _ = file.read(size - 80)

    print("Block hashes extracted and saved.")

# 블록 상세 정보 가져오기 및 저장 함수
def fetch_and_save_block_details(block_hash):
    block = rpc_connection.getblock(block_hash)
    block_node = Node("Block", hash=block_hash)
    block_node.update(block)
    graph.merge(block_node, "Block", "hash")

    print(f"Block details saved for block hash: {block_hash}")

# 트랜잭션 상세 정보 가져오기 및 저장 함수
def fetch_and_save_tx_details(txid):
    try:
        tx_details = rpc_connection.getrawtransaction(txid, True)
        tx_node = Node("Transaction", txid=txid)
        tx_node.update(tx_details)
        graph.merge(tx_node, "Transaction", "txid")

        print(f"Transaction details saved for TXID: {txid}")
    except Exception as e:
        print(f"Error fetching transaction details for TXID: {txid}")

# 출금 지갑 주소 추출 및 저장 함수
def extract_and_save_wallet_addresses(tx_details_file):
    with open(tx_details_file, 'r') as f:
        data = json.load(f)
        txid = data['txid']
        vouts = data.get('vout', [])
        for vout in vouts:
            if 'scriptPubKey' in vout and 'addresses' in vout['scriptPubKey']:
                addresses = vout['scriptPubKey']['addresses']
                for address in addresses:
                    address_node = Node("Address", address=address)
                    graph.merge(address_node, "Address", "address")
                    tx_node = graph.nodes.match("Transaction", txid=txid).first()
                    if tx_node:
                        graph.create(Relationship(tx_node, "OUTPUTS", address_node))

    print(f"Wallet addresses extracted and saved for TX details file: {tx_details_file}")

# 해커 주소 일치 여부 확인 함수
def match_hacker_addresses(wallet_add_file, hacker_addresses):
    with open(wallet_add_file, 'r') as f:
        data = json.load(f)
        txid = data['txid']
        vouts = data.get('vout', [])
        for vout in vouts:
            if 'scriptPubKey' in vout and 'addresses' in vout['scriptPubKey']:
                addresses = vout['scriptPubKey']['addresses']
                for address in addresses:
                    if address in hacker_addresses:
                        hacker_node = Node("HackerAddress", address=address)
                        graph.merge(hacker_node, "HackerAddress", "address")
                        tx_node = graph.nodes.match("Transaction", txid=txid).first()
                        if tx_node:
                            graph.create(Relationship(tx_node, "OUTPUTS", hacker_node))
                        print(f"Hacker address match found: {address} in TXID: {txid}")

    print(f"Hacker address matching completed for wallet address file: {wallet_add_file}")
# 메인 함수
def main():
    # 해커 주소 로드
    hacker_addresses = load_hacker_addresses(hacker_addresses_csv)

    # 블록 해시 추출 및 저장
    extract_and_save_block_hashes()

    # 블록 상세 정보 가져오기 및 저장
    with open(block_hashes_file, 'r') as file:
        block_hashes = [line.strip() for line in file.readlines()]
    for block_hash in block_hashes:
        fetch_and_save_block_details(block_hash)

    # 트랜잭션 상세 정보 가져오기 및 저장
    for filename in os.listdir(block_details_dir):
        with open(os.path.join(block_details_dir, filename), 'r') as f:
            block = json.load(f)
            for txid in block.get('tx', []):
                if txid != '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b':
                    fetch_and_save_tx_details(txid)

    # 출금 지갑 주소 추출 및 저장
    for filename in os.listdir(tx_details_dir):
        tx_details_file = os.path.join(tx_details_dir, filename)
        extract_and_save_wallet_addresses(tx_details_file)

    # 해커 주소 일치 여부 확인
    for filename in os.listdir(wallet_add_dir):
        wallet_add_file = os.path.join(wallet_add_dir, filename)
        match_hacker_addresses(wallet_add_file, hacker_addresses)

if __name__ == "__main__":
    main()