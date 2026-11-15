"""Toggle the game's own Infinite Boost debug option for this supported build."""
import os,struct
from pathlib import Path

def apply_boost(pid,enabled):
    fd=os.open(f'/proc/{pid}/mem',os.O_RDWR)
    try:
        base=None
        for line in Path(f'/proc/{pid}/maps').read_text().splitlines():
            f=line.split()
            if len(f)>5 and f[-1].endswith('/racing.exe') and int(f[2],16)==0:
                base=int(f[0].split('-')[0],16);break
        if base is None:raise RuntimeError('Game mapping not found')
        def read(a,n):return os.pread(fd,n,a)
        def uint(a):return struct.unpack('<I',read(a,4))[0]
        if read(base+0x80f98,5)!=b'\x68'+struct.pack('<I',base+0x1b76b0):
            raise RuntimeError('Unsupported Infinite Boost configuration')
        root=base+0x1d9300;groups=uint(root);count=uint(root+0x544)
        if not 0<count<128:return False
        for i in range(count):
            group=groups+i*0xc8
            if uint(group+0x84)!=2:continue
            items=uint(group+0x80);n=struct.unpack('<H',read(group+0x88,2))[0]
            if n>128:raise RuntimeError('Invalid debug option count')
            for j in range(n):
                item=items+j*0xc8
                if uint(item+0x80)!=11:continue
                label=read(item,128).decode('utf-16-le').split('\0')[0]
                if label!='Infinite Boost':raise RuntimeError('Unexpected debug option')
                os.pwrite(fd,struct.pack('<I',int(enabled)),item+0xc0)
                # Keep the same native setting when the game initializes another car.
                os.pwrite(fd,bytes([int(enabled)]),base+0x10bd5408)
                return True
        return False
    finally:os.close(fd)
