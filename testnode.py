from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
rpc_user = 'ujin'
rpc_password = '7749'
rpc_host = '127.0.0.1'
rpc_port = '8332'

# Known transaction ID (replace with a real TXID from your blockchain)
txid = '19e66f833cad8490beb92f231295a99f972641b533367e5497aade1891bbf9a5'

# Create a connection to the Bitcoin node
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

try:
    # Fetch the raw transaction data
    raw_tx = rpc_connection.getrawtransaction(txid, True)
    print("Transaction details:", raw_tx)
except JSONRPCException as e:
    print(f"An error occurred: {e}")
