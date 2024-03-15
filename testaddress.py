import json

def check_address_in_file(json_file, target_address):
    # 결과를 저장할 리스트 초기화
    matching_transactions = []

    # JSON 파일을 열고 데이터를 로드
    with open(json_file, 'r') as file:
        data = json.load(file)

    # 데이터 항목을 반복하여 주소 검사
    for transaction_id, tx_info in data.items():
        if tx_info['address'] == target_address:
            matching_transactions.append(transaction_id)

    # 결과 반환
    return matching_transactions

# JSON 파일 경로와 검사하려는 주소
json_file_path = '/home/ujin/Desktop/bitcoin/bit_trace/consolidated_data.json'  # 실제 파일 경로로 대체
target_address = '157PiPgqphedUvrco3mKU3Xoof7yzhj9pW'  # 실제 검사하려는 주소로 대체

# 함수 호출 및 결과 출력
matching_txs = check_address_in_file(json_file_path, target_address)
if matching_txs:
    print(f"The address {target_address} is found in the following transactions:")
    for tx in matching_txs:
        print(tx)
else:
    print(f"The address {target_address} was not found in the file.")
