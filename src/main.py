from typing import Union
from types import SimpleNamespace
import sys

import bpy

from .debug.mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD

from .utils.printx import *

from .native import native
from .native.blender import get_data

from . import prefs
from . import ime

from .prefs import get_prefs, Prefs

if DEBUG_BUILD:
    from . import dev

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

info = {
    'github': 'https://github.com/Arius-Cr/wire_ext_blender_fix_ime',
    'baidu': 'https://pan.baidu.com/s/1H9DxkAdmBJXLhl5Aj29Q6Q?pwd=q4e5',
}

registered: bool = False

blender_data: Union['BlenderData', None] = None

def register() -> None:
    if DEBUG_BUILD:
        printx(CCFY, f"\n===== {__package__} start =====")

    if sys.platform != 'win32':
        raise Exception(f"{__package__}: 仅支持 Windows 平台")

    # 在 Blender 处于后台模式（--background）时插件无需工作
    if bpy.app.background:
        return

    if 'input_ime' in dir(bpy.app.build_options):
        if DEBUG_BUILD:
            printx("输入法助手：当前的 Blender 已修复输入法问题。为避免冲突，插件已静默。")
        return

    if not native.dll_load():
        raise Exception(f"{__package__}: 无法加载 {__package__}.dll")

    # -----

    global registered, blender_data

    prefs.register()
    ime.register()

    if DEBUG_BUILD:
        dev.register()

    _prefs = get_prefs(bpy.context)

    if DEBUG_BUILD:
        Prefs.use_debug_update(_prefs, bpy.context)
        printx(CCBY, "调试选项：")
        for _name in mark.mark_names:
            printx(f"  {CCFA}{_name}{CCZ0}：{getattr(mark, _name)}")
    else:
        _prefs.use_debug = False

    native.init(*bpy.app.version)

    blender_data = BlenderData()
    blender_data.load()
    blender_data.apply()

    fix_on()

    registered = True
    pass

def unregister() -> None:
    global registered

    if not registered:
        return

    fix_off()

    native.uninit()

    native.dll_unload()

    prefs.unregister()
    ime.unregister()

    if DEBUG_BUILD:
        dev.unregister()

    if DEBUG_BUILD:
        printx(CCFY, f"===== {__package__} end =====")

    registered = False
    pass

def fix_on():
    _prefs = get_prefs(bpy.context)

    Prefs.use_fix_ime_update(_prefs, bpy.context)
    pass

def fix_off():
    Prefs.use_fix_ime_update(SimpleNamespace(
        use_fix_ime_for_field=False,
        use_fix_ime_for_space=False,
        use_fix_ime_font_edit=False,
        use_fix_ime_text_editor=False,
        use_fix_ime_console=False,
        use_fix_ime_sequence_editor=False,
    ), bpy.context)
    pass

class BlenderData:
    def __init__(self) -> None:
        self.data: Union[dict, None] = None
        self.blender_vers: list[tuple[tuple[int, int, int], tuple[int, int, int], Union[str, None], Union[str, None]]] = []
        self.items: dict[str, int] = {}
        self.is_compatible: bool = False
        pass

    def load(self) -> bool:
        self.data = None
        self.blender_vers = []
        self.items = {}
        self.is_compatible = False

        from . import _bl_info
        data = get_data(_bl_info['version'], bpy.app.version)

        if data is None:
            if mark.DEBUG:
                printx(CCFR, "调用 get_data 返回空")
            return False

        self.type = type
        self.data = data
        self.blender_vers = data['blender_vers']
        self.items = data['items']
        for _min, _max, *_ in self.blender_vers:
            if _min <= bpy.app.version <= _max:
                self.is_compatible = True

        return True

    def apply(self) -> bool:
        if not self.is_compatible:
            if mark.DEBUG:
                printx(CCFR, "内存偏移量和当前 Blender 版本不兼容")
            return False

        for _name, _value in self.items.items():
            success = native.blender_data_set(_name, _value)
            if not success:
                if mark.DEBUG:
                    printx(CCFR, "设置内存偏移量失败：", _name)
                return False

        return True
