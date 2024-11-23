from typing import cast, Literal, Union
from datetime import datetime
import asyncio

import bpy
from bpy.types import Context, UILayout

from .debug.mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD
DEBUG = mark.DEBUG

from .utils.printx import *

from .native import native

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

def register():
    bpy.utils.register_class(Prefs)

def unregister():
    bpy.utils.unregister_class(Prefs)

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

def get_prefs(context: bpy.types.Context) -> 'Prefs':
    return context.preferences.addons[__package__].preferences

class Prefs(bpy.types.AddonPreferences):
    bl_idname = __package__  # 必须和插件模块名称相同

    # 该属性用于检测插件是从停用状态到启用状态，还是从启用状态到启用状态（Blender 加载已启用的插件时）
    enable_from_disable: bpy.props.BoolProperty(
        name="停用->启用",
        description="(仅供内部使用)",
        default=True,
        options={'HIDDEN'}
    )

    def use_auto_update_blender_data_update(self, context: Context):
        from .main import blender_data
        if self.use_auto_update_blender_data:
            asyncio.run(blender_data.auto_update_and_restart())

    use_auto_update_blender_data: bpy.props.BoolProperty(
        name="自动更新内存偏移数据",
        description="初始启动插件或每隔三天自动更新内存偏移数据。",
        default=True if not DEBUG_BUILD else False,
        options={'HIDDEN'},
        update=use_auto_update_blender_data_update,
    )

    def use_fix_ime_update(self, context: Context):
        from .ime import Manager
        Manager.option_update(self, context)

    use_fix_ime_for_field: bpy.props.BoolProperty(
        name="增强输入框对输入法的支持",
        description="增强 Blender 输入框对输入法的支持",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_for_space: bpy.props.BoolProperty(
        name="增强编辑器对输入法的支持",
        description="增强 Blender 编辑器对输入法的支持",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_font_edit: bpy.props.BoolProperty(
        name="3D视图 - 文本物体编辑模式",
        description="启用后，用户可以在【3D视图】的【文本物体】的【编辑模式】中使用输入法",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_text_editor: bpy.props.BoolProperty(
        name="文本编辑器",
        description="启用后，用户可以在【文本编辑器】中使用输入法",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_console: bpy.props.BoolProperty(
        name="控制台",
        description="启用后，用户可以在【控制台】中使用输入法",
        default=True,
        update=use_fix_ime_update,
    )

    candidate_window_percent: bpy.props.FloatProperty(
        name="输入法候选窗水平位置",
        description="设置输入法候选窗相对3D视图底部左侧的位置，最终位置会受系统调整",
        default=0.4, min=0, max=1,
        subtype='FACTOR',
    )

    def use_debug_update(self, context: Context) -> None:
        mark.DEBUG = self.use_debug
        global DEBUG
        DEBUG = self.use_debug

        native.use_debug(DEBUG)
        native.use_fix_ime_debug(DEBUG)

        from . import ime
        ime.use_debug_update()
        pass

    # 仅用于 DEBUG 版
    use_debug: bpy.props.BoolProperty(
        name="启用调试",
        description="将插件的调试信息输出到控制台",
        default=True if DEBUG_BUILD else False,
        update=use_debug_update,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout: UILayout = self.layout.column()

        # 选项

        self.draw_options(layout.column())

        # 数据

        layout.separator()

        self.draw_data(layout.column())

        # 链接

        layout.separator()

        self.draw_link(layout.column())

        pass

    def draw_options(self, layout: UILayout):
        split_factor = 0.3

        from .main import blender_data
        layout.enabled = blender_data.is_compatible

        _for_field = self.use_fix_ime_for_field
        _for_space = self.use_fix_ime_for_space

        column = layout.column(align=True)

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.prop(self, 'use_fix_ime_for_field')

        layout.separator()

        _for_field = True

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = _for_field
        rowr.prop(self, 'use_fix_ime_for_space')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = _for_field and _for_space
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_font_edit')

        split = column.split(factor=split_factor)
        split.active = _for_field and _for_space and self.use_fix_ime_font_edit
        rowl = split.row()
        rowl.alignment = 'RIGHT'
        rowl.label(text="输入法候选窗水平位置")
        rowr = split.row()
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'candidate_window_percent', text="")

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = _for_field and _for_space
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_text_editor')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = _for_field and _for_space
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_console')

        # 调试

        if DEBUG_BUILD:

            column = layout.column(align=True)

            split = column.split(factor=split_factor)
            rowl = split.row()
            rowr = split.row()
            rowr.prop(self, 'use_debug')

    def draw_data(self, layout: UILayout):
        from .main import (
            tzlocal, dtzero,
            addon_data,
            blender_data,
            WIRE_FIX_IME_OT_update_blender_data,
            WIRE_FIX_IME_OT_clean_blender_data,
        )

        row = layout.row()
        rowrow = row.row(align=True)
        rowrow.operator(WIRE_FIX_IME_OT_update_blender_data.bl_idname, text='更新内存偏移数据')
        rowrow.prop(self, 'use_auto_update_blender_data', text="自动更新", toggle=True)
        row.operator(WIRE_FIX_IME_OT_clean_blender_data.bl_idname, text='清除内存偏移数据')

        _datetime = blender_data.mtime_default.astimezone(tzlocal)
        layout.label(text="本地版本: " + _datetime.strftime('%Y-%m-%d %H:%M') +
                     ("   [正在使用]" if blender_data.type == 'default' else ""))

        if blender_data.mtime_cache != dtzero:
            _datetime = blender_data.mtime_cache.astimezone(tzlocal)
            layout.label(text="远端版本: " + _datetime.strftime('%Y-%m-%d %H:%M') +
                        ("   [正在使用]" if blender_data.type == 'cache' else ""))
        else:
            layout.label(text="远端版本: (未获取)")

        if addon_data.blender_data_update_time != dtzero:
            _datetime = addon_data.blender_data_update_time.astimezone(tzlocal)
            layout.label(text="最近更新: " + _datetime.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            layout.label(text="最近更新: (未更新)")

        if not blender_data.is_compatible:
            col = layout.column()
            col.alert = True
            col.label(text=f"插件的当前版本不兼容 Blender {'.'.join(map(str, bpy.app.version))}", icon='ERROR')
            col.label(text="你可以尝试点击【更新内存偏移数据】或自行更新插件", icon='INFO')

        layout.label(text="当前支持的 Blender 版本:")
        for _min, _max, _date, _hash in blender_data.blender_vers:
            if _max[2] == 99:
                _max = (_max[0], _max[1], 'X')
            if not _date:
                layout.label(text=f"{'.'.join(map(str, _min))} - {'.'.join(map(str, _max))}")
            else:
                _dev = f" (开发版 {_date} {_hash})" if _date is not None else ""
                layout.label(text=f"{'.'.join(map(str, _max))}{_dev}")

        pass

    def draw_link(self, layout: UILayout):
        from .main import info

        row = layout.row()
        row.operator('wm.url_open', text="GitHub", icon='URL').url = info['github']
        row.operator('wm.url_open', text="Gitee", icon='URL').url = info['gitee']
        row.operator('wm.url_open', text="百度网盘", icon='URL').url = info['baidu']
        pass
