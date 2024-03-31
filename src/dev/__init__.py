
import typing
import bpy
import bpy.types
import time
import traceback
import sys

from ..debug.mark import mark
from ..utils.printx import *


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

'''
WIRE_FIX_IME_OT_test_delete_speed_1：基本用时 476215700
WIRE_FIX_IME_OT_test_delete_speed_2：基本用时 121231100
'''

class WIRE_FIX_IME_PT_text_editor_info(bpy.types.Panel):
    bl_idname = 'WIRE_FIX_IME_PT_text_editor_info'
    bl_label = "信息（仅用于测试）"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Text'
    '''
    用于显示文本编辑器的光标的位置，仅测试用
    '''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        space = cast(bpy.types.SpaceTextEditor, context.space_data)
        area = context.area
        region: bpy.types.Region = None
        for _r in area.regions:
            if _r.type == 'WINDOW':
                region = _r
                break
        window = context.window
        text = space.text

        # offset 的原点在区块左下角
        offset_x, offset_y = space.region_location_from_cursor(
            text.current_line_index, text.current_character)

        client_x = region.x + offset_x
        client_y = window.height - (region.y + offset_y)

        layout.label(text="光标位置（相对区块左下角）：")
        layout.label(text="%d, %d" % (offset_x, offset_y))
        layout.label(text="光标位置（相对窗口左上角）：")
        layout.label(text="%d, %d" % (client_x, client_y))

        layout.separator()

        layout.label(text="region x, y：")
        layout.label(text="%d, %d" % (region.x, region.y))
        layout.label(text="region w, h：")
        layout.label(text="%d, %d" % (region.width, region.height))

        layout.separator()

        layout.label(text="area x, y：")
        layout.label(text="%d, %d" % (area.x, area.y))
        layout.label(text="area w, h：")
        layout.label(text="%d, %d" % (area.width, area.height))

        layout.separator()

        layout.label(text="window x, y：")
        layout.label(text="%d, %d" % (window.x, window.y))
        layout.label(text="window w, h：")
        layout.label(text="%d, %d" % (window.width, window.height))

        pass

class WIRE_FIX_IME_OT_test_delete_speed_1(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.test_delete_speed_1'
    bl_label = "删除速度测试1"
    bl_description = "删除速度测试1"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        _text = "删除速度测试删除速度测试删除速度测试删除速度测试"
        _len = len(_text)
        _statr = time.perf_counter_ns()

        for _ in range(100):  # 测试100次
            bpy.ops.font.text_insert(text=_text)
            for _ in range(_len):  # 删除之前的输入
                bpy.ops.font.delete('EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')

        _end = time.perf_counter_ns()
        _span = _end - _statr

        printx(CCBY, "删除速度测试1 用时：", _span)

        return {'FINISHED'}

class WIRE_FIX_IME_OT_test_delete_speed_2(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.test_delete_speed_2'
    bl_label = "删除速度测试2"
    bl_description = "删除速度测试2"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        _text = "删除速度测试删除速度测试删除速度测试删除速度测试"
        _len = len(_text)
        _statr = time.perf_counter_ns()

        for _ in range(100):  # 测试100次
            bpy.ops.font.text_insert(text=_text)
            for _ in range(_len):  # 删除之前的输入
                bpy.ops.font.move_select('EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')
            bpy.ops.font.delete('EXEC_REGION_WIN', type='SELECTION')

        _end = time.perf_counter_ns()
        _span = _end - _statr

        printx(CCBY, "删除速度测试2 用时：", _span)

        return {'FINISHED'}

def VIEW3D_MT_edit_font_draw_func(self: bpy.types.Menu, context: bpy.types.Context):
    layout = self.layout
    layout.operator(WIRE_FIX_IME_OT_test_delete_speed_1.bl_idname)
    layout.operator(WIRE_FIX_IME_OT_test_delete_speed_2.bl_idname)

class WIRE_FIX_IME_OT_test_insert(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.test_insert'
    bl_label = "插入文本"
    # bl_options = {'UNDO'} # 必须不能有 UNOD 否则无法在编辑模式使用文本编辑器时撤销输入

    def execute(self, context: bpy.types.Context) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        bpy.ops.text.insert(text="A")
        bpy.ops.text.delete(type='PREVIOUS_CHARACTER')
        bpy.ops.text.insert(True, text="ABC") # 最后一个插入必须使用 UNDO
        return {'FINISHED'}

    @classmethod
    def add_key_map_item(clss) -> None:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Text Generic', space_type='TEXT_EDITOR', region_type='WINDOW')
        km.keymap_items.new(clss.bl_idname, type='I', value='PRESS',
                            ctrl=True, shift=False, alt=False, oskey=False)

    @classmethod
    def remove_key_map_item(clss) -> None:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        for _kmi in reversed(km.keymap_items):
            if _kmi.idname == clss.bl_idname:
                km.keymap_items.remove(_kmi)

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

def register():
    if mark.DEBUG_BUILD:
        printx(CCBY, "已加载测试相关功能")
        bpy.utils.register_class(WIRE_FIX_IME_PT_text_editor_info)
        bpy.utils.register_class(WIRE_FIX_IME_OT_test_delete_speed_1)
        bpy.utils.register_class(WIRE_FIX_IME_OT_test_delete_speed_2)
        bpy.types.VIEW3D_MT_edit_font.prepend(VIEW3D_MT_edit_font_draw_func)
        bpy.utils.register_class(WIRE_FIX_IME_OT_test_insert)
        WIRE_FIX_IME_OT_test_insert.add_key_map_item()

def unregister():
    if mark.DEBUG_BUILD:
        WIRE_FIX_IME_OT_test_insert.remove_key_map_item()
        bpy.utils.unregister_class(WIRE_FIX_IME_OT_test_insert)
        bpy.types.VIEW3D_MT_edit_font.remove(VIEW3D_MT_edit_font_draw_func)
        bpy.utils.unregister_class(WIRE_FIX_IME_OT_test_delete_speed_2)
        bpy.utils.unregister_class(WIRE_FIX_IME_OT_test_delete_speed_1)
        bpy.utils.unregister_class(WIRE_FIX_IME_PT_text_editor_info)
