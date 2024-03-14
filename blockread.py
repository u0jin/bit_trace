import struct
import hashlib

def read_varint(f):
    varint = ord(f.read(1))
    if varint < 0xfd:
        return varint
    elif varint == 0xfd:
        return struct.unpack('<H', f.read(2))[0]
    elif varint == 0xfe:
        return struct.unpack('<I', f.read(4))[0]
    elif varint == 0xff:
        return struct.unpack('<Q', f.read(8))[0]

def double_sha256(header):
    return hashlib.sha256(hashlib.sha256(header).digest()).digest()

def extract_block_hashes(dat_file_path, output_file_path):
    with open(dat_file_path, 'rb') as file, open(output_file_path, 'w') as output:
        while True:
            magic = file.read(4)
            if not magic:
                break  
            size = struct.unpack('<I', file.read(4))[0]
            header = file.read(80)  # Block header
            hash = double_sha256(header)[::-1].hex()  # Reverse hash for correct endianness
            output.write(hash + '\n')
            _ = file.read(size - 80)  # Skip the rest of the block

dat_file_path_Str = '/home/ujin/.bitcoin/blocks/blk00000.dat'
output_file_path_Str = '/home/ujin/Desktop/bitcoin/bit_trace/block_hashes.txt'
extract_block_hashes(dat_file_path_Str, output_file_path_Str)
