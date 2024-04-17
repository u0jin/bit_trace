import os
import json
import struct
from py2neo import Graph, Node, Relationship, NodeMatcher
from bitcoinrpc.authproxy import AuthServiceProxy
import hashlib
from decimal import Decimal
import csv
import logging
import sys 

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')



def save_HackerAddressesToDB(hackerAddresses_Dict):
    for address, report_type in hackerAddresses_Dict.items():
        hackerNode_Node = Node("HackerAddress", address=address, report_type=report_type)
        graph_Graph.merge(hackerNode_Node, "HackerAddress", "address")
        print(f"Hacker Address Node Created: {address} with Report Type: {report_type}")

# Neo4j 데이터베이스 연결 설정
graphUri_Str = "bolt://localhost:7687"
graphAuth_Tuple = ("neo4j", "tryit5826")
graph_Graph = Graph(graphUri_Str, auth=graphAuth_Tuple)
nodeMatcher_NodeMatcher = NodeMatcher(graph_Graph)

# Bitcoin RPC 연결 설정
rpcUser_Str = 'ujin'
rpcPassword_Str = '7749'
rpcHost_Str = '127.0.0.1'
rpcPort_Str = '8332'
rpcConnection_AuthServiceProxy = AuthServiceProxy(f"http://{rpcUser_Str}:{rpcPassword_Str}@{rpcHost_Str}:{rpcPort_Str}")
datFilePath_Str = '/home/ujin/.bitcoin/blocks'

# 입력 및 출력 디렉토리 설정
blockHashesFilePath_Str = '/home/ujin/Desktop/bitcoin/bit_trace/block_hashes.txt'
blockDetailsDir_Str = '/home/ujin/Desktop/bitcoin/bit_trace/blockDetail'
txDetailsDir_Str = '/home/ujin/Desktop/bitcoin/bit_trace/txDetail'
walletAddDir_Str = '/home/ujin/Desktop/bitcoin/bit_trace/walletAdd'
hackerAddressesCsv_Str = '/home/ujin/Desktop/bitcoin/bit_trace/hacker_addresses.csv'

# 수정된 부분: 이미 처리된 트랜잭션을 추적하기 위한 집합
processed_transactions = set()


# 수정된 부분: vout을 데이터베이스에 저장하는 함수 추가
def save_Vout_To_DB(txid, index, vout):
    logging.info(f"Attempting to save Vout {index} for TXID: {txid} to DB. Data: {vout}")
    txNode_Node = graph_Graph.nodes.match("Transaction", txid=txid).first()
    if txNode_Node:
        try:
            tx = graph_Graph.begin()  # 트랜잭션 시작
            voutNode_Node = Node("Vout", index=index, value=vout.get('value'), n=index, address=vout['scriptPubKey'].get('address'), type=vout['scriptPubKey'].get('type'))
            rel_Relationship = Relationship(txNode_Node, "HAS_VOUT", voutNode_Node)
            tx.create(voutNode_Node)
            tx.create(rel_Relationship)
            tx.commit()  # 트랜잭션 커밋
            logging.info(f"Vout {index} for TXID {txid} successfully saved to DB.")
        except Exception as e:
            logging.error(f"Error saving Vout {index} to DB for TXID {txid}: {e}")
            if tx:
                tx.rollback()  # 에러 시 롤백
            sys.exit(1)  # 에러 발생 시 종료 코드 1과 함께 종료
    else:
        logging.error(f"No transaction node found for TXID {txid}. Unable to save Vout.")
        sys.exit(1)  # 노드 미발견 시 종료 코드 1과 함께 종료



def load_HackerAddresses(csvFile_Str):
    hackerAddresses_Dict = {}
    try:
        with open(csvFile_Str, mode='r') as infile:
            reader = csv.reader(infile)
            next(reader)  # 헤더 스킵
            for row in reader:
                if len(row) == 2:
                    hackerAddresses_Dict[row[0]] = row[1]
                else:
                    print(f"Skipping invalid row: {row}")
    except FileNotFoundError:
        print(f"File not found: {csvFile_Str}")
    return hackerAddresses_Dict

def doubleSha256(header_Bytes):
    return hashlib.sha256(hashlib.sha256(header_Bytes).digest()).digest()

def extractAndSave_BlockHashes(datDirectory_Str):
    # 디렉토리 내 모든 .dat 파일에 대해 처리
    for filename in os.listdir(datDirectory_Str):
        if filename.endswith('.dat'):
            filePath_Str = os.path.join(datDirectory_Str, filename)
            try:
                with open(filePath_Str, 'rb') as file, open(blockHashesFilePath_Str, 'a') as output:
                    while True:
                        magic = file.read(4)
                        if not magic:
                            break
                        size = struct.unpack('<I', file.read(4))[0]
                        header = file.read(80)
                        hash = doubleSha256(header)[::-1].hex()
                        output.write(hash + '\n')
                        file.seek(size - 80, os.SEEK_CUR)
                print(f"Block hashes extracted and saved from {filePath_Str}.")
            except FileNotFoundError:
                print(f"File not found: {filePath_Str}")

def fetchAndSave_BlockDetails(blockHash_Str):
    try:
        block = rpcConnection_AuthServiceProxy.getblock(blockHash_Str)
        for key, value in block.items():
            if isinstance(value, Decimal):
                block[key] = float(value)
        
        block_data = {k: v for k, v in block.items() if k != 'hash'}
        blockNode_Node = Node("Block", hash=blockHash_Str, **block_data)
        graph_Graph.merge(blockNode_Node, "Block", "hash")
        print(f"Block details saved for block hash: {blockHash_Str}")
    except Exception as e:
        print(f"Error fetching block details for hash: {blockHash_Str}: {e}")

# 수정된 부분: 트랜잭션의 출력 값을 확인하는 함수 수정
def get_vout_for_txid(txid, txDetails):
    try:
        vouts = txDetails.get('vout', [])
        for index, vout in enumerate(vouts):
            print(f"Vout {index}: {vout}")
            save_Vout_To_DB(txid, index, vout)  # 수정: 올바른 vout 정보를 인자로 전달
    except Exception as e:
        print(f"Error fetching vout for TXID {txid}: {e}")



def fetchAndSave_TxDetails(txid_Str, hackerAddresses_Dict):
    try:
        if txid_Str in processed_transactions:
            return  # 이미 처리된 트랜잭션인 경우 중단

        txDetails = rpcConnection_AuthServiceProxy.getrawtransaction(txid_Str, True)
        processed_transactions.add(txid_Str)  # 처리된 트랜잭션으로 표시
        
        logging.info(f"Processing TXID: {txid_Str}")

        # 트랜잭션 노드 생성
        txNode_Node = nodeMatcher_NodeMatcher.match("Transaction", txid=txDetails['txid']).first()
        if txNode_Node is None:
            txNode_Node = Node("Transaction", txid=txDetails['txid'])
            graph_Graph.create(txNode_Node)

        # vout을 불러오는 부분 및 데이터베이스에 저장
        vouts = txDetails.get('vout', [])
        if vouts:
            for index, vout in enumerate(vouts):
                print(f"Vout {index}: {vout}")
                save_Vout_To_DB(txid_Str, index, vout)  # 각 vout 정보를 데이터베이스에 저장

                # vout에서 주소 추출 및 다음 트랜잭션 추적
                addresses = vout.get('scriptPubKey', {}).get('addresses', [])
                if addresses:
                    for address in addresses:
                        next_txs = rpcConnection_AuthServiceProxy.listunspent(0, 9999999, [address])
                        for next_tx in next_txs:
                            next_txid = next_tx['txid']
                            if next_txid not in processed_transactions:
                                fetchAndSave_TxDetails(next_txid, hackerAddresses_Dict)
        else:
            logging.info(f"No vout found for TXID: {txid_Str}")    

    except Exception as e:
        logging.error(f"Error fetching transaction details for TXID: {txid_Str}: {e}")




def extractAndSave_WalletAddresses(txDetailsFile_Str, depth=0, max_depth=10):
    try:
        if depth > max_depth:
            return  # 최대 깊이에 도달하면 중단

        with open(txDetailsFile_Str, 'r') as file:
            txDetails = json.load(file)
            txid = txDetails['txid']
            print(f"Processing Wallet Addresses for TXID: {txid}")

            txNode_Node = nodeMatcher_NodeMatcher.match("Transaction", txid=txid).first()
            if txNode_Node is not None:
                # 수정된 부분: 올바른 depth 값 전달
                print(f"Depth: {depth}")
                for vout in txDetails.get('vout', []):
                    addresses = vout.get('scriptPubKey', {}).get('addresses', [])
                    for address in addresses:
                        addressNode_Node = nodeMatcher_NodeMatcher.match("Address", address=address).first()
                        if addressNode_Node is None:
                            addressNode_Node = Node("Address", address=address)
                            graph_Graph.create(addressNode_Node)
                            print(f"Created Address Node: {address}")
                        rel_Relationship = Relationship(txNode_Node, "OUTPUTS", addressNode_Node)
                        graph_Graph.merge(rel_Relationship)
                        print(f"Created Relationship: Transaction {txid} -> Address {address}")

                        # 주소에서 출력된 다음 트랜잭션 추적 (재귀 호출)
                        next_txs = rpcConnection_AuthServiceProxy.listunspent(0, 9999999, [address])
                        for next_tx in next_txs:
                            next_txid = next_tx['txid']
                            # 수정된 부분: 올바른 파일 경로 전달
                            extractAndSave_WalletAddresses(os.path.join(txDetailsDir_Str, f"{next_txid}_wallet_address.json"), depth + 1, max_depth)

            print(f"Wallet addresses processed for TX details file: {txDetailsFile_Str}")
    except FileNotFoundError:
        print(f"File not found: {txDetailsFile_Str}")

def match_HackerAddresses(walletAddFile_Str, hackerAddresses_Dict):
    try:
        with open(walletAddFile_Str, 'r') as file:
            walletData = json.load(file)
            txid = walletData['txid']
            print(f"Matching Hacker Addresses for TXID: {txid}")

            txNode_Node = nodeMatcher_NodeMatcher.match("Transaction", txid=txid).first()
            if txNode_Node is not None:
                # 수정된 부분: 트랜잭션의 출력 값을 확인하도록 수정
                get_vout_for_txid(txid, walletData)

                for vout in walletData.get('vout', []):
                    addresses = vout.get('scriptPubKey', {}).get('addresses', [])
                    for address in addresses:
                        if address in hackerAddresses_Dict:
                            reportType_Str = hackerAddresses_Dict[address]
                            hackerNode_Node = nodeMatcher_NodeMatcher.match("HackerAddress", address=address).first()
                            if hackerNode_Node is None:
                                hackerNode_Node = Node("HackerAddress", address=address, report_type=reportType_Str)
                                graph_Graph.create(hackerNode_Node)
                                print(f"Created Hacker Address Node: {address}")
                            rel_Relationship = Relationship(txNode_Node, "OUTPUTS_TO_HACKER", hackerNode_Node)
                            graph_Graph.merge(rel_Relationship)
                            print(f"Created Relationship: Transaction {txid} -> Hacker Address {address}")
                            print(f"Hacker Address Report Type: {reportType_Str}")  # 해커 주소에 대한 보고서 유형 출력
                        else:
                            print(f"No hacker address found for address: {address}")

        print(f"Hacker address matching completed for wallet address file: {walletAddFile_Str}")
    except FileNotFoundError:
        print(f"File not found: {walletAddFile_Str}")

def check_DatabaseConnection(graph_Graph):
    try:
        graph_Graph.run("MATCH (n) RETURN n LIMIT 1")
        logging.info("Database connection successful.")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False
    

def main():
    setup_logging()

    # 데이터베이스 연결 상태 즉시 확인
    if not check_DatabaseConnection(graph_Graph):
        return

    # 해커 주소 목록 로드
    hackerAddresses_Dict = load_HackerAddresses(hackerAddressesCsv_Str)
    logging.info("Hacker addresses loaded.")

    # 블록 해시 파일에서 블록 해시 목록 로드
    try:
        with open(blockHashesFilePath_Str, 'r') as file:
            blockHashes_List = file.read().splitlines()
            logging.info("Block hashes loaded.")
    except FileNotFoundError:
        logging.error(f"File not found: {blockHashesFilePath_Str}")
        return

    # 각 트랜잭션에 대해 주소 데이터 처리
    for txDetailsFile in os.listdir(txDetailsDir_Str):
        txid = txDetailsFile.split('_')[0]  # 파일 이름에서 txid 추출
        txDetailsFilePath_Str = os.path.join(txDetailsDir_Str, txDetailsFile)
        if txDetailsFilePath_Str.endswith('_wallet_address.json'):
            logging.info(f"Processing wallet addresses for file: {txDetailsFile}")
            extractAndSave_WalletAddresses(txDetailsFilePath_Str)

    # 트랜잭션에 대한 정보 가져오기
    for txid in blockHashes_List:
        try:
            fetchAndSave_TxDetails(txid, hackerAddresses_Dict)
        except Exception as e:
            logging.error(f"Error processing TXID {txid}: {e}")

    # 해커 주소 매칭 및 저장
    for walletAddFile in os.listdir(walletAddDir_Str):
        txid = walletAddFile.split('_')[0]  # 파일 이름에서 txid 추출
        walletAddFilePath_Str = os.path.join(walletAddDir_Str, walletAddFile)
        if walletAddFilePath_Str.endswith('_wallet_address.json'):
            logging.info(f"Matching hacker addresses for file: {walletAddFile}")
            try:
                with open(walletAddFilePath_Str, 'r') as file:
                    walletData = json.load(file)
                    logging.info(f"Processing TXID: {txid}")
                    match_HackerAddresses(walletAddFilePath_Str, hackerAddresses_Dict)
            except Exception as e:
                logging.error(f"Error processing wallet address file {walletAddFilePath_Str}: {e}")

    logging.info("Address processing completed.")

if __name__ == "__main__":
    main()