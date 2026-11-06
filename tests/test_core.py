import struct
from spooky_eaf.core import rle_decode, parse_c

def test_rle():
    assert rle_decode(bytes([3,0x7f,2,0x10]),5)==bytes([0x7f]*3+[0x10]*2)

def test_c_metadata():
    text=b"online convert 0.1.4_2025-09-01"
    f=b"_C"+b"\0"*6+struct.pack("<II",1,len(text))+text
    r=parse_c(f)
    assert r["valid"] and r["field_1"]==1 and r["text"]==text.decode()
