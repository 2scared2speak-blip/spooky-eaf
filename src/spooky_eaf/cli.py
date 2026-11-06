import argparse, json
from pathlib import Path
from .core import *

def inspect_cmd(p):
    data=Path(p).read_bytes(); c=parse_container(data); types={}; meta=[]; dims=None
    for i in range(c["frames"]):
        f=get_frame(data,c,i); t=f[:2].decode("ascii","replace"); types[t]=types.get(t,0)+1
        if f[:2]==b"_S" and dims is None:
            s=parse_s(f); dims=(s["width"],s["height"])
        elif f[:2]==b"_C": meta.append(parse_c(f))
    print(f"Format: EAF\nFrames: {c['frames']}\nChecksum: VALID\nFrame types: {types}")
    if dims: print(f"Dimensions: {dims[0]}x{dims[1]}")
    for m in meta: print(f"Metadata: {m['text']!r} valid={m['valid']}")

def scan_cmd(p,as_json=False):
    rows=scan(Path(p).read_bytes())
    if as_json: print(json.dumps(rows,indent=2)); return
    for i,c in enumerate(rows,1): print(f"{i:02d} 0x{c['offset']:08X} frames={c['frames']} size={c['total_size']} checksum=VALID")

def decode_cmd(p,out,fps):
    data=Path(p).read_bytes(); c=parse_container(data); out=Path(out); fd=out/"frames"; fd.mkdir(parents=True,exist_ok=True); imgs=[]; metadata=[]
    for i in range(c["frames"]):
        f=get_frame(data,c,i)
        if f[:2]==b"_S":
            im,_=decode_image(f); im.save(fd/f"frame_{i:03d}.png"); imgs.append(im.copy())
        elif f[:2]==b"_C": metadata.append(parse_c(f))
    if imgs: imgs[0].save(out/(Path(p).stem+".gif"),save_all=True,append_images=imgs[1:],duration=1000//fps,loop=0,disposal=2)
    print(f"Rendered {len(imgs)} image frames; metadata records={len(metadata)}")

def metadata_cmd(p):
    data=Path(p).read_bytes(); c=parse_container(data); found=0
    for i in range(c["frames"]):
        f=get_frame(data,c,i)
        if f[:2]==b"_C": found+=1; print(json.dumps({"frame":i,**parse_c(f)},indent=2))
    if not found: print("No _C metadata records")

def main():
    ap=argparse.ArgumentParser(prog="spooky-eaf"); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("inspect"); p.add_argument("file")
    p=sub.add_parser("scan"); p.add_argument("file"); p.add_argument("--json",action="store_true")
    p=sub.add_parser("decode"); p.add_argument("file"); p.add_argument("-o","--output",required=True); p.add_argument("--fps",type=int,default=20)
    p=sub.add_parser("metadata"); p.add_argument("file")
    a=ap.parse_args()
    try:
        if a.cmd=="inspect": inspect_cmd(a.file)
        elif a.cmd=="scan": scan_cmd(a.file,a.json)
        elif a.cmd=="decode": decode_cmd(a.file,a.output,a.fps)
        elif a.cmd=="metadata": metadata_cmd(a.file)
    except Exception as e:
        ap.error(str(e))
