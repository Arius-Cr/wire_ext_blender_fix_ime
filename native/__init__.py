from typing import Literal
import os
import ctypes
import ctypes.wintypes as wintypes

from .. mark import *

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

kernel32 = ctypes.windll.kernel32
kernel32.LoadLibraryW.argtypes = [ctypes.wintypes.LPCWSTR]
kernel32.LoadLibraryW.restype = ctypes.wintypes.HMODULE
kernel32.FreeLibrary.argtypes = [ctypes.wintypes.HMODULE]
kernel32.FreeLibrary.restype = ctypes.wintypes.BOOL

EDITOR_TYPE = {
    'font': 1,
    'text': 2,
    'console': 3,
}

class _main:
    def _dll_init__main(self):
        self.dll.use_debug.argtypes = [ctypes.c_int]
        self.dll.use_debug.restype = None

        self.dll.init.argtypes = []
        self.dll.init.restype = None

    def use_debug(self, level: int) -> None:
        return self.dll.use_debug(level)

    def init(self) -> None:
        return self.dll.init()

class _hook:
    def __init__(self) -> None:
        self.is_hook_startup = False

    def _dll_init__hook(self):
        self.dll.use_hook_debug.argtypes = [ctypes.c_bool]
        self.dll.use_hook_debug.restype = None

        self.dll.use_hook.argtypes = [ctypes.c_bool]
        self.dll.use_hook.restype = ctypes.c_bool

        self.dll.window_associate_pointer.argtypes = [ctypes.c_void_p]
        self.dll.window_associate_pointer.restype = ctypes.c_bool

        self.dll.window_is_active.argtypes = [ctypes.c_void_p]
        self.dll.window_is_active.restype = ctypes.c_bool

    def use_hook_debug(self, enable: int) -> None:
        return self.dll.use_hook_debug(enable)

    def use_hook(self, enable: bool) -> bool:
        result = self.dll.use_hook(enable)
        if result == True:
            self.is_hook_startup = enable
        return result

    def window_associate_pointer(self, pointer: int) -> None:
        return self.dll.window_associate_pointer(pointer)

    def window_is_active(self, pointer: int) -> None:
        return self.dll.window_is_active(pointer)

class _fix_ime:
    def _dll_init__fix_ime(self):
        self.dll.use_fix_ime_debug.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_debug.restype = None

    def use_fix_ime_debug(self, enable: bool) -> None:
        return self.dll.use_fix_ime_debug(enable)

class _fix_ime_state:
    def _dll_init__fix_ime_state(self):
        self.dll.use_fix_ime_state.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_state.restype = ctypes.c_bool

    def use_fix_ime_state(self, enable: bool) -> bool:
        return self.dll.use_fix_ime_state(enable)

class _fix_ime_input:
    def _dll_init__fix_ime_input(self):
        self.dll.use_fix_ime_input.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_input.restype = ctypes.c_bool

        self.dll.ime_input_enable.argtypes = [ctypes.c_void_p]
        self.dll.ime_input_enable.restype = ctypes.c_bool

        self.dll.ime_input_disable.argtypes = [ctypes.c_void_p]
        self.dll.ime_input_disable.restype = ctypes.c_bool

        self.dll.ime_text_get.argtypes = []
        self.dll.ime_text_get.restype = ctypes.c_wchar_p

        self.dll.candidate_window_position_update_font_edit.argtypes = [ctypes.c_void_p, ctypes.c_float]
        self.dll.candidate_window_position_update_font_edit.restype = ctypes.c_bool

        self.dll.candidate_window_position_update_text_editor.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        self.dll.candidate_window_position_update_text_editor.restype = ctypes.c_bool

        self.dll.candidate_window_position_update_console.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.dll.candidate_window_position_update_console.restype = ctypes.c_bool

    def use_fix_ime_input(self, enable: bool) -> bool:
        return self.dll.use_fix_ime_input(enable)

    def ime_input_enable(self, wm_pinter: int) -> bool:
        return self.dll.ime_input_enable(wm_pinter)

    def ime_input_disable(self, wm_pinter: int) -> bool:
        return self.dll.ime_input_disable(wm_pinter)

    def ime_text_get(self) -> str:
        # 从Windows传来的是UTF-16字符串，需要编码为UTF-8
        return self.dll.ime_text_get().encode('utf-8').decode('utf-8')

    def ime_text_caret_pos_get(self) -> int:
        # 从Windows传来的是UTF-16字符串，需要编码为UTF-8
        return self.dll.ime_text_caret_pos_get()

    def candidate_window_position_update_font_edit(self, wm_pinter: int, p: float) -> bool:
        return self.dll.candidate_window_position_update_font_edit(wm_pinter, p)

    def candidate_window_position_update_text_editor(self, wm_pinter: int, x: int, y: int) -> bool:
        return self.dll.candidate_window_position_update_text_editor(wm_pinter, x, y)

    def candidate_window_position_update_console(self, wm_pinter: int, x: int, y: int, l: int, t: int, r: int, b: int) -> bool:
        return self.dll.candidate_window_position_update_console(wm_pinter, x, y, l, t, r, b)

class Native(_main, _hook, _fix_ime, _fix_ime_state, _fix_ime_input):
    def __init__(self):
        _main.__init__(self)
        _hook.__init__(self)
        _fix_ime.__init__(self)
        _fix_ime_state.__init__(self)
        _fix_ime_input.__init__(self)
        self.dll: ctypes.CDLL = None
        self.dll_handle = None
        self.dll_loaded = False
        pass

    def dll_load(self):
        dir = os.path.dirname(os.path.realpath(__file__))
        dll_path = os.path.join(dir, 'native.dll')
        if DEBUG:
            # 使用副本可以避免文件锁定，方便调试，一旦锁定必须先停用插件，再生成源码，再启用插件，步骤繁琐
            dll_dest = os.path.join(dir, '_native.dll')
            try:
                os.system('copy "%s" "%s" > nul' % (dll_path, dll_dest))
                dll_path = dll_dest
            except:
                print("复制 native.dll 为 _native.dll 失败")

        self.dll_handle = kernel32.LoadLibraryW(dll_path)

        if self.dll_handle is not None:
            if DEBUG:
                print("加载 DLL 完成")
        else:
            print("加载 DLL 失败")

        self.dll = ctypes.CDLL("", handle=self.dll_handle)

        self.dll_loaded = True

        self._dll_init__main()
        self._dll_init__hook()
        self._dll_init__fix_ime()
        self._dll_init__fix_ime_state()
        self._dll_init__fix_ime_input()

    def dll_unload(self):
        if self.dll_handle is None:
            return

        if kernel32.FreeLibrary(self.dll_handle):
            if DEBUG:
                print("卸载 DLL 完成")
        else:
            print("卸载 DLL 失败")

        del self.dll
        del self.dll_handle

        self.dll = None
        self.dll_handle = None
        self.dll_loaded = False


native: 'Native' = Native()
