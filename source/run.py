#!/usr/bin/env python3
from pathlib import Path
import os,json,subprocess,signal
r=Path(__file__).resolve().parents[1]
env=os.environ.copy();env.update(json.loads((r/'source/runtime-env.json').read_text()))
env.update(STEAM_COMPAT_CLIENT_INSTALL_PATH=str(Path.home()/'.local/share/Steam'),STEAM_COMPAT_DATA_PATH=str(r/'compatdata'),PROTON_LOG='0',WINEDEBUG='-all',PROTON_LOG_DIR=str(r/'logs'),WAL_LOG='Z:'+str(r/'logs/payload.log').replace('/','\\'),WINEDLLOVERRIDES='usb_io,wmv9vcm=n,b')
env.pop('LD_PRELOAD',None)
for p in ['logs','compatdata']:(r/p).mkdir(exist_ok=True)
with (r/'logs/controls.log').open('a') as log:
 helper=subprocess.Popen(['python3',str(r/'source/controls.py')],env=env,stdout=log,stderr=subprocess.STDOUT)
 try:
  with (r/'logs/session.log').open('a') as out:
   subprocess.run([str(Path.home()/'.local/share/Steam/steamapps/common/Proton 11.0/proton'),'waitforexitandrun',str(r/'game/bin/racing.exe')],cwd=r/'game/bin',env=env,stdout=out,stderr=subprocess.STDOUT)
 finally:helper.terminate();helper.wait(timeout=5)
