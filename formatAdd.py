import os
import json

# 입력 및 출력 디렉토리 설정
output_dir = '/home/ujin/Desktop/bitcoin/bit_trace/walletAdd'

# 각 트랜잭션에 대한 고유 정보를 저장할 파일
output_file = 'consolidated_data.json'

# 집계된 데이터를 저장할 딕셔너리 초기화
consolidated_data = {}

# 출력 디렉토리 내의 모든 파일을 순회
for filename in os.listdir(output_dir):
    if filename.endswith('_details.json'):  # 파일명 형식 확인
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'r') as f:
            data = json.load(f)
            txid = data['txid']
            block_hash = data['details']['blockhash']  # blockhash 위치 수정

            vouts = data['details'].get('vout', [])  # vout 위치 수정
            for i, vout in enumerate(vouts):
                address = vout['scriptPubKey'].get('address')  # 주소 추출 방식 수정
                if address:
                    unique_id = f"{txid}-{i}"
                    consolidated_data[unique_id] = {
                        'block_hash': block_hash,
                        'txid': txid,
                        'address': address
                    }

with open(output_file, 'w') as f:
    json.dump(consolidated_data, f, indent=4)

print(f"Consolidated data saved to {output_file}")