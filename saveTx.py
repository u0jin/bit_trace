from bitcoinrpc.authproxy import AuthServiceProxy
import json
import os

# Configuration for your node
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'

# Directory containing block detail files and directory for transaction details output
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
