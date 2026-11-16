"""Configure the private installation from a pinned upstream system profile."""
import hashlib,json,re,struct,urllib.request
from pathlib import Path

PROFILE_URL='https://raw.githubusercontent.com/aderumier/windowsarcadeloader/dd23fdc15e88d8b09a62d712d3d1e5a7d99ae94d/systemprofiles/wahlap/storm-racer-g.yaml'
PROFILE_SHA='c760633702a525091a9e6f91b09606033e203bcc82c3145e9fa85c6d4bfb6fc0'

def configure(root,profile=None):
    data=Path(profile).read_bytes() if profile else urllib.request.urlopen(PROFILE_URL,timeout=30).read()
    if hashlib.sha256(data).hexdigest()!=PROFILE_SHA:raise ValueError('Unexpected system profile')
    block=data.decode().split('env:\n')[1].split('\ncontrols:')[0]
    block=re.sub(r'\\\n\s*','',block)
    env={}
    for line in block.splitlines():
        m=re.match(r'  (WAL_\w+): (.*)',line)
        if m:env[m[1]]=m[2].strip('"')
    # Race boost is action 8, bound to board bit 0x04 in this executable.
    env.update(WAL_PORT='33703',WAL_MAP='start=start+key_enter,b1=bit04,b2=key_backspace,b3=key_b,up=up+key_up,down=down+key_down,left=key_left,right=key_right,coin=coin_counter,test=up+boost')
    env['WAL_D3D9_WINDOWED_SIZE']='1920x1080'
    # The debug dialog restores and focuses its console even on Continue.
    # Return the same non-abort result without changing the focused window.
    env['WAL_PATCHES']+=',0xbffe0:31C0C3'
    # This executable reads the board words in the reverse order from WAL v0.1.
    # Align the two loads with WAL's encoded switch/extended-switch layout.
    env['WAL_PATCHES']+=',0x9f7bf:08,0x9f7f3:04'
    # Keep earned unlocks and points when the arcade session returns to idle.
    # Preserve the reset routine's EAX=0 return convention.
    env['WAL_PATCHES']+=',0x5c8c0:31C0C3'
    # Native asset settings can override the text CFG. Enable the record
    # manager's saveTesting bit when it initializes (set DL=1, same register).
    env['WAL_PATCHES']+=',0x3a0e0:B20190'
    # Drift selection proceeds to the waiting screen, skipping photo capture.
    env['WAL_PATCHES']+=',0x3116:0A'
    # Photo completion normally creates the waiting UI. Retain that initializer
    # before starting the waiting screen. The wrapper uses unused .text padding
    # beyond the pause clock wrappers, and only position-relative branches.
    cave=0x198c10
    wrapper=b'\x60\xe8'+struct.pack('<i',0x62300-(cave+6))+b'\x61\xe9'+struct.pack('<i',0x62470-(cave+12))
    call=b'\xe8'+struct.pack('<i',cave-(0x2980+5))
    env['WAL_PATCHES']+=f',0x198c10:{wrapper.hex()},0x2980:{call.hex()}'
    (root/'source/runtime-env.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf8')
    p=root/'game/bin/netdbsync.xml'
    # Older Windows edits could leave mojibake before the XML declaration.
    s=p.read_text(encoding='utf-8-sig')
    s=s[s.index('<?xml'):]
    s=re.sub(r'<servers>.*?</servers>','<servers />',s,flags=re.S)
    if (root/'game/patch/_version').is_file():
        s=re.sub(r'<verfile>.*?</verfile>','<verfile>../patch/_version</verfile>',s)
    p.write_text(s,encoding='utf8')
    p=root/'game/bin/db_cfg/racing.xml'
    s=p.read_text(encoding='utf-8-sig')
    s=s[s.index('<?xml'):]
    # Disable local housekeep deletes, retaining SQL parameter counts and tasks.
    # The cabinet also purges by row count and mark_send, not just by age.
    s=re.sub(r'<keep_day>.*?</keep_day>','<keep_day>60</keep_day>',s)
    def keep_history(m):
        condition=m[2]
        if not condition.startswith('0 AND ('):condition='0 AND ('+condition+')'
        return '<sql>'+m[1]+condition+'</sql>'
    s=re.sub(r'<sql>(delete from (?:ranking|behavior|inventory|selection|collision) where )(.*?)</sql>',keep_history,s,flags=re.S)
    p.write_text(s,encoding='utf8')
    p=root/'game/bin/racing.cfg'
    s=p.read_text(encoding='utf-8-sig')
    s=re.sub(r'(?m)^screenWidth\s*=.*$','screenWidth = 1920',s)
    s=re.sub(r'(?m)^screenHeight\s*=.*$','screenHeight = 1080',s)
    # Free-play sessions are marked as testing by the native record manager.
    # Its explicit option must be enabled for offline results to reach the DB.
    if re.search(r'(?m)^saveTesting\s*=',s):
        s=re.sub(r'(?m)^saveTesting\s*=.*$','saveTesting = 1',s)
    else:s=s.replace('[record]','[record]\nsaveTesting = 1')
    p.write_text(s,encoding='utf8')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--profile',type=Path)
    a=parser.parse_args();configure(a.root.expanduser().resolve(),a.profile)
