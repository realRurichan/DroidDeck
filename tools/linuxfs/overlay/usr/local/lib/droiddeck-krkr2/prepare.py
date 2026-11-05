from pathlib import Path
import sys


def prepare(root):
    port = root / 'vcpkg/ports/cocos2dx'
    edits = {
        'patch/cocos2d-x/cocos/CMakeLists.txt': (
            'include(audio/CMakeLists.txt)',
            'include(audio/CMakeLists.txt)\nset(COCOS_AUDIO_SRC "")'),
        'patch/cocos2d-x/external/CMakeLists.txt': (
            'if (LINUX)\n    add_subdirectory(linux-specific/fmod)\n'
            '    target_link_libraries(external INTERFACE ext_fmod) # will replace\nendif ()', ''),
        'patch/cocos2d-x/CMakeLists.txt': (
            'if(LINUX)\n    install_ext_lib("linux-specific/fmod")\nendif()', ''),
        'cocos2dx-config.cmake.in': (
            '    add_library(ext_fmod SHARED IMPORTED)\n\n'
            '    set_target_properties(ext_fmod PROPERTIES\n'
            '        INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_CURRENT_LIST_DIR}/linux-specific/fmod/include"\n'
            '        IMPORTED_LOCATION "${CMAKE_CURRENT_LIST_DIR}/linux-specific/fmod/prebuilt/64-bit/libfmod.so"\n'
            '    )', ''),
    }
    # Krkr2 uses its own OpenAL mixer; Cocos' unused audio backend ships x86-only FMOD.
    for name, (before, after) in edits.items():
        path = port / name
        text = path.read_text(encoding='utf-8')
        if text.count(before) != 1:
            raise RuntimeError(f'Unexpected pinned source: {name}')
        path.write_text(text.replace(before, after), encoding='utf-8')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]))
