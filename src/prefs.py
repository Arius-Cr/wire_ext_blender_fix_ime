from typing import cast, Literal, Union

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
        split_factor = 0.3

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

        # 链接

        layout.separator()

        self.draw_link(layout.column())
        pass

    def draw_link(self, layout: UILayout):
        from .main import info

        row = layout.row()
        row.operator('wm.url_open', text="GitHub", icon='URL').url = info['github']
        row.operator('wm.url_open', text="百度网盘", icon='URL').url = info['baidu']
        pass

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

class PrefsAlert(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context: bpy.types.Context) -> None:
        layout: UILayout = self.layout

        # 警告

        from .main import version_mismatch_alert

        column = layout.column()
        for _str in version_mismatch_alert:
            column.label(text=_str)

        # 链接

        layout.separator()

        Prefs.draw_link(self, layout.column())
        pass
