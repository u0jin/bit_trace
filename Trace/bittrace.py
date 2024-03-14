import json
import csv

def extract_addresses_and_amounts(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
        addresses = []
        amounts = []
        details = data.get('details', {})
        for output in details.get('vout', []):
            address = output.get('scriptPubKey', {}).get('address')
            value = output.get('value')
            if address and value:
                addresses.append(address)
                amounts.append(float(value))
    return addresses, amounts

def save_addresses_and_amounts(addresses, amounts, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['address', 'amount'])
        for address, amount in zip(addresses, amounts):
            writer.writerow([address, amount])

def load_addresses_and_amounts(input_file):
    addresses = []
    amounts = []
    with open(input_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            addresses.append(row[0])
            amounts.append(float(row[1]))
    return addresses, amounts

json_file = '/home/ujin/Desktop/bitcoin/bit_trace/Trace/hackerMatch/darknet market/eb5b761c7380ed4c6adf688f9e5ab94953dcabeda47d9eeabd77261902fccccf_details.json'
output_file = 'addresses_and_amounts.csv'

addresses, amounts = extract_addresses_and_amounts(json_file)

save_addresses_and_amounts(addresses, amounts, output_file)

loaded_addresses, loaded_amounts = load_addresses_and_amounts(output_file)

