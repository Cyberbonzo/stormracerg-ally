"""Exercise persistence and recovery with synthetic data, without a game copy."""
from pathlib import Path
import sqlite3
import struct
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from autosave import Profile, NativeSaves, NATIVE, DATABASE, valid_native


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        profile = Profile(root)
        profile.update(dict(cars=5, tracks=1, points=45))
        profile.update(dict(cars=2, tracks=0, points=12))
        assert Profile(root).value == dict(cars=7, tracks=1, points=45)
        (root / 'saves/progress.json').write_text('{truncated')
        assert Profile(root).value == dict(cars=7, tracks=1, points=45)
        profile = Profile(root)
        profile.update(dict(cars=8, tracks=2, points=46))
        assert Profile(root).value == dict(cars=15, tracks=3, points=46)
        # Synthetic format fixtures contain no original game assets or saves.
        for name in NATIVE:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.name == 'saveData.dat':
                data = b'500v' + bytes(128) + struct.pack('<5I', 1, 0, 8, 123, 1)
            else:
                size = 212 if path.name == 'incomeData.dat' else 144 if path.name == 'playerStatData.dat' else 68
                data = b'100v' + bytes(size - 4)
            assert valid_native(path.name, data)
            path.write_bytes(data)
        database = root / DATABASE
        database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(database)
        db.execute('CREATE TABLE ranking(time REAL)')
        db.execute('INSERT INTO ranking VALUES (123.456)')
        db.commit()
        db.close()
        native = NativeSaves(root)
        native.snapshot()
        original = (root / NATIVE[0]).read_bytes()
        (root / NATIVE[0]).write_bytes(b'partial')
        database.write_bytes(b'corrupted')
        native.recover()
        assert (root / NATIVE[0]).read_bytes() == original
        db = sqlite3.connect(database)
        assert db.execute('SELECT time FROM ranking').fetchone() == (123.456,)
        db.execute('INSERT INTO ranking VALUES (110.0)')
        db.commit()
        db.close()
        native.recover()
        db = sqlite3.connect(database)
        assert db.execute('SELECT COUNT(*) FROM ranking').fetchone() == (2,)
        db.close()
    print('PASS: progress merging, redundant profile, native recovery, newer records retained')


if __name__ == '__main__':
    main()
