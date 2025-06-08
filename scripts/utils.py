# utils.py
import bech32

def decode_npub(npub):
    """Decodes a bech32-encoded npub string to a raw hex pubkey"""
    hrp, data = bech32.bech32_decode(npub)
    if data is None:
        raise ValueError("Invalid bech32 string")
    decoded = bech32.convertbits(data, 5, 8, False)
    return bytes(decoded).hex()
