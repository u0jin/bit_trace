from bitcoinrpc.authproxy import AuthServiceProxy
import json
import os

# Configuration for your node
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'

# Path to the file containing block hashes and directory for output
block_hashes_file = '/home/ujin/Desktop/bitcoin/bit_trace/block_hashes.txt'
output_dir = '/home/ujin/Desktop/bitcoin/bit_trace/blockDetail'

def save_block_details(block, block_hash):
    output_file = os.path.join(output_dir, f'block_{block_hash}_details.txt')
    with open(output_file, 'w') as f:
        json.dump(block, f, indent=4, default=str)
    print(f"Block details saved to {output_file}")

def main():
    rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")
    with open(block_hashes_file, 'r') as file:
        block_hashes = [line.strip() for line in file.readlines()]

    for block_hash in block_hashes:
        block = rpc_connection.getblock(block_hash)
        save_block_details(block, block_hash)

if __name__ == '__main__':
    main()
