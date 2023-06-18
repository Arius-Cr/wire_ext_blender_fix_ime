import sys
import traceback
from typing import cast, Literal

import bpy
import bpy.types

from .mark import *

from .native import native


def get_prefs(context: bpy.types.Context) -> 'WIRE_FIX_IME_Preferences':
    prefs = context.preferences.addons[__package__].preferences
    return prefs

def fix_ime_method_update(self: dict, context: bpy.types.Context):
    global _fix_ime_method, _windows

    fix_ime_method = self.get('fix_ime_method')  # int 或 str

    # 由Blender调用时，传入的值为枚举值，即 int
    if isinstance(fix_ime_method, int):
        if fix_ime_method == 0:
            fix_ime_method = 'NONE'
        elif fix_ime_method == 1:
            fix_ime_method = 'HOOK'
        elif fix_ime_method == 2:
            fix_ime_method = 'MODAL'
        else:
            raise Exception("无法识别的索引：%s", fix_ime_method)

    if fix_ime_method != _fix_ime_method:

        if DEBUG:
            print("fix_ime_method_update", fix_ime_method)

        if _fix_ime_method == 'HOOK':
            native.use_fix_ime_state(False)
            native.use_hook(False)
        elif _fix_ime_method == 'MODAL':
            WIRE_FIX_IME_OT_fix_ime.remove_key_map_item()
            _windows = None

        if fix_ime_method == 'HOOK':
            native.use_hook(True)
            native.use_fix_ime_state(True)

        elif fix_ime_method == 'MODAL':
            WIRE_FIX_IME_OT_fix_ime.add_key_map_item()
            _windows = []

        _fix_ime_method = fix_ime_method

    pass

class WIRE_FIX_IME_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__  # 必须和插件模块名称相同

    fix_ime_method: bpy.props.EnumProperty(
        items=[
            ("NONE", "无", "停用输入法状态修复", 0),
            ("HOOK", "消息钩子", "通过消息钩子获取事件并在特定事件时调整输入法状态", 1),
            ("MODAL", "模态操作", "通过模态操作获取事件并在特定事件时调整输入法状态", 2),
        ],
        name="输入法状态修复方式",
        description="",
        default='HOOK',
        update=fix_ime_method_update,
    )

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout

        column = layout.column(align=True)

        split = column.box().split(factor=0.3)
        coll = split.column()
        colr = split.column()
        row = coll.row()
        row.alignment = 'RIGHT'
        row.label(text="输入法状态修复方式")
        row = colr.row()
        row.prop(self, 'fix_ime_method', expand=True)
        row = colr.row()
        row.label(text="优先使用 “消息钩子”， 如有问题可考虑换成 “模态操作”。")

        pass


_fix_ime_method: Literal['NONE', 'HOOK', 'MODAL'] = None
# 已经启用了 WIRE_FIX_IME_OT_fix_ime 的窗口
_windows: list[bpy.types.Window] = None

class WIRE_FIX_IME_OT_fix_ime(bpy.types.Operator):
    bl_idname = "wire_fix_ime.fix_ime"
    bl_label = "修复输入法状态"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # if DEBUG:
        #     print("WIRE_FIX_IME_OT_fix_ime poll")

        if _fix_ime_method == 'MODAL':
            # 每个窗口只能运行一个当前操作的实例，暂时无法获知窗口是否销毁，但不影响
            if (window := context.window) not in _windows:
                _windows.append(window)
                return True
        return False

    def execute(self, context: bpy.types.Context) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        self.report({'ERROR'}, "本操作只能以 INVOKE 的方式调用")
        return {'CANCELLED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        if DEBUG:
            print("WIRE_FIX_IME_OT_fix_ime invoke")

        native.change_ime_state(False)  # 先禁用一次

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        # if DEBUG:
        #     print("WIRE_FIX_IME_OT_fix_ime modal")

        if _fix_ime_method == 'MODAL':
            if (event.type in [
                'LEFTMOUSE', 'RIGHTMOUSE',
                'RET', 'ESC', 'NUMPAD_ENTER', 'TAB',
            ] and event.value == 'RELEASE'):  # 必须设为 RELEASE，因为离开输入框时，不会收到 PRESS 事件
                native.change_ime_state(False)
            return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

        if DEBUG:
            print("WIRE_FIX_IME_OT_fix_ime destory")

        return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

    @staticmethod
    def add_key_map_item():
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        km.keymap_items.new(
            WIRE_FIX_IME_OT_fix_ime.bl_idname,
            type='MOUSEMOVE',
            value='ANY')

    @staticmethod
    def remove_key_map_item():
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        for _kmi in reversed(km.keymap_items):
            if _kmi.idname == WIRE_FIX_IME_OT_fix_ime.bl_idname:
                km.keymap_items.remove(_kmi)


def register():

    bpy.utils.register_class(WIRE_FIX_IME_Preferences)
    bpy.utils.register_class(WIRE_FIX_IME_OT_fix_ime)

    native.dll_load()

    native.use_debug(DEBUG)
    native.use_hook_debug(DEBUG)
    native.use_fix_ime_state_debug(DEBUG)

    native.init()

    prefs = get_prefs(bpy.context)
    fix_ime_method_update({'fix_ime_method': prefs.fix_ime_method}, bpy.context)

    pass

def unregister():

    WIRE_FIX_IME_OT_fix_ime.remove_key_map_item()

    native.use_hook(False)

    native.dll_unload()

    bpy.utils.unregister_class(WIRE_FIX_IME_OT_fix_ime)
    bpy.utils.unregister_class(WIRE_FIX_IME_Preferences)

    pass
