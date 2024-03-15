import csv
import json
import os

def load_hacker_addresses(csv_file):
    hacker_addresses = []
    with open(csv_file, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            hacker_addresses.append(row['hacker_address'])
    return hacker_addresses


def check_address_in_consolidated_data(consolidated_data, hacker_addresses):
    matching_transactions = []
    for unique_id, tx_info in consolidated_data.items():
        address = tx_info['address']
        if address in hacker_addresses:
            matching_transactions.append((tx_info['txid'], address))
    return matching_transactions


def process_transactions(consolidated_data_file, hacker_addresses, output_dir):
    with open(consolidated_data_file, 'r') as f:
        consolidated_data = json.load(f)

    matching_transactions = check_address_in_consolidated_data(consolidated_data, hacker_addresses)

    with open(os.path.join(output_dir, 'vout_matching_transactions.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tx_id', 'hacker_address'])
        writer.writerows(matching_transactions)


hacker_addresses_csv = '/home/ujin/Desktop/bitcoin/bit_trace/hacker_addresses.csv'
consolidated_data_json = '/home/ujin/Desktop/bitcoin/bit_trace/consolidated_data.json'  # 경로 수정
hacker_match_dir = '/home/ujin/Desktop/bitcoin/bit_trace/hackerMatch'

hacker_addresses = load_hacker_addresses(hacker_addresses_csv)
process_transactions(consolidated_data_json, hacker_addresses, hacker_match_dir)
