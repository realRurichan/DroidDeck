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

    headers = {
        'cpp/core/plugin/PluginImpl.cpp': ('<functional>', '<wctype.h>'),
        'cpp/plugins/psbfile/PSBValue.h': ('<optional>', '<memory>'),
    }
    for name, (existing, missing) in headers.items():
        path = root / name
        text = path.read_text(encoding='utf-8')
        before = f'#include {existing}'
        if text.count(before) != 1:
            raise RuntimeError(f'Unexpected pinned source: {path}')
        path.write_text(text.replace(before, before + f'\n#include {missing}'), encoding='utf-8')

    path = root / 'cpp/core/tjs2/tjsString.h'
    text = path.read_text(encoding='utf-8')
    before = 'tjs_int GetLen() const { return Ptr->GetLength(); }'
    if text.count(before) != 1:
        raise RuntimeError(f'Unexpected pinned source: {path}')
    # Empty TJS strings have no backing object; GCC removes null-this checks.
    path.write_text(text.replace(before,
        'tjs_int GetLen() const { return Ptr ? Ptr->GetLength() : 0; }'), encoding='utf-8')

    fixes = {
        'cpp/core/environ/linux/Platform.cpp': [(
            'return !std::filesystem::create_directory(folder.AsStdString().c_str());',
            'return std::filesystem::create_directory(folder.AsStdString().c_str()) ||\n'
            '        TVPCheckExistentLocalFolder(folder);')],
        'cpp/plugins/fstat/main.cpp': [(
            'if(ttstr filename(TVPGetLocallyAccessibleName(TVPGetPlacedPath(file)));',
            'const ttstr placed = TVPGetPlacedPath(file);\n'
            '        if(placed.IsEmpty()) return false;\n'
            '        if(ttstr filename(TVPGetLocallyAccessibleName(placed));')],
        'cpp/plugins/psbfile/main.cpp': [(
            'static PSBMedia *psbMedia = nullptr;\n', ''), (
            '''        auto objs = self->getObjects();
        for(const auto &[k, v] : *objs) {
            const auto &res = std::dynamic_pointer_cast<PSBResource>(v);
            if(res == nullptr)
                continue;
            ttstr pathN{ k };
            psbMedia->NormalizeDomainName(path);
            psbMedia->NormalizePathName(pathN);
            psbMedia->add((path + TJS_W("/") + pathN).AsStdString(), res);
        }''',
            '        if(loadSuccess) registerRootResources(path, *self);'), (
            '        psbFile->loadPSBFile(path);',
            '        if(psbFile->loadPSBFile(path)) registerRootResources(path, *psbFile);')],
    }
    for name, replacements in fixes.items():
        path = root / name
        text = path.read_text(encoding='utf-8')
        for before, after in replacements:
            if text.count(before) != 1:
                raise RuntimeError(f'Unexpected pinned source: {path}')
            text = text.replace(before, after)
        path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]))
