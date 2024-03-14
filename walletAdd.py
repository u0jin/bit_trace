import os
import json
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# 트랜잭션에 대한 더 자세한 정보
# saveTx.py 보다 좀더 세부적인 내용 저장
# 자금이 얼마나 이동되는지 확인가능 

rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'
tx_detail_dir = '/home/ujin/Desktop/bitcoin/bit_trace/txDetail'
output_dir = '/home/ujin/Desktop/bitcoin/bit_trace/txDetail/walletAdd'

rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

def process_tx_files():
    for filename in os.listdir(tx_detail_dir):
        with open(os.path.join(tx_detail_dir, filename), 'r') as file:
            txid = filename.replace('_details.json', '')  

            try:
                raw_tx = rpc_connection.getrawtransaction(txid, True)
                raw_tx['txid'] = txid  

                output_file = os.path.join(output_dir, f"{txid}_wallet_address.json")
                with open(output_file, 'w') as outfile:
                    json.dump(raw_tx, outfile, indent=4, default=str)
                print(f"Transaction details including TXID saved for {txid}")
                
            except JSONRPCException as e:
                print(f"An error occurred fetching details for {txid}: {e}")

if __name__ == '__main__':
    process_tx_files()
