import typing as T
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

class _main:
    def _dll_init__main(self):
        self.dll.use_debug.argtypes = [ctypes.c_bool]
        self.dll.use_debug.restype = None
        self.dll.init.argtypes = []
        self.dll.init.restype = None

    def use_debug(self, enable: bool) -> None:
        return self.dll.use_debug(enable)

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

    def use_hook_debug(self, enable: bool) -> None:
        return self.dll.use_hook_debug(enable)

    def use_hook(self, enable: bool) -> bool:
        result = self.dll.use_hook(enable)
        if result == True:
            self.is_hook_startup = enable
        return result

class _fix_ime_state:
    def _dll_init__fix_ime_state(self):
        self.dll.use_fix_ime_state_debug.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_state_debug.restype = None

        self.dll.use_fix_ime_state.argtypes = [ctypes.c_bool]
        self.dll.use_fix_ime_state.restype = ctypes.c_bool

    def use_fix_ime_state_debug(self, enable: bool) -> None:
        return self.dll.use_fix_ime_state_debug(enable)

    def use_fix_ime_state(self, enable: bool) -> bool:
        return self.dll.use_fix_ime_state(enable)

class Native(_main, _hook, _fix_ime_state):
    def __init__(self):
        _main.__init__(self)
        _hook.__init__(self)
        _fix_ime_state.__init__(self)
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
        self._dll_init__fix_ime_state()

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
