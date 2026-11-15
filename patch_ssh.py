"""Generate a patched copy of a compatible WindTerm SSH DLL."""

import argparse
import pathlib
import struct


USERNAME_BUFFER_SIZE = 4096
IMAGE_SCN_MEM_EXECUTE = 0x20000000
EXPECTED_HELPER = bytes.fromhex(
    '40 53 48 83 ec 20 48 8d 54 24 30 c7 44 24 30 00 00 00 00 '
    '33 c9 ff 15 25 7c 02 00 8b 4c 24 30 ff 15 23 7f 02 00'
)


def find_username_helper(data, pe_offset):
    section_count = struct.unpack_from('<H', data, pe_offset + 6)[0]
    optional_header_size = struct.unpack_from('<H', data, pe_offset + 20)[0]
    section_table = pe_offset + 24 + optional_header_size
    if optional_header_size < 68 or section_table + section_count * 40 > len(data):
        raise ValueError('Invalid PE section table or optional header.')

    match = -1
    for index in range(section_count):
        section_offset = section_table + index * 40
        characteristics = struct.unpack_from('<I', data, section_offset + 36)[0]
        if not characteristics & IMAGE_SCN_MEM_EXECUTE:
            continue

        raw_size, raw_offset = struct.unpack_from('<II', data, section_offset + 16)
        raw_end = raw_offset + raw_size
        if raw_end > len(data):
            raise ValueError('Invalid PE executable section.')

        start = data.find(EXPECTED_HELPER, raw_offset, raw_end)
        if start == -1:
            continue
        if match != -1 or data.find(EXPECTED_HELPER, start + 1, raw_end) != -1:
            raise ValueError('Multiple matches for the username helper.')
        match = start

    if match == -1:
        raise ValueError('The known username helper code was not found.')
    return match


def update_pe_checksum(data, pe_offset):
    checksum_offset = pe_offset + 24 + 64
    struct.pack_into('<I', data, checksum_offset, 0)
    total = 0
    for offset in range(0, len(data), 2):
        word = data[offset]
        if offset + 1 < len(data):
            word |= data[offset + 1] << 8
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    struct.pack_into('<I', data, checksum_offset, (total + len(data)) & 0xFFFFFFFF)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()

    try:
        data = bytearray(args.input.read_bytes())
        pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
        if data[:2] != b'MZ' or data[pe_offset:pe_offset + 6] != b'PE\0\0\x64\x86':
            raise ValueError('Expected a Windows x86-64 PE file.')
        start = find_username_helper(data, pe_offset)

        # Initialize DWORD size to 4096 and skip GetUserNameA(NULL, &size).
        struct.pack_into('<I', data, start + 15, USERNAME_BUFFER_SIZE)
        data[start + 21:start + 27] = b'\x90' * 6
        update_pe_checksum(data, pe_offset)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as output:
            output.write(data)
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f'Error: {error}\n')

    print(f'Generated {args.output}')


if __name__ == '__main__':
    main()
