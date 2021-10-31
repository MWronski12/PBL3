def string_to_bitlist(s):
    ords = [ord(char) for char in s]
    shifts = (7, 6, 5, 4, 3, 2, 1, 0)
    return [(o >> shift) & 1 for o in ords for shift in shifts]

def bitlist_to_chars(bl):
    bi = iter(bl)
    bytes = zip(*(bi,) * 8)
    shifts = (7, 6, 5, 4, 3, 2, 1, 0)
    for byte in bytes:
        yield chr(sum(bit << s for bit, s in zip(byte, shifts)))

def bitlist_to_string(bl):
    return ''.join(bitlist_to_chars(bl))

def string_to_bitstring(s):
    l = string_to_bitlist(s)
    return ''.join([str(bit) for bit in l])

print(string_to_bitstring("a"))