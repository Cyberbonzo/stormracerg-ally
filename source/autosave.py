"""Local automatic progression and native-save protection for the supported build.

Only progression values are persisted from RAM, never pointers or a race state.
The companion process performs disk work independently of controller polling.
"""
import hashlib
from contextlib import closing
import io
import json
import os
from pathlib import Path
import signal
import sqlite3
import struct
import time
import zipfile

GAME_SHA = 'e9370d75a93ab55739a08c2f88297ce80a6185f8f2b82590990999da3a97a5f7'
NATIVE = ['game/assets/save/' + n + '.dat' for n in
          ('saveData', 'incomeData', 'playerStatData', 'miscStatData', 'miscStatData0', 'miscStatData1')]
DATABASE = 'game/bin/racing.db'
FIELDS = ('cars', 'tracks', 'points')


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    # The data and rename must both survive loss of power on Linux.
    if os.name == 'posix':
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def valid_progress(p):
    return (isinstance(p, dict) and set(p) == set(FIELDS)
            and all(type(p[k]) is int for k in FIELDS)
            and 0 <= p['cars'] < 1 << 12 and 0 <= p['tracks'] < 1 << 7
            and 0 <= p['points'] <= 10000000)


def merged(a, b):
    return dict(cars=a['cars'] | b['cars'], tracks=a['tracks'] | b['tracks'],
                points=max(a['points'], b['points']))


class Profile:
    def __init__(self, root):
        self.path = root / 'saves/progress.json'
        self.previous = root / 'saves/progress.previous.json'
        self.value = dict.fromkeys(FIELDS, 0)
        self.loaded = False
        existing = False
        for path in (self.path, self.previous):
            if not path.exists():
                continue
            existing = True
            try:
                doc = json.loads(path.read_text(encoding='utf8'))
                value = doc['progress']
                encoded = json.dumps(value, sort_keys=True).encode()
                if (doc['version'] != 1 or doc['game_sha256'] != GAME_SHA
                        or not valid_progress(value)
                        or hashlib.sha256(encoded).hexdigest() != doc['sha256']):
                    raise ValueError('Invalid progression snapshot')
                self.value = merged(self.value, value)
                self.loaded = True
            except (OSError, ValueError, KeyError, TypeError):
                print('Invalid progression copy:', path.name, flush=True)
        if existing and not self.loaded:
            raise ValueError('Both progression copies are invalid; preserved for recovery')

    def update(self, value):
        if not valid_progress(value):
            raise ValueError('Progression is outside supported limits')
        value = merged(self.value, value)
        if self.loaded and value == self.value:
            return
        doc = dict(version=1, game_sha256=GAME_SHA, progress=value,
                   sha256=hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest(),
                   saved_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        data = (json.dumps(doc, indent=2) + '\n').encode()
        # Both copies contain the latest confirmed progress after a successful save.
        # A crash between renames leaves at least the previous valid generation.
        atomic(self.path, data)
        atomic(self.previous, data)
        self.value, self.loaded = value, True
        print('Progress saved:', value, flush=True)


def valid_native(name, data):
    sizes = {'incomeData.dat': 212, 'playerStatData.dat': 144,
             'miscStatData.dat': 68, 'miscStatData0.dat': 68, 'miscStatData1.dat': 68}
    if name in sizes:
        return len(data) == sizes[name] and data[:4] in (b'100v', b'200v')
    if name != 'saveData.dat' or len(data) < 136 or data[:4] != b'500v':
        return False
    count = struct.unpack_from('<I', data, 132)[0]
    if not 1 <= count <= 10:
        return False
    offset = 136
    for _ in range(count):
        if offset + 16 > len(data):
            return False
        entries, maximum = struct.unpack_from('<II', data, offset)
        if not 0 <= entries <= maximum <= 100:
            return False
        offset += 16 + entries * 12
    return offset == len(data)


def sqlite_ok(path):
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            return db.execute('PRAGMA quick_check').fetchone() == ('ok',) and bool(
                db.execute("SELECT 1 FROM sqlite_master WHERE name='ranking'").fetchone())
    except sqlite3.Error:
        return False


class NativeSaves:
    def __init__(self, root):
        self.root = root
        self.path = root / 'saves/native-latest.zip'
        self.previous = root / 'saves/native-previous.zip'
        self.signature = None

    def recover(self):
        """Only restore missing/damaged files, before the game process is started."""
        bad = [n for n in NATIVE if not (self.root / n).is_file()
               or not valid_native(Path(n).name, (self.root / n).read_bytes())]
        if not sqlite_ok(self.root / DATABASE):
            bad.append(DATABASE)
        for archive in (self.path, self.previous):
            if not bad or not archive.exists():
                continue
            try:
                with zipfile.ZipFile(archive) as z:
                    for name in list(bad):
                        data = z.read(name)  # CRC is verified by ZipFile.
                        if name != DATABASE and not valid_native(Path(name).name, data):
                            continue
                        if name == DATABASE:
                            check = self.root / 'saves/recovery-check.db'
                            atomic(check, data)
                            good = sqlite_ok(check)
                            check.unlink()
                            if not good:
                                continue
                        destination = self.root / name
                        if destination.exists():
                            atomic(self.root / 'saves/damaged' / (destination.name + '-' + str(time.time_ns())),
                                   destination.read_bytes())
                        atomic(destination, data)
                        bad.remove(name)
                        print('Recovered native save:', name, flush=True)
            except (OSError, ValueError, KeyError, zipfile.BadZipFile):
                continue
        if bad and (self.path.exists() or self.previous.exists()):
            raise ValueError('Unable to recover native saves: ' + ', '.join(bad))

    def snapshot(self):
        paths = [self.root / n for n in NATIVE + [DATABASE]]
        if not all(p.is_file() for p in paths):
            return
        signature = [(p.stat().st_mtime_ns, p.stat().st_size) for p in paths]
        if signature == self.signature:
            return
        contents = {}
        for name in NATIVE:
            p = self.root / name
            data = p.read_bytes()
            if data != p.read_bytes() or not valid_native(p.name, data):
                return  # A concurrent native write will be retried next time.
            contents[name] = data
        temp = self.root / 'saves/database-snapshot.db'
        temp.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect((self.root / DATABASE).as_uri() + '?mode=ro', uri=True, timeout=2)) as src:
                with closing(sqlite3.connect(temp)) as dst:
                    src.backup(dst)
            if not sqlite_ok(temp):
                return
            contents[DATABASE] = temp.read_bytes()
        finally:
            temp.unlink(missing_ok=True)
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in contents.items():
                z.writestr(name, data)
        if self.path.exists():
            atomic(self.previous, self.path.read_bytes())
        atomic(self.path, memory.getvalue())
        self.signature = signature


class LiveProgress:
    def __init__(self, root, profile):
        self.root, self.profile = root, profile
        self.pid = None
        self.base = None

    def tick(self):
        if self.pid is None or not Path(f'/proc/{self.pid}').exists():
            self.pid = self.base = None
            for p in Path('/proc').glob('[0-9]*'):
                try:
                    command = (p / 'cmdline').read_bytes().replace(b'\\', b'/')
                    if ((p / 'comm').read_text().strip() == 'racing.exe'
                            and ('/' + self.root.name + '/game/bin/').encode() in command):
                        self.pid = int(p.name)
                        break
                except OSError:
                    continue
            if self.pid is None:
                return
        fd = os.open(f'/proc/{self.pid}/mem', os.O_RDWR)
        try:
            if self.base is None:
                for line in Path(f'/proc/{self.pid}/maps').read_text().splitlines():
                    fields = line.split()
                    if line.endswith('/racing.exe') and int(fields[2], 16) == 0:
                        self.base = int(fields[0].split('-')[0], 16)
                        break
                if self.base is None:
                    return
            b = self.base
            # The launcher supplies this patch before execution. Refuse unknown code.
            if os.pread(fd, 3, b + 0x5c8c0) != b'\x31\xc0\xc3':
                return
            if struct.unpack('<I', os.pread(fd, 4, b + 0x10bd544c))[0] == 0:
                return  # Wait for framework initialization.
            address = b + 0x3e16bdc
            raw = os.pread(fd, 20, address)
            if raw != os.pread(fd, 20, address):
                return
            _, cars, _, tracks, points = struct.unpack('<5I', raw)
            live = dict(cars=cars, tracks=tracks, points=points)
            if not valid_progress(live):
                return
            self.profile.update(live)
            saved = self.profile.value
            # Restore only missing progress; never reduce values earned in this run.
            if live != saved:
                from pause import Pause
                pause = Pause()
                already_stopped = '\nState:\tT' in Path(f'/proc/{self.pid}/status').read_text()
                try:
                    if not already_stopped:
                        pause.apply([self.pid], True)
                    # Re-read while stopped, so a newly earned bit cannot be lost.
                    _, cars, _, tracks, points = struct.unpack('<5I', os.pread(fd, 20, address))
                    current = dict(cars=cars, tracks=tracks, points=points)
                    if not valid_progress(current):
                        return
                    saved = merged(saved, current)
                    for offset, key in ((4, 'cars'), (12, 'tracks'), (16, 'points')):
                        if current[key] != saved[key]:
                            os.pwrite(fd, struct.pack('<I', saved[key]), address + offset)
                            if offset in (4, 12):
                                os.pwrite(fd, struct.pack('<I', saved[key]), address + offset - 4)
                            print('Progress restored:', key, saved[key], flush=True)
                finally:
                    if not already_stopped:
                        pause.apply([], False)
        finally:
            os.close(fd)


def prepare(root):
    with (root / 'game/bin/racing.exe').open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != GAME_SHA:
            raise ValueError('Automatic save requires the supported executable revision')
    Profile(root)  # Validate before starting the game.
    native = NativeSaves(root)
    native.recover()
    native.snapshot()


def main():
    root = Path(__file__).resolve().parents[1]
    profile = Profile(root)
    live, native = LiveProgress(root, profile), NativeSaves(root)
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    last_disk = 0
    last_error = None
    while running:
        try:
            live.tick()
            if time.monotonic() - last_disk >= 5:
                native.snapshot()
                last_disk = time.monotonic()
            last_error = None
        except (OSError, ValueError, RuntimeError, sqlite3.Error) as e:
            if str(e) != last_error:
                print('Autosave retry:', e, flush=True)
                last_error = str(e)
        time.sleep(.25)
    native.snapshot()


if __name__ == '__main__':
    main()
