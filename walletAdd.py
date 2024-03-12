import os
import json
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'
tx_detail_dir = '/home/ujin/Desktop/bitcoin/bit_trace/txDetail'
output_dir = '/home/ujin/Desktop/bitcoin/bit_trace/walletAdd'

# Create a connection to the Bitcoin node
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

def process_tx_files():
    for filename in os.listdir(tx_detail_dir):
        txid = filename.replace('.json', '')  # Remove '.json' extension to get the correct TXID
        try:
            # Fetch the raw transaction data
            raw_tx = rpc_connection.getrawtransaction(txid, True)
            
            # Save the transaction details along with TXID to the output directory
            output_file = os.path.join(output_dir, f"{txid}_details.json")
            with open(output_file, 'w') as outfile:
                json.dump({'txid': txid, 'details': raw_tx}, outfile, indent=4, default=str)
            print(f"Transaction details saved for {txid}")
            
        except JSONRPCException as e:
            print(f"An error occurred fetching details for {txid}: {e}")

if __name__ == '__main__':
    process_tx_files()
