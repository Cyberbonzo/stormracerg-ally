#!/usr/bin/env python3
"""Apply private, user-supplied artwork through the running Steam client."""
import argparse
import base64
import hashlib
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from PIL import Image
from steam_cdp import SteamCDP

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.home()/'Games/StormRacerG')
    parser.add_argument('--app-id',type=int,required=True)
    parser.add_argument('--account',required=True,help='Steam userdata directory name')
    args=parser.parse_args()
    if not args.account.isdigit() or not 0<args.app_id<2**32:
        parser.error('Invalid Steam identifiers')
    root=args.root.expanduser().resolve();art=root/'artes'
    grid=Path.home()/'.local/share/Steam/userdata'/args.account/'config/grid'
    assert grid.is_dir(),'Steam grid directory not found'
    assets=[]
    for stem,kind,suffix in [('portrait',0,'p'),('hero',1,'_hero'),
                             ('logo',2,'_logo'),('landscape',3,''),('icon',4,'_icon')]:
        candidates=[art/(stem+ext) for ext in ('.png','.jpg')]
        path=next((p for p in candidates if p.is_file()),None)
        assert path is not None,'Missing artwork: '+stem
        with Image.open(path) as im:
            width,height=im.size;ratio=width/height
            if stem=='portrait':assert abs(ratio-2/3)<.03,'Portrait must be 2:3'
            if stem=='hero':assert 2.5<=ratio<=3.5,'Hero must be panoramic'
            if stem=='landscape':assert abs(ratio-16/9)<.04,'Landscape must be 16:9'
            if stem=='icon':assert abs(ratio-1)<.03,'Icon must be square'
            if stem=='logo':
                assert im.mode=='RGBA' and im.getchannel('A').getextrema()[0]==0,'Logo must have transparency'
            im.load()
        assets.append((path.name,kind,suffix))
    for filename,_,_ in assets:
        path=art/filename
        assert path.is_file() and path.stat().st_size<20_000_000,filename
        data=path.read_bytes()
        assert (data.startswith(b'\x89PNG\r\n\x1a\n') if path.suffix=='.png' else data.startswith(b'\xff\xd8')),filename
    backup=root/'source/artwork-backup'/datetime.now().strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True,exist_ok=False)
    for p in grid.glob(str(args.app_id)+'*'):
        if p.is_file():shutil.copy2(p,backup/p.name)
    c=SteamCDP()
    name=c.evaluate(f'appStore.GetAppOverviewByAppID({args.app_id})?.display_name')
    assert name=='Storm Racer G',f'Unexpected shortcut: {name!r}'
    report={'app_id':args.app_id,'name':name,'assets':[]}
    for filename,kind,suffix in assets:
        src=art/filename;ext=src.suffix[1:]
        dest=grid/(str(args.app_id)+suffix+'.'+ext)
        if kind==4:
            # Non-Steam icons use the shortcut API; artwork type 4 can reject them.
            shutil.copy2(src,dest)
            c.evaluate('SteamClient.Apps.SetShortcutIcon('+str(args.app_id)+','+json.dumps(str(src))+')')
        else:
            c.evaluate(f'SteamClient.Apps.ClearCustomArtworkForApp({args.app_id},{kind})')
            time.sleep(.6)
            payload=base64.b64encode(src.read_bytes()).decode()
            c.evaluate('SteamClient.Apps.SetCustomArtworkForApp('+','.join(map(json.dumps,[args.app_id,payload,ext,kind]))+')')
        for _ in range(30):
            if dest.is_file() and digest(dest)==digest(src):break
            time.sleep(.1)
        assert dest.is_file() and digest(dest)==digest(src),f'Artwork not persisted: {filename}'
        with Image.open(src) as im:size=list(im.size)
        report['assets'].append({'source':filename,'steam_file':dest.name,'size':size,'sha256':digest(src),'verified':True})
        print('Installed and verified:',filename,flush=True)
    report['overview']=c.evaluate(f'({{custom_images_found:appStore.GetAppOverviewByAppID({args.app_id}).custom_images_found}})')
    (root/'logs').mkdir(exist_ok=True)
    (root/'logs/artwork-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('All five artwork files verified.')

if __name__=='__main__':main()
