"""Create a redistributable XP3 regression for archive-root auto paths."""
import json
from pathlib import Path
import struct
import sys
import zlib


def chunk(tag, data):
    return tag + struct.pack('<Q', len(data)) + data


def psb_resource():
    """One-key PSB v1 dictionary with an executable text resource."""
    resource = b'Debug.message("DROIDDECK_KRKR2_PSB_RESOURCE_OK");\n'
    array = lambda values: bytes([13, len(values), 13, *values])
    package = bytearray(40)
    offsets = []
    for data in [array([0]), b'pixel.tjs\0', array([]), b'', array([0]),
                 array([len(resource)]), resource,
                 b'\x21' + array([0]) + b'\x11\0\x19\0']:
        offsets.append(len(package))
        package.extend(data)
    struct.pack_into('<4sHH8I', package, 0, b'PSB\0', 1, 0, *offsets)
    return package


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
            'Debug.message("DROIDDECK_KRKR2_ARCHIVE_ROOT_OK");\n'
            'Plugins.link("psbfile.dll");\n'
            'var psb = new PSBFile();\n'
            'if (!psb.load("probe.pimg")) throw "PSB load failed";\n'
            'Scripts.execStorage("psb://probe.pimg/pixel.tjs");\n'
            'Plugins.link("fstat.dll");\n'
            f'var save = {json.dumps(str(archive.parent / "fresh-save/nested/probe.ksd"), ensure_ascii=False)};\n'
            'var data = %["value" => 42];\n'
            '(Dictionary.saveStruct incontextof data)(save, "b");\n'
            'if (Dictionary.loadStruct(save).value != 42) throw "Save round trip failed";\n'
            'if (!Storages.deleteFile(save)) throw "Delete existing save failed";\n'
            'if (Storages.deleteFile(save)) throw "Missing save reported deleted";\n'
            'Debug.message("DROIDDECK_KRKR2_SAVE_OK");\n'),
        'probe.pimg': psb_resource(),
    }
    package = bytearray(b'XP3\r\n \n\x1a\x8bg\x01' + bytes(8))
    index = bytearray()
    for name, script in sorted(files.items()):
        data = script.encode('utf-8') if isinstance(script, str) else script
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
