import csv
import json
import os

# Load hacker addresses from CSV
def load_hacker_addresses(csv_file):
    hacker_addresses = []
    with open(csv_file, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            hacker_addresses.append(row['hacker_address'])
    return hacker_addresses

# Check if transaction involves a hacker address

def check_transaction(tx_details, hacker_addresses):
    with open(tx_details, 'r') as f:
        tx_data = json.load(f)
        for output in tx_data.get('details', {}).get('vout', []):
            if 'address' in output.get('scriptPubKey', {}):
                address = output['scriptPubKey']['address']                
                if address in hacker_addresses:
                    return True, address
    return False, None


# Main function to process transactions
def process_transactions(tx_dir, hacker_addresses, output_dir):
    matching_transactions = []
    for filename in os.listdir(tx_dir):
        tx_path = os.path.join(tx_dir, filename)
        match, address = check_transaction(tx_path, hacker_addresses)
        if match:
            tx_id = filename.replace('_details.json', '')
            matching_transactions.append((tx_id, address))

    # Save matching transactions
    with open(os.path.join(output_dir, 'matching_transactions.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tx_id', 'hacker_address'])
        writer.writerows(matching_transactions)

hacker_addresses_csv = '/home/ujin/Desktop/bitcoin/bit_trace/hacker_addresses.csv'
wallet_add_dir = '/home/ujin/Desktop/bitcoin/bit_trace/walletAdd'
hacker_match_dir = '/home/ujin/Desktop/bitcoin/bit_trace/hackerMatch'

hacker_addresses = load_hacker_addresses(hacker_addresses_csv)
process_transactions(wallet_add_dir, hacker_addresses, hacker_match_dir)
