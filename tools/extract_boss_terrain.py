"""Decode original boss-entry scroll RAM writes (fixed routine 5DC6)."""
def extract(source, level):
    source.expect(0, 0x5dc6, '3aa1f3875f160021908d195e2356eb7ecd6f03235e235613237ab3c81b7e1223137e1223c3da5d')
    pointer = source.word(4, 0x8d90 + level * 2)
    page = source.read(4, pointer, 1)[0]
    assert page < 4
    pointer += 1
    writes = {}
    for _ in range(256):
        address = source.word(4, pointer)
        if address == 0xffff:
            return writes
        assert 0xc000 <= address < 0xcfff and address % 2 == 0
        offset = page * 4096 + address - 0xc000
        assert offset not in writes
        writes[offset] = source.word(4, pointer + 2)
        pointer += 4
    raise ValueError('Unterminated boss terrain patch')
