#!/usr/bin/env python3
"""Prepare Storm Racer G from the user's archive and separately obtained dependencies."""
import argparse,hashlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
from pathlib import Path

RUNTIME_URL='https://github.com/aderumier/windowsarcadeloader/releases/download/v0.1/windows-arcade-loader-v0.1.tar.gz'
RUNTIME_SHA='8423c2169271043938b309554d1ab1d47e06ec83f849d290ceb5fad0f6f8e534'
CODEC_URL='https://download.microsoft.com/download/2/8/D/28DA9C3E-6DA2-456F-BD33-1F937EB6E0FF/WindowsServer2003-WindowsMedia-KB2845142-x86-ENU.exe'
CODEC_SHA='51e11691339c1c817b12f92e613145ffcd7b6f7e869d994cc8dbc4591b24f155'
GAME_SHA='e9370d75a93ab55739a08c2f88297ce80a6185f8f2b82590990999da3a97a5f7'

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def dependency(root,path,url,expected,download):
    if path is None:
        path=root/'dependencias'/url.rsplit('/',1)[1]
        if not path.exists():
            if not download:raise ValueError('Supply dependency archives or use --download-dependencies')
            urllib.request.urlretrieve(url,path)
    if digest(path)!=expected:raise ValueError('Dependency checksum mismatch: '+path.name)
    return path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-zip',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path.home()/'Games/StormRacerG')
    p.add_argument('--runtime-archive',type=Path)
    p.add_argument('--codec-archive',type=Path)
    p.add_argument('--system-profile',type=Path)
    p.add_argument('--download-dependencies',action='store_true')
    a=p.parse_args();r=a.root.expanduser().resolve()
    if (r/'game/bin/racing.exe').exists():raise SystemExit('Existing installation: preserve saves and update source separately.')
    if not shutil.which('cabextract'):raise SystemExit('cabextract is required to extract the codec; nothing was installed.')
    try:import PIL
    except ImportError:raise SystemExit('The pause menu requires Pillow from the Linux environment; nothing was installed.')
    with zipfile.ZipFile(a.game_zip) as z:
        if hashlib.sha256(z.read('bin/racing.exe')).hexdigest()!=GAME_SHA:raise ValueError('Unsupported racing.exe revision')
    for d in ('game','source','logs','dependencias','artes'):(r/d).mkdir(parents=True,exist_ok=True)
    runtime=dependency(r,a.runtime_archive,RUNTIME_URL,RUNTIME_SHA,a.download_dependencies)
    codec=dependency(r,a.codec_archive,CODEC_URL,CODEC_SHA,a.download_dependencies)
    with zipfile.ZipFile(a.game_zip) as z:
        for m in z.infolist():
            relative=Path(m.filename)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe ZIP path')
            if m.is_dir() or '.svn' in relative.parts:continue
            out=(r/'game'/relative).resolve()
            if not out.is_relative_to(r/'game'):raise ValueError('Unsafe ZIP path')
            out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(m) as src,out.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
    shutil.copy2(r/'game/bin/usb_io.dll',r/'dependencias/usb_io.original.dll')
    with tarfile.open(runtime) as t:
        m=t.getmember('windows-arcade-loader-v0.1/payloads/wal_wahlap.dll')
        with t.extractfile(m) as src,(r/'game/bin/usb_io.dll').open('wb') as dst:shutil.copyfileobj(src,dst)
    subprocess.run(['cabextract','-q','-d',str(r/'dependencias/codec'),str(codec)],check=True)
    shutil.copy2(r/'dependencias/codec/wm64/wmv9vcm.dll',r/'game/bin/WMV9VCM.dll')
    repo=Path(__file__).resolve().parents[1]
    for name in ('jogar.sh','source/run.py','source/controls.py','source/pause.py','source/pause_menu.py','source/cheats.py','source/configure.py','source/autosave.py'):
        shutil.copy2(repo/name,r/name)
    (r/'jogar.sh').chmod(0o755)
    sys.path.insert(0,str(r/'source'))
    from configure import configure
    configure(r,a.system_profile)
    print('Prepared:',r)
    print('Add jogar.sh as a non-Steam game. Do not force compatibility: it starts Proton 11 itself.')

if __name__=='__main__':main()
