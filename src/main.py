from typing import cast, Literal, Union
from types import SimpleNamespace
import os
import sys
import importlib
import json
from pathlib import Path
import asyncio
import requests
from datetime import datetime, timezone, timedelta
dtfmt = '%Y-%m-%d %H:%M:%S %z'
tzbj = timezone(timedelta(hours=8))
tzlocal = datetime.now().tzinfo
dtzero = datetime.fromtimestamp(0, tzbj)

import bpy
from bpy.types import Context, Operator

from .debug.mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD

from .utils.printx import *

from .native import native

from . import bl_info
from . import prefs
from . import ime

from .prefs import get_prefs, Prefs

if DEBUG_BUILD:
    from . import dev

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

info = {
    'github': 'https://github.com/Arius-Cr/wire_ext_blender_fix_ime',
    'gitee': 'https://gitee.com/arius-cr/wire_ext_blender_fix_ime',
    'baidu': 'https://pan.baidu.com/s/1H9DxkAdmBJXLhl5Aj29Q6Q?pwd=q4e5',
    'blender_data_url': 'https://gitee.com/arius-cr/wire_ext_blender_fix_ime/raw/main/src/native/blender.py',
}

registered: bool = False

addon_data: Union['AddonData', None] = None

blender_data: Union['BlenderData', None] = None

def register() -> None:
    if DEBUG_BUILD:
        printx(CCFY, f"\n===== {__package__} start =====")

    if sys.platform != 'win32':
        raise Exception(f"{__package__}: 仅支持 Windows 平台")

    # 在 Blender 处于后台模式（--background）时插件无需工作
    if bpy.app.background:
        return

    if not native.dll_load():
        raise Exception(f"{__package__}: 无法加载 {__package__}.dll")

    # -----

    global registered, addon_data, blender_data

    bpy.utils.register_class(WIRE_FIX_IME_OT_update_blender_data)
    bpy.utils.register_class(WIRE_FIX_IME_OT_clean_blender_data)

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

    native.init()

    addon_data = AddonData()
    addon_data.load()

    blender_data = BlenderData()
    blender_data.init()
    blender_data.startup()

    fix_on()

    registered = True

    if _prefs.use_auto_update_blender_data:
        asyncio.run(blender_data.auto_update_and_restart())
    pass

def unregister() -> None:
    global registered

    if not registered:
        return

    fix_off()

    native.uninit()

    native.dll_unload()

    bpy.utils.unregister_class(WIRE_FIX_IME_OT_update_blender_data)
    bpy.utils.unregister_class(WIRE_FIX_IME_OT_clean_blender_data)

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
    ), bpy.context)
    pass

class AddonData:
    def __init__(self) -> None:
        self.blender_data_update_time: datetime = dtzero
        pass

    def load(self) -> bool:
        file_path = Path(__file__).parent.joinpath('data', 'data.json')

        if not file_path.exists():
            return False

        with open(file_path, 'r', encoding='utf-8') as file:

            json_dict = json.load(file)

            self.blender_data_update_time = datetime.strptime(json_dict['blender_data_update_time'], dtfmt)
            return True

    def save(self) -> bool:
        file_path = Path(__file__).parent.joinpath('data', 'data.json')
        os.makedirs(file_path.parent, exist_ok=True)

        with open(file_path, 'w+', encoding='utf-8') as file:

            json_dict = {}

            json_dict['blender_data_update_time'] = self.blender_data_update_time.strftime(dtfmt)

            json.dump(json_dict, file, indent=4)

            return True

class BlenderData:
    def __init__(self) -> None:
        root = Path(__file__).parent
        self.file_path_default = root.joinpath('native', 'blender.py')
        self.file_path_cache = root.joinpath('data', 'blender.py')

        self.type: Union[Literal['default', 'cache'], None] = None
        self.mtime_default: datetime = dtzero
        self.mtime_cache: datetime = dtzero

        # blender.py
        self.data: Union[dict, None] = None
        self.mtime: datetime = dtzero
        self.blender_vers: list[tuple[tuple[int, int, int], tuple[int, int, int], Union[str, None], Union[str, None]]] = []
        self.items: dict[str, int] = {}
        self.is_compatible: bool = False

        pass

    def init(self):
        # 仅为了加载默认数据中的更新时间而已
        self.load('default')
        self.mtime_default = self.mtime

        self.type = None
        self.data = None
        self.mtime = dtzero
        self.blender_vers = []
        self.items = {}
        self.is_compatible = False

    def load(self, type: Literal['default', 'cache']) -> bool:
        import importlib

        self.type = None
        self.data = None
        self.mtime = dtzero
        self.blender_vers = []
        self.items = {}
        self.is_compatible = False

        try:
            if type == 'default':
                module = importlib.import_module('.native.blender', __package__)
            elif type == 'cache':
                if not self.file_path_cache.exists():
                    if mark.DEBUG:
                        printx(CCFR, "找不到 data/blender.py 文件")
                    return False
                module = importlib.import_module('.data.blender', __package__)
        except:
            if type == 'default':  # 此为严重错误，必须不能发生
                raise TypeError(f"{__package__}: 加载默认 blender.py 失败")

            if mark.DEBUG:
                printx(CCFR, "加载 blender.py 模块失败")
            return False
        from . import bl_info

        # 设计缺陷：get_data 这个函数的内容应该放在这里，不应该放在 blender.py，
        # 否则新版本获取到旧版 blender.py 时，调用 get_data 必然失败。
        # 但这个缺陷并不严重，因为发布新版时，新的 blender.py 必然伴随发布。
        data = getattr(module, 'get_data')(bl_info['version'], bpy.app.version)

        del sys.modules[module.__name__]

        if data is None:
            if mark.DEBUG:
                printx(CCFR, "调用 get_data 返回空")
            return False

        self.type = type
        self.data = data
        self.mtime = data['mtime'] if 'mtime' in data else dtzero
        if self.type == 'cache':
            self.mtime_cache = self.mtime
        self.blender_vers = data['blender_vers']
        self.items = data['items']
        for _min, _max, *_ in self.blender_vers:
            if _min <= bpy.app.version <= _max:
                self.is_compatible = True

        return True

    def apply(self) -> bool:
        if not self.is_compatible:
            if mark.DEBUG:
                printx(CCBA, "不能设置不兼容的数据")
            return False

        for _name, _value in self.items.items():
            success = native.blender_data_set(_name, _value)
            if not success:
                if mark.DEBUG:
                    printx(CCBA, "设置数据失败：", _name)
                return False

        return True

    async def fetch(self) -> bool:
        '''
        从 Gitee 获取最新的 blender.json 文件并保存到指定目录中。
        获取并保存成功则返回 True，否则返回 False。
        '''
        try:
            url = info['blender_data_url']
            res = requests.get(url)
            if res.status_code == 200:
                text = res.text
                dir = self.file_path_cache.parent
                os.makedirs(dir, exist_ok=True)
                with open(self.file_path_cache, 'w+') as file:
                    file.write(text)
                    return True
            return False
        except:
            return False

    async def update(self) -> bool:
        '''
        下载远端的 blender.py 文件，加载下载的 blender.py 文件并应用。
        '''
        success = await self.fetch()
        if not success:
            if mark.DEBUG:
                printx(CCFA, "获取 blender.py 失败")
            return False

        addon_data.blender_data_update_time = datetime.now(tzbj)
        addon_data.save()

        return self.startup()

    async def update_and_restart(self):
        await blender_data.update()
        fix_off()
        fix_on()
        pass

    async def auto_update(self) -> Union[bool, None]:
        # 启用插件时，先执行一次更新
        _prefs = get_prefs(bpy.context)
        if _prefs.enable_from_disable:
            _prefs.enable_from_disable = False
            if mark.DEBUG:
                printx(CCFA, "自动更新 blender.py：初次启动")
            return await blender_data.update()

        # 当前离上次更新超过三天则自动执行一次更新
        now = datetime.now(tzbj)
        delta = now - addon_data.blender_data_update_time
        if delta.days >= 3:
            if mark.DEBUG:
                printx(CCFA, f"自动更新 blender.py：计划任务 (已间隔 {delta.days} 天)")
            return await blender_data.update()

        return None

    async def auto_update_and_restart(self):
        await blender_data.auto_update()
        fix_off()
        fix_on()
        pass

    def startup(self) -> bool:
        '''
        加载下载或默认的 blender.py 文件并应用。
        '''
        load_cache = False
        _success = self.load('cache')
        if not _success:
            return self.reset()
        else:
            if self.mtime_default > self.mtime:
                if mark.DEBUG:
                    printx(CCFA, "本地比远端 blender.py 更新")
            else:
                load_cache = True

        if not load_cache:
            self.load('default')

        self.apply()  # 应用可以失败，譬如当前为不兼容的 Blender 时

        return True

    def reset(self) -> bool:
        '''
        删除下载的 blender.py 文件，加载默认的 blender.py 并应用。
        '''
        if self.file_path_cache.exists():
            os.unlink(self.file_path_cache)
        self.mtime_cache = dtzero

        addon_data.blender_data_update_time = dtzero
        addon_data.save()

        self.load('default')

        self.apply()
        return True

class WIRE_FIX_IME_OT_update_blender_data(Operator):
    bl_idname = 'wire_fix_ime.update_blender_data'
    bl_label = "更新内存偏移量"
    bl_description = "获取插件所需 Blender 内部数据的内存偏移量"

    def execute(self, context: Context) -> Union[Literal['RUNNING_MODAL'], Literal['CANCELLED'], Literal['FINISHED'], Literal['PASS_THROUGH'], Literal['INTERFACE']]:
        asyncio.run(blender_data.update_and_restart())
        return {'FINISHED'}

class WIRE_FIX_IME_OT_clean_blender_data(Operator):
    bl_idname = 'wire_fix_ime.clean_blender_data'
    bl_label = "清除内存偏移量"
    bl_description = "清除下载的内存偏移量文件"

    @classmethod
    def poll(cls, context: Context = None) -> bool:
        return blender_data.file_path_cache.exists()

    def execute(self, context: Context) -> Union[Literal['RUNNING_MODAL'], Literal['CANCELLED'], Literal['FINISHED'], Literal['PASS_THROUGH'], Literal['INTERFACE']]:
        blender_data.reset()
        fix_off()
        fix_on()
        return {'FINISHED'}
