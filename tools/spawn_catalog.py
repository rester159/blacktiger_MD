"""Read constructor identities directly from the supplied spawn tables."""
import struct

def constructors(source):
    entries = {}
    for level in range(8):
        root = source.word(None, 0x1e07 + level*2)
        pointers = struct.unpack('<33H', source.read(5, root, 66))
        for pointer in pointers[1:]:
            for _ in range(128):
                raw = source.read(5, pointer, 8)
                if raw[:2] == b'\xff\xff':
                    break
                x, y, address, bank, persistent = struct.unpack('<HHHBB', raw)
                if bank > 7 or address < 0x100 or address >= 0xc000:
                    break
                pointer += 8
                if address in (0x7138, 0x6f71):
                    continue
                key = (bank if address >= 0x8000 else 0, address)
                if key not in entries:
                    entries[key] = dict(id=len(entries), bank=key[0], address=address)
    return list(entries.values())
