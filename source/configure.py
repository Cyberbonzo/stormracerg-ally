"""Configure the private installation from a pinned upstream system profile."""
import hashlib,json,re,urllib.request
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
    (root/'source/runtime-env.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf8')
    p=root/'game/bin/netdbsync.xml'
    s=re.sub(r'<servers>.*?</servers>','<servers />',p.read_text(),flags=re.S)
    p.write_text(s,encoding='utf8')
    p=root/'game/bin/racing.cfg'
    s=p.read_text()
    s=re.sub(r'(?m)^screenWidth\s*=.*$','screenWidth = 1920',s)
    s=re.sub(r'(?m)^screenHeight\s*=.*$','screenHeight = 1080',s)
    p.write_text(s,encoding='utf8')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--profile',type=Path)
    a=parser.parse_args();configure(a.root.expanduser().resolve(),a.profile)
