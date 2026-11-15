"""Pause the supported game using a shared offset for its two Windows clocks.

The unused executable-section tail holds two small x86 wrappers. Only the
game's QPC/GetTickCount imports change. Wine and controller clocks stay real.
No file is patched. Mapping, zero padding and existing hooks are validated.
"""
import os,signal,struct,time
from pathlib import Path

def u32(n):return struct.pack('<I',n)

class Pause:
    def __init__(self):self.stopped={}

    def apply(self,pids,value):
        if value:
            for pid in pids:
                if pid in self.stopped:continue
                fd=os.open(f'/proc/{pid}/mem',os.O_RDWR)
                try:
                    base=None
                    for line in Path(f'/proc/{pid}/maps').read_text().splitlines():
                        fields=line.split()
                        if len(fields)>5 and fields[-1].endswith('/racing.exe') and int(fields[2],16)==0:
                            base=int(fields[0].split('-')[0],16);break
                    if base is None or os.pread(fd,3,base+0x9fd20)!=bytes.fromhex('83ec10'):
                        raise RuntimeError('Unsupported frame timer mapping')
                    freq=struct.unpack('<Q',os.pread(fd,8,base+0x1e04e8))[0]
                    if not 1000<=freq<=10**10:raise RuntimeError('Invalid timer frequency')
                    os.kill(pid,signal.SIGSTOP)
                    for _ in range(100):
                        if '\nState:\tT' in Path(f'/proc/{pid}/status').read_text():break
                        time.sleep(.001)
                    cave=base+0x198b60
                    block=os.pread(fd,160,cave)
                    if block[:8]==b'SRGPAU01':
                        if os.pread(fd,4,base+0x1990b0)!=u32(cave+32) or os.pread(fd,4,base+0x1990ac)!=u32(cave+96):
                            raise RuntimeError('Clock hooks changed')
                    elif block==bytes(160):
                        data=bytearray(160);data[:8]=b'SRGPAU01'
                        data[20:24]=os.pread(fd,4,base+0x1990b0)
                        data[24:28]=os.pread(fd,4,base+0x1990ac)
                        # BOOL QPC(LARGE_INTEGER *p): preserve ESI and the BOOL result.
                        code=bytes.fromhex('568B74240856FF15')+u32(cave+20)
                        code+=bytes.fromhex('8B0E2B0D')+u32(cave+8)
                        code+=bytes.fromhex('8B56041B15')+u32(cave+12)
                        code+=bytes.fromhex('890E8956045EC20400')
                        data[32:32+len(code)]=code
                        # DWORD GetTickCount(void): subtract accumulated pause ms.
                        code=bytes.fromhex('FF15')+u32(cave+24)+bytes.fromhex('2B05')+u32(cave+16)+b'\xc3'
                        data[96:96+len(code)]=code
                        os.pwrite(fd,data,cave)
                        os.pwrite(fd,u32(cave+32),base+0x1990b0)
                        os.pwrite(fd,u32(cave+96),base+0x1990ac)
                    else:raise RuntimeError('Executable padding is not unused')
                    self.stopped[pid]=(fd,cave,freq,time.monotonic_ns())
                except BaseException:
                    os.kill(pid,signal.SIGCONT);os.close(fd);raise
        else:
            for pid,(fd,cave,freq,started) in list(self.stopped.items()):
                try:
                    elapsed=time.monotonic_ns()-started
                    old=struct.unpack('<Q',os.pread(fd,8,cave+8))[0]
                    os.pwrite(fd,struct.pack('<Q',old+round(elapsed*freq/1e9)),cave+8)
                    old=struct.unpack('<I',os.pread(fd,4,cave+16))[0]
                    os.pwrite(fd,u32((old+round(elapsed/1e6))&0xffffffff),cave+16)
                finally:
                    try:os.kill(pid,signal.SIGCONT)
                    except ProcessLookupError:pass
                    os.close(fd);del self.stopped[pid]
