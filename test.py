
import typing
import bpy
import bpy.types
import time

from .mark import *
from .debug import *

'''
WIRE_OT_test_delete_speed_1：基本用时 476215700
WIRE_OT_test_delete_speed_2：基本用时 121231100
'''

class WIRE_OT_test_delete_speed_1(bpy.types.Operator):
    bl_idname = 'wire.test_delete_speed_1'
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

        print(CCBY, "删除速度测试1 用时：", _span)

        return {'FINISHED'}

class WIRE_OT_test_delete_speed_2(bpy.types.Operator):
    bl_idname = 'wire.test_delete_speed_2'
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

        print(CCBY, "删除速度测试2 用时：", _span)

        return {'FINISHED'}

def text_menu_prepend(self: bpy.types.Menu, context: bpy.types.Context):
    layout = self.layout
    layout.operator(WIRE_OT_test_delete_speed_1.bl_idname)
    layout.operator(WIRE_OT_test_delete_speed_2.bl_idname)

def register():
    if DEBUG_BUILD:
        print(CCBY, "已加载测试操作")
        bpy.utils.register_class(WIRE_OT_test_delete_speed_1)
        bpy.utils.register_class(WIRE_OT_test_delete_speed_2)
        bpy.types.VIEW3D_MT_edit_font.prepend(text_menu_prepend)

def unregister():
    if DEBUG_BUILD:
        bpy.types.VIEW3D_MT_edit_font.remove(text_menu_prepend)
        bpy.utils.unregister_class(WIRE_OT_test_delete_speed_1)
        bpy.utils.unregister_class(WIRE_OT_test_delete_speed_2)
