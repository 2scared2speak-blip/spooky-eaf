from pathlib import Path
import struct
from PIL import Image

HEADER_SIZE=16; ENTRY_SIZE=8; FRAME_MAGIC=0x5A5A; EAF_MAGIC=b"\x89EAF"

def checksum32(data): return sum(data)&0xFFFFFFFF

def parse_container(data, base=0):
    if base+16>len(data) or data[base:base+4]!=EAF_MAGIC: raise ValueError("invalid EAF header")
    frames, chk, stored = struct.unpack_from("<III",data,base+4)
    end=base+16+stored
    if frames<1 or end>len(data): raise ValueError("invalid/truncated container")
    if checksum32(data[base+16:end])!=chk: raise ValueError("checksum mismatch")
    if frames*8>stored: raise ValueError("frame table exceeds payload")
    return {"offset":base,"frames":frames,"checksum":chk,"stored_length":stored,"total_size":16+stored}

def scan(data):
    out=[]; pos=0
    while True:
        off=data.find(EAF_MAGIC,pos)
        if off<0: return out
        pos=off+1
        try: out.append(parse_container(data,off))
        except ValueError: pass

def get_frame(data,c,index):
    if not 0<=index<c["frames"]: raise IndexError(index)
    base=c["offset"]; ts=c["frames"]*8
    size,rel=struct.unpack_from("<II",data,base+16+index*8)
    region=c["stored_length"]-ts
    if size<2 or rel>region or size>region-rel: raise ValueError("invalid frame bounds")
    p=base+16+ts+rel
    if struct.unpack_from("<H",data,p)[0]!=FRAME_MAGIC: raise ValueError("bad frame magic")
    return data[p+2:p+size]

def parse_s(frame):
    if frame[:2]!=b"_S" or len(frame)<18: raise ValueError("invalid _S frame")
    depth=frame[9]; w,h,blocks,bh=struct.unpack_from("<HHHH",frame,10)
    if depth!=8 or not w or not h or not blocks: raise ValueError("unsupported/invalid _S frame")
    table_end=18+blocks*4
    if table_end>len(frame): raise ValueError("truncated block table")
    lengths=[struct.unpack_from("<I",frame,18+i*4)[0] for i in range(blocks)]
    pal_end=table_end+1024
    if pal_end>len(frame): raise ValueError("truncated palette")
    offs=[]; cur=pal_end
    for n in lengths: offs.append(cur); cur+=n
    if cur>len(frame): raise ValueError("truncated block data")
    return {"width":w,"height":h,"blocks":blocks,"block_height":bh,"lengths":lengths,"offsets":offs,"palette":frame[table_end:pal_end]}

def parse_c(frame):
    r={"valid":False,"field_1":None,"text_length":None,"text":"","error":""}
    if frame[:2]!=b"_C": r["error"]="not _C"; return r
    if len(frame)<16: r["error"]="truncated _C header"; return r
    r["field_1"],r["text_length"]=struct.unpack_from("<II",frame,8)
    avail=len(frame)-16; n=r["text_length"]
    r["text"]=frame[16:16+min(n,avail)].decode("utf-8","replace")
    if n>avail: r["error"]=f"text truncated: declared {n}, available {avail}"; return r
    r["valid"]=True; return r

def rle_decode(src,cap):
    out=bytearray()
    for i in range(0,len(src)-1,2):
        n,v=src[i],src[i+1]
        if len(out)+n>cap: raise ValueError("RLE overflow")
        out.extend([v]*n)
    return bytes(out)

def decode_image(frame):
    h=parse_s(frame); idx=bytearray(); w=h["width"]; height=h["height"]
    for bi,(off,n) in enumerate(zip(h["offsets"],h["lengths"])):
        block=frame[off:off+n]
        if not block or block[0]!=0: raise ValueError("unsupported block encoding")
        rows=min(h["block_height"],height-bi*h["block_height"]); expected=w*rows
        raw=rle_decode(block[1:],expected)
        if len(raw)!=expected: raise ValueError("RLE size mismatch")
        idx.extend(raw)
    if len(idx)!=w*height: raise ValueError("pixel count mismatch")
    rgba=bytearray()
    pal=h["palette"]
    for ci in idx:
        b,g,r,a=pal[ci*4:ci*4+4]; rgba.extend((r,g,b,a))
    return Image.frombytes("RGBA",(w,height),bytes(rgba)),h
