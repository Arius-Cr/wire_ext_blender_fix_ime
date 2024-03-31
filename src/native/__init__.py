from typing import Literal, Union, Callable
import os
import ctypes
import ctypes.wintypes as wintypes
from pathlib import Path
import shutil

from ..mark import mark
from ..printx import *

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

kernel32 = ctypes.windll.kernel32
kernel32.LoadLibraryW.argtypes = [ctypes.wintypes.LPCWSTR]
kernel32.LoadLibraryW.restype = ctypes.wintypes.HMODULE
kernel32.FreeLibrary.argtypes = [ctypes.wintypes.HMODULE]
kernel32.FreeLibrary.restype = ctypes.wintypes.BOOL

# 参数：窗口WM指针，合成事件，合成文本，光标位置
CompositionCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int)
# 参数：窗口WM指针
ButtonDownCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
# 参数：窗口WM指针
LostFocusCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
# 参数：窗口WM指针
WindowDestoryCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

class _main:
    def _dll_init__main(self):
        self.dll.use_debug.argtypes = [ctypes.c_int]
        self.dll.use_debug.restype = ctypes.c_bool

        self.dll.init.argtypes = []
        self.dll.init.restype = ctypes.c_bool

    def use_debug(self, level: int) -> bool:
        return self.dll.use_debug(level)

    def init(self) -> bool:
        return self.dll.init()

class _hook:
    def __init__(self) -> None:
        self.is_use_hook = False

    def _dll_init__hook(self):
        self.dll.use_hook_debug.argtypes = [ctypes.c_bool]
        self.dll.use_hook_debug.restype = ctypes.c_bool

        self.dll.use_hook.argtypes = [ctypes.c_bool]
        self.dll.use_hook.restype = ctypes.c_bool

        self.dll.window_associate.argtypes = [ctypes.c_void_p]
        self.dll.window_associate.restype = ctypes.c_bool

        self.dll.window_is_active.argtypes = [ctypes.c_void_p]
        self.dll.window_is_active.restype = ctypes.c_bool

        self.dll.window_is_mouse_capture.argtypes = [ctypes.c_void_p]
        self.dll.window_is_mouse_capture.restype = ctypes.c_bool

    def use_hook_debug(self, enable: int) -> bool:
        return self.dll.use_hook_debug(enable)

    def use_hook(self, enable: bool) -> bool:
        self.is_use_hook = self.dll.use_hook(enable)
        return self.is_use_hook

    def window_associate(self, wm_pointer: int) -> bool:
        return self.dll.window_associate(wm_pointer)

    def window_is_active(self, wm_pointer: int) -> bool:
        return self.dll.window_is_active(wm_pointer)

    def window_is_mouse_capture(self, wm_pointer: int) -> bool:
        return self.dll.window_is_mouse_capture(wm_pointer)

class _fix_ime:
    def _dll_init__fix_ime(self):
        self.dll.use_fix_ime_debug.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_debug.restype = ctypes.c_bool

    def use_fix_ime_debug(self, enable: bool) -> bool:
        return self.dll.use_fix_ime_debug(enable)

class _fix_ime_state:
    def __init__(self) -> None:
        self.is_use_fix_ime_state: bool = False

    def _dll_init__fix_ime_state(self):
        self.dll.use_fix_ime_state.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_state.restype = ctypes.c_bool

    def use_fix_ime_state(self, enable: bool) -> bool:
        self.is_use_fix_ime_state = self.dll.use_fix_ime_state(enable)
        return self.is_use_fix_ime_state

class _fix_ime_input:
    def __init__(self) -> None:
        self.is_use_fix_ime_input: bool = False
        self._composition_callback: ctypes._FuncPointer = None
        self._button_down_callback: ctypes._FuncPointer = None
        self._kill_focus_callback: ctypes._FuncPointer = None
        self._window_destory_callback: ctypes._FuncPointer = None

    def _dll_init__fix_ime_input(self):
        self.dll.use_fix_ime_input.argtypes = [ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.dll.use_fix_ime_input.restype = ctypes.c_bool

        self.dll.ime_input_enable.argtypes = [ctypes.c_void_p]
        self.dll.ime_input_enable.restype = ctypes.c_bool

        self.dll.ime_input_disable.argtypes = [ctypes.c_void_p]
        self.dll.ime_input_disable.restype = ctypes.c_bool

        self.dll.is_input_box_active.argtypes = [ctypes.c_void_p]
        self.dll.is_input_box_active.restype = ctypes.c_bool

        self.dll.candidate_window_position_update_font_edit.argtypes = [ctypes.c_void_p, ctypes.c_float]
        self.dll.candidate_window_position_update_font_edit.restype = ctypes.c_bool

        self.dll.candidate_window_position_update_text_editor.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.dll.candidate_window_position_update_text_editor.restype = ctypes.c_bool

        self.dll.candidate_window_position_update_console.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.dll.candidate_window_position_update_console.restype = ctypes.c_bool

    def use_fix_ime_input(self, enable: bool,
        composition_callback: Union[Callable[[int, int, str, int], None], None] = None,
        button_down_callback: Union[Callable[[int], None], None] = None,
        kill_focus_callback: Union[Callable[[int], None], None] = None,
        window_destory_callback: Union[Callable[[int], None], None] = None,
    ) -> bool:
        if enable:
            if not composition_callback:
                raise Exception("缺少 composition_event_handler 参数")

            if not button_down_callback:
                raise Exception("缺少 button_down_callback 参数")

            if not kill_focus_callback:
                raise Exception("缺少 kill_focus_callback 参数")

            if not window_destory_callback:
                raise Exception("缺少 window_destory_callback 参数")

            self._composition_callback = CompositionCallback(composition_callback)
            self._button_down_callback = ButtonDownCallback(button_down_callback)
            self._kill_focus_callback = LostFocusCallback(kill_focus_callback)
            self._window_destory_callback = WindowDestoryCallback(window_destory_callback)
        else:
            self._composition_callback = None
            self._button_down_callback = None
            self._kill_focus_callback = None
            self._window_destory_callback = None

        self.is_use_fix_ime_input = self.dll.use_fix_ime_input(enable,
            self._composition_callback,
            self._button_down_callback,
            self._kill_focus_callback,
            self._window_destory_callback,)
        return self.is_use_fix_ime_input

    def ime_input_enable(self, wm_pinter: int) -> bool:
        return self.dll.ime_input_enable(wm_pinter)

    def ime_input_disable(self, wm_pinter: int) -> bool:
        return self.dll.ime_input_disable(wm_pinter)
    
    def is_input_box_active(self, wm_pinter: int) -> bool:
        return self.dll.is_input_box_active(wm_pinter)

    def candidate_window_position_update_font_edit(self, wm_pinter: int, p: float, show_caret: bool) -> bool:
        return self.dll.candidate_window_position_update_font_edit(wm_pinter, p, show_caret)

    def candidate_window_position_update_text_editor(self, wm_pinter: int, x: int, y: int, h: int, show_caret: bool) -> bool:
        return self.dll.candidate_window_position_update_text_editor(wm_pinter, x, y, h, show_caret)

    def candidate_window_position_update_console(self, wm_pinter: int, l: int, t: int, r: int, b: int, show_caret: bool) -> bool:
        return self.dll.candidate_window_position_update_console(wm_pinter, l, t, r, b, show_caret)

class Native(_main, _hook, _fix_ime, _fix_ime_state, _fix_ime_input):
    def __init__(self):
        _main.__init__(self)
        _hook.__init__(self)
        _fix_ime.__init__(self)
        _fix_ime_state.__init__(self)
        _fix_ime_input.__init__(self)
        self.dll: ctypes.CDLL = None
        self.dll_handle = None
        pass

    def dll_load(self) -> bool:
        dir = Path(os.path.realpath(__file__)).parent
        dll_name = __package__.split('.')[0]
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

        self.dll_handle = kernel32.LoadLibraryW(os.path.join(dir, f'_{dll_name}.dll'))

        if self.dll_handle is not None:
            if mark.DEBUG:
                printx("加载 DLL 完成")
        else:
            printx(CCBR, "加载 DLL 失败")
            return False

        self.dll = ctypes.CDLL("", handle=self.dll_handle)

        self._dll_init__main()
        self._dll_init__hook()
        self._dll_init__fix_ime()
        self._dll_init__fix_ime_state()
        self._dll_init__fix_ime_input()
        return True

    def dll_unload(self) -> bool:
        if self.dll_handle is None:
            return True

        if kernel32.FreeLibrary(self.dll_handle):
            if mark.DEBUG:
                printx("卸载 DLL 完成")
        else:
            printx(CCBR, "卸载 DLL 失败")
            return False

        del self.dll
        del self.dll_handle

        self.dll = None
        self.dll_handle = None
        return True


native: 'Native' = Native()
