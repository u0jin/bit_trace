from bitcoinrpc.authproxy import AuthServiceProxy
import json
import os

# 트랜잭션의 기본정보 저장
# [주요 필드]
# txid: 트랜잭션의 고유 식별자
# vin: 이 트랜잭션의 입력 트랜잭션(들)에 대한 정보
# vout: 이 트랜잭션의 출력(보낸 비트코인 주소와 금액)에 대한 정보
# blockhash: 이 트랜잭션이 포함된 블록의 해시값
# confirmations: 이 트랜잭션이 받은 확인 횟수
# time, blocktime: 트랜잭션이 블록에 포함된 시간

rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'

block_details_dir = '/home/ujin/Desktop/bitcoin/bit_trace/blockDetail'
tx_details_dir = '/home/ujin/Desktop/bitcoin/bit_trace/txDetail'

def fetch_and_save_tx_details(txid, rpc_connection):
    try:
        tx_details = rpc_connection.getrawtransaction(txid, True)
        tx_details_file = os.path.join(tx_details_dir, f"{txid}.json")
        with open(tx_details_file, 'w') as f:
            json.dump(tx_details, f, indent=4, default=str)
        print(f"Saved transaction details for {txid}")
    except Exception as e:
        print(f"Error fetching transaction {txid}: {e}")

def process_block_files():
    rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")
    for filename in os.listdir(block_details_dir):
        with open(os.path.join(block_details_dir, filename), 'r') as f:
            block = json.load(f)
            for txid in block.get('tx', []):
                # Skip the genesis block's coinbase transaction
                if txid != '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b':
                    fetch_and_save_tx_details(txid, rpc_connection)

if __name__ == '__main__':
    process_block_files()
