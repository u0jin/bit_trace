from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'

# Known transaction ID (replace with a real TXID from your blockchain)
txid = '013b1bc7b6bb1318c4cd2262f33a6ccd0470718c91266f8736f8b59bfc166ada'

# Create a connection to the Bitcoin node
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

try:
    # Fetch the raw transaction data
    raw_tx = rpc_connection.getrawtransaction(txid, True)
    print("Transaction details:", raw_tx)
except JSONRPCException as e:
    print(f"An error occurred: {e}")
