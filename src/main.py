from typing import cast, Literal, Union
from types import SimpleNamespace
import sys
import importlib

import bpy

from .debug.mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD

from .utils.printx import *

from .native import native

from . import bl_info
from . import prefs
from . import ime

from .prefs import get_prefs, Prefs, PrefsAlert

if DEBUG_BUILD:
    from . import dev

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

info = {
    'supported_versions': [
        ((3, 0, 0), (3, 6, 11)),
        ((4, 0, 0), (4, 1, 1)),
    ],
    'github': 'https://github.com/Arius-Cr/wire_ext_blender_fix_ime',
    'baidu': 'https://pan.baidu.com/s/1H9DxkAdmBJXLhl5Aj29Q6Q?pwd=q4e5',
}

version_mismatch_alert: Union[list[str], None] = None

def register() -> None:
    if DEBUG_BUILD:
        printx(CCFY, f"\n===== {__package__} start =====")

    if sys.platform != 'win32':
        raise Exception(f"{__package__}: 仅支持 Windows 平台")

    # 在 Blender 处于后台模式（--background）时插件无需工作
    if bpy.app.background:
        return

    # 因为使用了指针，所以需要严格限制 Blender 版本号
    supported = False
    supported_versions = info['supported_versions']
    for supported_version in supported_versions:
        if supported_version[0] <= bpy.app.version <= supported_version[1]:
            supported = True
            break
    if not supported:
        global version_mismatch_alert

        ver_addon = '.'.join(map(str, bl_info['version']))

        vers: list[str] = []
        for supported_version in supported_versions:
            vers.append(f"{'.'.join(map(str, supported_version[0]))}-{'.'.join(map(str, supported_version[1]))}")

        version_mismatch_alert = []
        version_mismatch_alert.append(f"当前插件（{ver_addon}）仅支持以下的 Blender 版本：")
        version_mismatch_alert.extend(vers)
        version_mismatch_alert.append("请更新插件，或联系作者升级插件。")

        _str = '\n'.join(version_mismatch_alert)
        printx(CCFA, f"{__package__}: {_str}")

        bpy.utils.register_class(PrefsAlert)
        return

    # -----

    if native.dll_load():

        prefs.register()
        ime.register()

        if DEBUG_BUILD:
            dev.register()

        # -----

        _prefs = get_prefs(bpy.context)

        if DEBUG_BUILD:
            Prefs.use_debug_update(_prefs, bpy.context)
            printx(CCBY, "调试选项：")
            # printx(f"  {CCFA}DEBUG{CCZ0}：{mark.DEBUG}")
            for _name in mark.mark_names:
                printx(f"  {CCFA}{_name}{CCZ0}：{getattr(mark, _name)}")
        else:
            _prefs.use_debug = False

        native.init(*bpy.app.version)

        Prefs.use_fix_ime_update(_prefs, bpy.context)

    pass

def unregister() -> None:
    if bpy.app.background:
        return

    global version_mismatch_alert
    if version_mismatch_alert is not None:
        bpy.utils.unregister_class(PrefsAlert)
        return

    # -----

    if native.dll:

        Prefs.use_fix_ime_update(SimpleNamespace(
            use_fix_ime_for_field=False,
            use_fix_ime_for_space=False,
            use_fix_ime_font_edit=False,
            use_fix_ime_text_editor=False,
            use_fix_ime_console=False,
        ), bpy.context)

        native.uninit()

        native.dll_unload()

        # -----

        ime.unregister()
        prefs.unregister()

        if DEBUG_BUILD:
            dev.unregister()

    if DEBUG_BUILD:
        printx(CCFY, f"===== {__package__} end =====")
    pass
