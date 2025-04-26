import typing
from typing import Literal, Union, Callable
import os
import ctypes
import ctypes as ct
import ctypes.wintypes as wintypes
from pathlib import Path
import shutil

from ..debug.mark import mark
from ..utils.printx import *

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

dll_name = 'wire_fix_ime'

kernel32 = ctypes.windll.kernel32
kernel32.LoadLibraryW.argtypes = [ctypes.wintypes.LPCWSTR]
kernel32.LoadLibraryW.restype = ctypes.wintypes.HMODULE
kernel32.FreeLibrary.argtypes = [ctypes.wintypes.HMODULE]
kernel32.FreeLibrary.restype = ctypes.wintypes.BOOL

# 参数：wm_pointer, FIEV, data
AddonEventCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)

IMEInvoker = Literal['NONE', 'FIELD', 'VIEW_3D', 'TEXT_EDITOR', 'CONSOLE', 'SEQUENCE_EDITOR']
IMEInvokerMaps = {
    0: 'NONE',
    1: 'FIELD',
    2: 'VIEW_3D',
    3: 'TEXT_EDITOR',
    4: 'CONSOLE',
    5: 'SEQUENCE_EDITOR',
    'NONE': 0,
    'FIELD': 1,
    'VIEW_3D': 2,
    'TEXT_EDITOR': 3,
    'CONSOLE': 4,
    'SEQUENCE_EDITOR': 5,
}

FIEV_NONE = 0
FIEV_COMP_START = 1
FIEV_COMP_INPUT = 2
FIEV_COMP_END = 3
FIEV_BUTTON_DOWN = 4
FIEV_LOST_FOCUS = 5
FIEV_WINDOW_DESTORY = 6
FIEVMaps = {
    0: 'NONE',
    1: 'COMP_START',
    2: 'COMP_INPUT',
    3: 'COMP_END',
    4: 'BUTTON_DOWN',
    5: 'LOST_FOCUS',
    6: 'WINDOW_DESTORY',
}

class IMEData:
    def __init__(self) -> None:
        self.composite_str: str = None
        self.composite_len_b: int = None
        self.composite_len_c: int = None
        self.composite_cur_i: int = None
        self.composite_sta_i: int = None
        self.composite_end_i: int = None
        self.result_str: str = None
        self.result_len_b: int = None
        self.result_len_c: int = None

class _main:
    def _dll_init__main(self):
        self.dll.use_debug.argtypes = [ctypes.c_int]
        self.dll.use_debug.restype = ctypes.c_bool

        self.dll.init.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.dll.init.restype = ctypes.c_bool

        self.dll.uninit.argtypes = []
        self.dll.uninit.restype = ctypes.c_bool

    def use_debug(self, level: int) -> bool:
        return self.dll.use_debug(level)

    def init(self, bl_ver_main: int, bl_ver_minor: int, bl_ver_patch: int) -> bool:
        return self.dll.init(bl_ver_main, bl_ver_minor, bl_ver_patch)

    def uninit(self) -> bool:
        return self.dll.uninit()


class _blender:
    def _dll_init__blender(self):
        self.dll.blender_data_set.argtypes = [ctypes.c_wchar_p, ctypes.c_size_t]
        self.dll.blender_data_set.restype = ctypes.c_bool

        self.dll.wmWindow_is_but_active.argtypes = [ctypes.c_void_p]
        self.dll.wmWindow_is_but_active.restype = ctypes.c_bool

        self.dll.wmWindow_is_pop_active.argtypes = [ctypes.c_void_p]
        self.dll.wmWindow_is_pop_active.restype = ctypes.c_bool

        self.dll.wmWindow_active_screen_get.argtypes = [ctypes.c_void_p]
        self.dll.wmWindow_active_screen_get.restype = ctypes.c_void_p

        self.dll.wmWindow_active_region_get.argtypes = [ctypes.c_void_p]
        self.dll.wmWindow_active_region_get.restype = ctypes.c_void_p

        self.dll.SpaceText_lheight_px_get.argtypes = [ctypes.c_void_p]
        self.dll.SpaceText_lheight_px_get.restype = ctypes.c_int

        self.dll.SpaceText_cwidth_px_get.argtypes = [ctypes.c_void_p]
        self.dll.SpaceText_cwidth_px_get.restype = ctypes.c_int

        self.dll.SpaceText_line_number_display_digits_get.argtypes = [ctypes.c_void_p]
        self.dll.SpaceText_line_number_display_digits_get.restype = ctypes.c_int

        self.dll.Strip_is_text_editing_active.argtypes = [ctypes.c_void_p]
        self.dll.Strip_is_text_editing_active.restype = ctypes.c_bool
        
        self.dll.Strip_text_cursor_offset_get.argtypes = [ctypes.c_void_p]
        self.dll.Strip_text_cursor_offset_get.restype = ctypes.c_int
        
        self.dll.Strip_text_cursor_offset_set.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.dll.Strip_text_cursor_offset_set.restype = None
        
        self.dll.Strip_text_selection_start_offset_get.argtypes = [ctypes.c_void_p]
        self.dll.Strip_text_selection_start_offset_get.restype = ctypes.c_int
        
        self.dll.Strip_text_selection_start_offset_set.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.dll.Strip_text_selection_start_offset_set.restype = None
        
        self.dll.Strip_text_selection_end_offset_get.argtypes = [ctypes.c_void_p]
        self.dll.Strip_text_selection_end_offset_get.restype = ctypes.c_int
        
        self.dll.Strip_text_selection_end_offset_set.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.dll.Strip_text_selection_end_offset_set.restype = None

        self.dll.BLF_fixed_width.argtypes = [ctypes.c_wchar_p, ctypes.c_float]
        self.dll.BLF_fixed_width.restype = ctypes.c_int

    def blender_data_set(self, name: str, value: int):
        return self.dll.blender_data_set(name, value)

    def wmWindow_is_but_active(self, wm_pointer: int) -> bool:
        return self.dll.wmWindow_is_but_active(wm_pointer)

    def wmWindow_is_pop_active(self, wm_pointer: int) -> bool:
        return self.dll.wmWindow_is_pop_active(wm_pointer)

    def wmWindow_active_screen_get(self, wm_pointer: int) -> int:
        return self.dll.wmWindow_active_screen_get(wm_pointer)

    def wmWindow_active_region_get(self, wm_pointer: int) -> int:
        return self.dll.wmWindow_active_region_get(wm_pointer)

    def SpaceText_lheight_px_get(self, SpaceText_pointer: int) -> int:
        return self.dll.SpaceText_lheight_px_get(SpaceText_pointer)

    def SpaceText_cwidth_px_get(self, SpaceText_pointer: int) -> int:
        return self.dll.SpaceText_cwidth_px_get(SpaceText_pointer)

    def SpaceText_line_number_display_digits_get(self, SpaceText_pointer: int) -> int:
        return self.dll.SpaceText_line_number_display_digits_get(SpaceText_pointer)
    
    def Strip_is_text_editing_active(self, TextStrip_pointer: int) -> bool:
        return self.dll.Strip_is_text_editing_active(TextStrip_pointer)
    
    def Strip_text_cursor_offset_get(self, TextStrip_pointer: int) -> int:
        return self.dll.Strip_text_cursor_offset_get(TextStrip_pointer)
    
    def Strip_text_cursor_offset_set(self, TextStrip_pointer: int, cursor_offset: int) -> None:
        self.dll.Strip_text_cursor_offset_set(TextStrip_pointer, cursor_offset)
    
    def Strip_text_selection_start_offset_get(self, TextStrip_pointer: int) -> int:
        return self.dll.Strip_text_selection_start_offset_get(TextStrip_pointer)
    
    def Strip_text_selection_start_offset_set(self, TextStrip_pointer: int, cursor_offset: int) -> None:
        self.dll.Strip_text_selection_start_offset_set(TextStrip_pointer, cursor_offset)
    
    def Strip_text_selection_end_offset_get(self, TextStrip_pointer: int) -> int:
        return self.dll.Strip_text_selection_end_offset_get(TextStrip_pointer)
    
    def Strip_text_selection_end_offset_set(self, TextStrip_pointer: int, cursor_offset: int) -> None:
        self.dll.Strip_text_selection_end_offset_set(TextStrip_pointer, cursor_offset)

    def BLF_fixed_width(self, font_path: str, font_size: float) -> int:
        return self.dll.BLF_fixed_width(font_path, font_size)

class _fix_ime:
    def __init__(self) -> None:
        self._use_fix_ime = False
        self._event_callback: ctypes._FuncPointer = None

    def _dll_init__fix_ime(self):
        self.dll.use_fix_ime_debug.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_debug.restype = ctypes.c_bool

        self.dll.use_fix_ime.argtypes = [ctypes.c_bool, ctypes.c_void_p]
        self.dll.use_fix_ime.restype = ctypes.c_bool

        self.dll.use_fix_ime_for_field.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_for_field.restype = None

        self.dll.use_fix_ime_for_space.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_for_space.restype = None

        self.dll.use_fix_direct_input_caps_lock.argtypes = [ctypes.c_bool]
        self.dll.use_fix_direct_input_caps_lock.restype = None

        self.dll.use_fix_direct_input_all.argtypes = [ctypes.c_bool]
        self.dll.use_fix_direct_input_all.restype = None

        self.dll.hook_window.argtypes = [ctypes.c_void_p]
        self.dll.hook_window.restype = ctypes.c_bool

        self.dll.unhook_window.argtypes = [ctypes.c_void_p]
        self.dll.unhook_window.restype = ctypes.c_bool

        self.dll.window_is_active.argtypes = [ctypes.c_void_p]
        self.dll.window_is_active.restype = ctypes.c_bool

        self.dll.window_is_mouse_capture.argtypes = [ctypes.c_void_p]
        self.dll.window_is_mouse_capture.restype = ctypes.c_bool

        self.dll.ime_invoker_get.argtypes = [ctypes.c_void_p]
        self.dll.ime_invoker_get.restype = ctypes.c_int

        self.dll.ime_is_enabled.argtypes = [ctypes.c_void_p]
        self.dll.ime_is_enabled.restype = ctypes.c_bool

        self.dll.ime_enable.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.dll.ime_enable.restype = ctypes.c_bool

        self.dll.ime_disable.argtypes = [ctypes.c_void_p]
        self.dll.ime_disable.restype = ctypes.c_bool

        self.dll.ime_move_candidate_window.argtypes = [ctypes.c_void_p,
                                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                                       ctypes.c_bool]
        self.dll.ime_move_candidate_window.restype = ctypes.c_bool

    def use_fix_ime_debug(self, enable: int) -> bool:
        return self.dll.use_fix_ime_debug(enable)

    def use_fix_ime(self, enable: bool,
                    event_callback: Union[Callable[[int, int, int], None], None] = None) -> bool:
        if enable:
            if not event_callback:
                raise Exception("缺少 composition_event_handler 参数")
            self._event_callback = AddonEventCallback(event_callback)
        else:
            self._event_callback = None

        self._use_fix_ime = self.dll.use_fix_ime(enable,
            self._event_callback)
        return self._use_fix_ime

    def use_fix_ime_for_field(self, enable: bool):
        self.dll.use_fix_ime_for_field(enable)

    def use_fix_ime_for_space(self, enable: bool):
        self.dll.use_fix_ime_for_space(enable)

    def use_fix_direct_input_caps_lock(self, enable: bool):
        self.dll.use_fix_direct_input_caps_lock(enable)

    def use_fix_direct_input_all(self, enable: bool):
        self.dll.use_fix_direct_input_all(enable)

    def hook_window(self, wm_pointer: int) -> bool:
        return self.dll.hook_window(wm_pointer)

    def unhook_window(self, wm_pointer: int) -> bool:
        return self.dll.unhook_window(wm_pointer)

    def window_is_active(self, wm_pointer: int) -> bool:
        return self.dll.window_is_active(wm_pointer)

    def window_is_mouse_capture(self, wm_pointer: int) -> bool:
        return self.dll.window_is_mouse_capture(wm_pointer)

    def ime_invoker_get(self, wm_pointer: int) -> IMEInvoker:
        return IMEInvokerMaps[self.dll.ime_invoker_get(wm_pointer)]

    def ime_is_enabled(self, wm_pointer: int) -> bool:
        return self.dll.ime_is_enabled(wm_pointer)

    def ime_enable(self, wm_pinter: int, invoker: IMEInvoker) -> bool:
        ret = self.dll.ime_enable(wm_pinter, IMEInvokerMaps[invoker])
        return ret

    def ime_disable(self, wm_pinter: int) -> bool:
        ret = self.dll.ime_disable(wm_pinter)
        return ret

    def ime_move_candidate_window(self, wm_pinter: int,
        c_l: int, c_t: int, c_w: int, c_h: int,
        e_l: int, e_t: int, e_w: int, e_h: int, show_caret: bool) -> bool:
        return self.dll.ime_move_candidate_window(wm_pinter,
            c_l, c_t, c_w, c_h,
            e_l, e_t, e_w, e_h, show_caret)

    def get_ime_data(self, addr: int) -> IMEData:
        ime_data = IMEData()

        if ct.c_size_t.from_address(addr).value:
            ime_data.composite_str = ct.c_wchar_p.from_address(addr).value.encode('utf-8').decode('utf-8')
        addr += ct.sizeof(ct.c_size_t)

        ime_data.composite_len_b = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)
        ime_data.composite_len_c = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)
        ime_data.composite_cur_i = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)
        ime_data.composite_sta_i = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)
        ime_data.composite_end_i = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)

        addr += ct.sizeof(ct.c_char) * 4

        if ct.c_size_t.from_address(addr).value:
            ime_data.result_str = ct.c_wchar_p.from_address(addr).value.encode('utf-8').decode('utf-8')
        addr += ct.sizeof(ct.c_size_t)

        ime_data.result_len_b = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)
        ime_data.result_len_c = ct.c_long.from_address(addr).value
        addr += ct.sizeof(ct.c_long)

        return ime_data

class Native(_main, _blender, _fix_ime):
    def __init__(self):
        _main.__init__(self)
        _blender.__init__(self)
        _fix_ime.__init__(self)
        self.dll: ctypes.CDLL = None
        pass

    def dll_load(self) -> bool:
        dir = Path(os.path.realpath(__file__)).parent
        # 使用副本可以避免文件锁定，方便调试，一旦锁定必须先停用插件，再生成源码，再启用插件，步骤繁琐
        for _ext in ['.dll', '.pdb']:
            _src_name = f'{dll_name}{_ext}'
            _dst_name = '_' + _src_name
            _src = dir.joinpath(_src_name)
            _dst = dir.joinpath(_dst_name)
            if _src.exists() and (not _dst.exists() or _dst.stat().st_mtime < _src.stat().st_mtime):
                try:
                    shutil.copyfile(_src, _dst)
                except:
                    printx(CCBR, f"复制 {_src_name} 到 {_dst_name} 失败")

        self.dll = ctypes.CDLL(os.path.join(dir, f'_{dll_name}.dll'))

        if self.dll is None:
            printx(CCBG, f"加载 _{dll_name}.dll 失败")
            return False
        else:
            if mark.DEBUG:
                printx(f"加载 _{dll_name}.dll 完成")

        self._dll_init__main()
        self._dll_init__blender()
        self._dll_init__fix_ime()
        return True

    def dll_unload(self) -> bool:
        if self.dll is None:
            return True
        
        if not kernel32.FreeLibrary(self.dll._handle):
            printx(CCBG, f"卸载 _{dll_name}.dll 失败")
            return False
        else:
            if mark.DEBUG:
                print(f"卸载 _{dll_name}.dll 完成")

        del self.dll

        self.dll = None

        return True


native: 'Native' = Native()
