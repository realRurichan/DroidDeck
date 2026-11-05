"""Create a redistributable XP3 regression for archive-root auto paths."""
import json
from pathlib import Path
import struct
import sys
import zlib


def chunk(tag, data):
    return tag + struct.pack('<Q', len(data)) + data


def create(archive):
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    files = {
        'startup.tjs': (
            f'Storages.addAutoPath({json.dumps(str(archive) + ">", ensure_ascii=False)});\n'
            'if (Storages.isExistentStorage("absent-smoke-resource.tjs")) '
            'throw "Unexpected resource";\n'
            'Scripts.execStorage("probe.tjs");\n'
            'System.exit();\n'),
        'probe.tjs': (
            'var empty = "";\n'
            'if (empty.length != 0 || empty[0] != "" || (int)empty != 0 '
            '|| (real)empty != 0) throw "Empty string conversion failed";\n'
            'Debug.message("DROIDDECK_KRKR2_ARCHIVE_ROOT_OK");\n'),
    }
    package = bytearray(b'XP3\r\n \n\x1a\x8bg\x01' + bytes(8))
    index = bytearray()
    for name, script in sorted(files.items()):
        data = script.encode('utf-8')
        offset = len(package)
        package.extend(data)
        info = struct.pack('<IQQH', 0, len(data), len(data), len(name)) + name.encode('utf-16-le')
        segment = struct.pack('<IQQQ', 0, offset, len(data), len(data))
        index.extend(chunk(b'File', chunk(b'info', info) + chunk(b'segm', segment)
                           + chunk(b'adlr', struct.pack('<I', zlib.adler32(data)))))
    struct.pack_into('<Q', package, 11, len(package))
    package.extend(b'\0' + struct.pack('<Q', len(index)) + index)
    archive.write_bytes(package)


if __name__ == '__main__':
    create(Path(sys.argv[1]))
