from typing import cast, Literal, Union
from types import SimpleNamespace
import sys
import os

import bpy
import bpy.types

from .mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD
DEBUG = mark.DEBUG

from .printx import *

from .native import native

if DEBUG_BUILD:
    from .test import register as test_register, unregister as test_unregister


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


def use_debug_update(self: Union['WIRE_FIX_Preferences', SimpleNamespace], context: bpy.types.Context):
    use_debug = self.use_debug

    mark.DEBUG = use_debug
    global DEBUG
    DEBUG = use_debug

    native.use_debug(DEBUG)
    native.use_hook_debug(DEBUG)
    native.use_fix_ime_debug(DEBUG)

def use_fix_ime_update(self: Union['WIRE_FIX_Preferences', SimpleNamespace], context: bpy.types.Context):
    use_fix_ime_input_update(self, context)

    use_fix_ime_state = self.use_fix_ime_state
    use_fix_ime_input = self.use_fix_ime_input

    if use_fix_ime_state:
        native.use_fix_ime_state(True)
        if use_fix_ime_input:
            fix_ime_input_enable()
        else:
            fix_ime_input_disable()
    else:
        native.use_fix_ime_state(False)
        fix_ime_input_disable()  # 必须关闭

def use_fix_ime_input_update(self: Union['WIRE_FIX_Preferences', SimpleNamespace], context: bpy.types.Context):
    global use_fix_ime_input_is_valid

    use_fix_ime_input_is_valid = (self.use_fix_ime_state and
            self.use_fix_ime_input and (
            self.use_fix_ime_input_font_edit or
            self.use_fix_ime_input_text_editor or
            self.use_fix_ime_input_console))
    
    if DEBUG:
        printx(CCFY, "use_fix_ime_input_is_valid:", use_fix_ime_input_is_valid)

def use_header_extend(self: Union['WIRE_FIX_Preferences', SimpleNamespace], context: bpy.types.Context):
    global TEXT_HT_header_extend_appended
    global CONSOLE_HT_header_extend_appended

    use_header_extend_text_editor = self.use_header_extend_text_editor
    use_header_extend_console = self.use_header_extend_console

    if DEBUG:
        printx("use_header_extend_text_editor:", use_header_extend_text_editor)
        printx("use_header_extend_console:", use_header_extend_console)

    if use_header_extend_text_editor:
        if not TEXT_HT_header_extend_appended:
            bpy.types.TEXT_HT_header.append(header_extend_draw_func)
            TEXT_HT_header_extend_appended = True
    else:
        if TEXT_HT_header_extend_appended:
            bpy.types.TEXT_HT_header.remove(header_extend_draw_func)
            TEXT_HT_header_extend_appended = False

    if use_header_extend_console:
        if not CONSOLE_HT_header_extend_appended:
            bpy.types.CONSOLE_HT_header.append(header_extend_draw_func)
            CONSOLE_HT_header_extend_appended = True
    else:
        if CONSOLE_HT_header_extend_appended:
            bpy.types.CONSOLE_HT_header.remove(header_extend_draw_func)
            CONSOLE_HT_header_extend_appended = False

def get_prefs(context: bpy.types.Context) -> 'WIRE_FIX_Preferences':
    return context.preferences.addons[__package__].preferences

class WIRE_FIX_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__  # 必须和插件模块名称相同

    use_fix_ime_state: bpy.props.BoolProperty(
        name="自动管理输入法状态",
        description="启用后，当用户激活输入框时，插件会自动启用输入法，退出输入框时，插件会自动停用输入法",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input: bpy.props.BoolProperty(
        name="使用输入法输入文字",
        description="启用后，可以在某些情况下直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_font_edit: bpy.props.BoolProperty(
        name="文本物体编辑模式",
        description="启用后，可以在【3D视图】的【文本物体】的【编辑模式】中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_input_update,
    )

    use_fix_ime_input_text_editor: bpy.props.BoolProperty(
        name="文本编辑器",
        description="启用后，可以在【文本编辑器】中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_input_update,
    )

    use_fix_ime_input_console: bpy.props.BoolProperty(
        name="控制台",
        description="启用后，可以在【控制台】中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_input_update,
    )

    candidate_window_percent: bpy.props.FloatProperty(
        name="候选窗口水平位置",
        description="候选窗口的左侧在屏幕工作区底部的水平位置，最终位置会受系统调整",
        default=0.4,
        min=0,
        max=1,
        subtype='FACTOR',
    )

    use_header_extend_text_editor: bpy.props.BoolProperty(
        name="文本编辑器状态提示",
        description="启用后，在【文本编辑器】的标题栏中显示“使用输入法输入文字”功能相关的状态提示",
        default=True if DEBUG_BUILD else False,
        update=use_header_extend,
    )

    use_header_extend_console: bpy.props.BoolProperty(
        name="控制台状态提示",
        description="启用后，在【控制台】的标题栏中显示“使用输入法输入文字”功能相关的状态提示",
        default=True if DEBUG_BUILD else False,
        update=use_header_extend,
    )

    use_debug: bpy.props.BoolProperty(
        name="启用调试",
        description="启用调试模式，运行信息将会输出到控制台",
        default=True if DEBUG_BUILD else False,
        update=use_debug_update,
    )

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout.column()
        split_factor = 0.3

        column = layout.column(align=True)

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.prop(self, 'use_fix_ime_state')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = self.use_fix_ime_state
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_input')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = self.use_fix_ime_state and self.use_fix_ime_input
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_input_font_edit')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowl.alignment = 'RIGHT'
        rowl.label(text="候选窗口水平位置")
        rowr = split.row()
        rowr.active = self.use_fix_ime_state and self.use_fix_ime_input and self.use_fix_ime_input_font_edit
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'candidate_window_percent', text="")

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = self.use_fix_ime_state and self.use_fix_ime_input
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_input_text_editor')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = self.use_fix_ime_state and self.use_fix_ime_input
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_fix_ime_input_console')

        # 界面

        layout.separator()

        column = layout.column(align=True)

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowl.alignment = 'RIGHT'
        rowl.label(text="显示状态提示")
        rowr = split.row()
        rowr.active = self.use_fix_ime_state and self.use_fix_ime_input
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_header_extend_text_editor', text="文本编辑器")

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.active = self.use_fix_ime_state and self.use_fix_ime_input
        rowr.separator(factor=1.5)
        rowr.separator(factor=1.5)
        rowr.prop(self, 'use_header_extend_console', text="控制台")

        # 调试

        layout.separator()

        column = layout.column(align=True)

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.prop(self, 'use_debug')

        split = column.split(factor=split_factor)
        rowl = split.row()
        rowr = split.row()
        rowr.alert = True
        rowr.separator(factor=1.5)
        rowr.label(text="平时不要开启调试，会影响性能")


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


_fix_ime_input_enabled: bool = False

def fix_ime_input_enable():
    global _fix_ime_input_enabled
    if _fix_ime_input_enabled:
        return

    native.use_fix_ime_input(True,
        Watcher.composition_callback,
        Watcher.button_press_callback,
        Watcher.kill_focus_callback,
        Watcher.window_destory_callback)

    _fix_ime_input_enabled = True
    pass

def fix_ime_input_disable():
    global _fix_ime_input_enabled
    if not _fix_ime_input_enabled:
        return

    native.use_fix_ime_input(False)

    for window in list(watchers.keys()):
        watchers[window].close()

    watchers.clear()

    _fix_ime_input_enabled = False
    pass


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


use_temp_override: bool = False

use_fix_ime_input_is_valid: bool = False

watchers: dict[bpy.types.Window, 'Watcher'] = {}

EditorType = Literal['font', 'text', 'console']
CompositionEventMaps = {0: 'START', 1: 'UPDATE', 2: 'FINISH', 3: 'CANCEL'}
CompositionEventType = Literal['START', "UPDATE", 'FINISH', 'CANCEL']

class Watcher():
    def __init__(self) -> None:
        self.window: bpy.types.Window = None
        self.hwnd: int = None
        self.wm_pointer: int = None

        # 当前输入法是否已经启动
        self.ime_enabled = False
        self.editor_type: EditorType = None
        self.area = None
        self.region = None
        self.space = None

        self.op_insert = None
        self.op_delete = None
        self.op_move = None
        self.op_select = None

        self.inputing: bool = False
        self.events: list[tuple[CompositionEventType, str, int]] = []
        self.input_handler: WIRE_OT_fix_ime_input_handler = None
        self.input_handler_start_timer: function = None
        self.input_handelr_event_timer: bpy.types.Timer = None

        # 上次合成文本的长度
        self.length: int = 0
        # 上次合成文本中光标相对末尾的字符数
        self.move_times: int = 0

    def start(self, context: bpy.types.Context):
        window = context.window
        watchers[window] = self

        self.window = window
        self.wm_pointer = window.as_pointer()

        # 将窗口指针和窗口句柄绑定
        native.window_associate_pointer(self.wm_pointer)

        if DEBUG:
            printx(CCBY, "鼠标位置检查器启动 (现有: %d)：%X (wm)" % (
                len(watchers), self.wm_pointer))
        pass

    def close(self):
        if self.window in watchers:
            watchers.pop(self.window)
        if DEBUG:
            printx(CCFY, "鼠标位置检查器关闭 (剩余：%d)：%X (wm)" % (
                len(watchers), self.wm_pointer))
        pass

    def mouse_move(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        # 如果用户激活了输入控件，则 MOUSEMOVE 事件不会被触发，因此不用担心和输入控件中的输入法状态的冲突。
        if not self.inputing:
            # 因为任务栏中的输入法状态仅反映活动窗口的，所以仅在窗口处于活动状态时维护输入法状态
            if native.window_is_active(self.wm_pointer):
                self.update_ime_state(context, event)

    def update_ime_state(self, context: bpy.types.Context, event: bpy.types.Event):
        # 鼠标进入符合条件的区块则启用输入法，否则停用输入法

        prefs = get_prefs(context)
        mouse_x = event.mouse_x
        mouse_y = event.mouse_y

        editor_type: EditorType = None
        area: bpy.types.Area = None
        region: bpy.types.Region = None
        space: bpy.types.Space = None

        if not editor_type and prefs.use_fix_ime_input_font_edit:
            _obj = context.active_object
            if _obj and _obj.type == 'FONT' and _obj.mode == 'EDIT':
                for _area in context.screen.areas.values():
                    if _area.type == 'VIEW_3D':
                        for _region in _area.regions.values():
                            if _region.type == 'WINDOW':
                                break
                        if (_region.x <= mouse_x <= _region.x + _region.width and
                            _region.y <= mouse_y <= _region.y + _region.height):
                            editor_type = 'font'
                            area = _area
                            region = _region
                            space = _area.spaces[0]
                            break

        if not editor_type and prefs.use_fix_ime_input_text_editor:
            for _area in context.screen.areas.values():
                if _area.type == 'TEXT_EDITOR':
                    _space: bpy.types.SpaceTextEditor = _area.spaces[0]
                    if _space.text:
                        for _region in _area.regions.values():
                            if _region.type == 'WINDOW':
                                break
                        if (_region.x <= mouse_x <= _region.x + _region.width and
                            _region.y <= mouse_y <= _region.y + _region.height):
                            editor_type = 'text'
                            area = _area
                            region = _region
                            space = _area.spaces[0]
                            break

        if not editor_type and prefs.use_fix_ime_input_console:
            for _area in context.screen.areas.values():
                if _area.type == 'CONSOLE':
                    for _region in _area.regions.values():
                        if _region.type == 'WINDOW':
                            break
                    if (_region.x <= mouse_x <= _region.x + _region.width and
                        _region.y <= mouse_y <= _region.y + _region.height):
                        editor_type = 'console'
                        area = _area
                        region = _region
                        space = _area.spaces[0]
                        break

        if editor_type:
            # 检测到符合条件的区块，如果当前没有启用输入法或当前鼠标所在空间和之前不同，则启用输入法
            if not self.ime_enabled or space != self.space:
                if DEBUG:
                    printx(CBHIT2, "在区块中启用输入法：%s" % space.type)
                native.ime_input_enable(self.wm_pointer)
                self.ime_enabled = True
                self.editor_type = editor_type
                self.area = area
                self.region = region
                self.space = space
                self.op_insert = None  # 延迟到 event_process 中再初始化
                self.op_delete = None
                self.op_move = None
                self.op_delete = None
                if DEBUG:
                    printx(CFHIT2, "启动后更新光标位置")
                update_candidate_window_pos(self)
        else:
            if self.ime_enabled:
                if DEBUG:
                    printx(CBHIT3, "在区块中停用输入法")
                native.ime_input_disable(self.wm_pointer)
                self.ime_enabled = False
                self.editor_type = None
                self.area = None
                self.region = None
                self.space = None
                self.op_insert = None
                self.op_delete = None
                self.op_move = None
                self.op_delete = None

    @ staticmethod
    def button_press_callback(wm_pointer: int) -> None:
        # 该回调函数只在启用了 “使用输入法输入文字” 且 非正在合成文字 且 非输入法按键 时调用，
        # 简单来说，就是在启用了功能后且处于普通状态下时才被调用。
        watcher: Watcher = None
        for k, v in watchers.items():
            if v.wm_pointer == wm_pointer:
                watcher = v
                break
        if not watcher:
            return
        if watcher.ime_enabled and not watcher.inputing:
            # 在大部分按键事件中均会重新获取光标位置，以便下次输入的时候，候选框能够在准确的位置显示，不会闪一下
            if DEBUG:
                printx(CFHIT2, "按键后更新光标位置")
            update_candidate_window_pos(watcher)

    @ staticmethod
    def kill_focus_callback(wm_pointer: int) -> None:
        watcher: Watcher = None
        for k, v in watchers.items():
            if v.wm_pointer == wm_pointer:
                watcher = v
                break
        if not watcher:
            return
        if watcher.ime_enabled:
            def _func():  # 延迟到下一个事件才执行，否则和“强制取消文字合成”冲突
                if DEBUG:
                    printx(CBHIT3, "在区块中停用输入法（窗口失去焦点）")
                native.ime_input_disable(watcher.wm_pointer)
                watcher.ime_enabled = False
                watcher.editor_type = None
                watcher.area = None
                watcher.region = None
                watcher.space = None
                watcher.op_insert = None
                watcher.op_delete = None
                watcher.op_move = None
                watcher.op_delete = None
            bpy.app.timers.register(_func, first_interval=0.001, persistent=True)

    @ staticmethod
    def window_destory_callback(wm_pointer: int) -> None:
        watcher: Watcher = None
        for k, v in watchers.items():
            if v.wm_pointer == wm_pointer:
                watcher = v
                break
        if not watcher:
            return
        watchers.pop(watcher.window)
        if DEBUG:
            printx(CCFY, "鼠标位置检查器销毁 (剩余：%d)：%X (wm)" % (
                len(watchers), wm_pointer))

    @ staticmethod
    def composition_callback(wm_pointer: int, event_: int, text_: str, pos: int) -> None:
        if DEBUG:
            printx("派送消息(wm: %x)：" % wm_pointer, event_, text_, pos)
        watcher: Watcher = None
        for k, v in watchers.items():
            if k.as_pointer() == wm_pointer:
                watcher = v
                break
        if not watcher:
            return

        event: CompositionEventType = CompositionEventMaps[event_]

        # 从 Windows 传来的是 UTF-16 字符串，需要编码为 UTF-8
        text = text_.encode('utf-8').decode('utf-8')

        watcher.events.append((event, text, pos))

        # 收到开始消息，并且当前没有处理文本输入，则注册定时器
        if event == 'START' and not watcher.input_handler:
            watcher.register_start_timer()

        # 收到其它消息，则注册一个定时器，以便在没有输入消息时也能触发 input_handler 的 modal 函数
        elif event != 'START' and watcher.input_handler:
            if not watcher.input_handelr_event_timer:
                printx(CCBR, "注册定时器")
                watcher.input_handelr_event_timer = bpy.context.window_manager.event_timer_add(0.001, window=watcher.window)
        pass

    def register_start_timer(self):
        if self.input_handler_start_timer:
            return

        def _func():
            ctx = bpy.context.copy()
            ctx['window'] = self.window
            ctx['area'] = self.area
            ctx['region'] = self.region
            ctx['space_data'] = self.space
            if self.editor_type == 'text':
                ctx['edit_text'] = self.space.text
            if use_temp_override:
                with bpy.context.temp_override(**ctx):
                    bpy.ops.wire.fix_ime_input_handler('INVOKE_DEFAULT')
            else:  # 3.0.0 ~ 3.1.0 不支持 temp_override() ，只能使用旧方法
                bpy.ops.wire.fix_ime_input_handler(ctx, 'INVOKE_DEFAULT')

            self.input_handler_start_timer = None  # 必须放在操作调用之后
            pass

        bpy.app.timers.register(_func, first_interval=0.001, persistent=True)
        self.input_handler_start_timer = _func
        pass

    def process_event(self) -> CompositionEventType:
        if len(self.events) == 0:
            return

        if DEBUG:
            printx(CCFY, "处理输入事件...(总数：%d)" % len(self.events))

        if self.op_insert is None:
            if self.editor_type == 'font':
                self.op_insert = bpy.ops.font.text_insert
                self.op_delete = bpy.ops.font.delete
                self.op_move = bpy.ops.font.move
                self.op_select = bpy.ops.font.move_select
            if self.editor_type == 'text':
                self.op_insert = bpy.ops.text.insert
                self.op_delete = bpy.ops.text.delete
                self.op_move = bpy.ops.text.move
                self.op_select = None,  # 虽然有该操作，但 selection 无法用于 delete，等于没用
            elif self.editor_type == 'console':
                self.op_insert = bpy.ops.console.insert
                self.op_delete = bpy.ops.console.delete
                self.op_move = bpy.ops.console.move
                self.op_select = None,  # 没有该操作

        ctx = bpy.context.copy()
        ctx['window'] = self.window
        ctx['area'] = self.area
        ctx['region'] = self.region
        ctx['space_data'] = self.space
        if self.editor_type == 'text':
            ctx['edit_text'] = self.space.text

        # 更新合成文本
        if use_temp_override:
            with bpy.context.temp_override(**ctx):
                last_event = self.process_event_core(ctx)
        # 3.0.0 ~ 3.1.0 不支持 temp_override() ，只能使用旧方法
        else:
            last_event = self.process_event_core(ctx)

        # 更新光标位置
        if DEBUG:
            printx(CFHIT2, "输入后更新光标位置")
        update_candidate_window_pos(self)

        return last_event

    def process_event_core(self, ctx: bpy.types.Context) -> CompositionEventType:
        event: CompositionEventType = None

        args: list[object] = ['EXEC_REGION_WIN'] if use_temp_override else [ctx, 'EXEC_REGION_WIN']

        while len(self.events) > 0:
            event, text, pos = self.events.pop(0)

            start = (event == 'START')
            update = (event == 'UPDATE')
            finish = (event == 'FINISH')
            cancel = (event == 'CANCEL')

            if DEBUG:
                if event == 'START':
                    printx(CFHIT1, "开始合成文本")
                elif event == 'UPDATE':
                    printx(CFHIT1, "更新合成文本")
                elif event == 'FINISH':
                    printx(CFHIT1, "确认合成文本")
                elif event == 'CANCEL':
                    printx(CFHIT1, "取消合成文本")

            if start:
                self.inputing = True

            # 删除旧的文本
            if update or finish or cancel:

                if self.move_times != 0:  # 移动光标到最后的位置
                    for _ in range(self.move_times):
                        self.op_move(*args, type='NEXT_CHARACTER')

                if self.editor_type == 'font':
                    # 该方法速度更快，但是不能用于文本编辑器和控制台
                    for _ in range(self.length):
                        self.op_select(*args, type='PREVIOUS_CHARACTER')
                    self.op_delete(*args, type='SELECTION')
                else:
                    for _ in range(self.length):
                        self.op_delete(*args, type='PREVIOUS_CHARACTER')

            # 插入新的文本
            if start or update:
                self.length = len(text) + 2  # 加上中括号两个字符
                self.move_times = self.length - pos - 1  # -1 = -2 + 1，-2 是减去之前多加的 2，+1 是右侧的中括号
                self.op_insert(*args, text='[' + text + ']')
                for _ in range(self.move_times):
                    self.op_move(*args, type='PREVIOUS_CHARACTER')
            elif finish:
                self.op_insert(*args, text=text)

            if DEBUG:
                if start or update or finish:
                    printx("当前文本 (长度：%d，光标：%d):" % (self.length - 2, pos), CCBY + text + CCZ0)

            if finish or cancel:
                self.inputing = False

                # 注意 ：每次处理事件只处理到文本输入结束，之后的消息属于下一轮的事件
                return event

        return event

class WIRE_OT_fix_ime_input_watcher(bpy.types.Operator):
    bl_idname = 'wire.fix_ime_input_watcher'
    bl_label = "鼠标位置检查器"
    bl_description = "由 wire_fix_ime 插件在内部使用"
    bl_options = set()

    # 注意 ：通过非模态方式获取 MOUSEMOVE 事件，用模态操作会导致自动保存失效（Blender 不会在模态操作存在时保存文件）。

    # 注意 ：必须监听 Blender 提供的 MOUSEMOVE 事件，因为该事件在非鼠标移动时也会触发，例如切换编辑模式等。

    @ classmethod
    def poll(clss, context: bpy.types.Context) -> bool:
        if not use_fix_ime_input_is_valid:
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        window = context.window
        if window in watchers:
            watcher = watchers[window]
        else:
            watcher = Watcher()
            watcher.start(context)
        watcher.mouse_move(context, event)
        return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

    @ classmethod
    def add_key_map_item(clss):
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        km.keymap_items.new(clss.bl_idname, type='MOUSEMOVE', value='ANY')

    @ classmethod
    def remove_key_map_item(clss):
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        for _kmi in reversed(km.keymap_items):
            if _kmi.idname == clss.bl_idname:
                km.keymap_items.remove(_kmi)

class WIRE_OT_fix_ime_input_handler(bpy.types.Operator):
    bl_idname = 'wire.fix_ime_input_handler'
    bl_label = "文本输入"
    bl_description = ""
    bl_options = {'UNDO'}

    # 注意 ：文本输入必须在具有 'UNDO' 特性的 Operator 的生命周期内完成，否则无法完整撤销输入的文本

    def __init__(self) -> None:
        super().__init__()
        self.watcher = None

    # def __del__(self):
    #     # 实例和类型的销毁都会调用该函数（例如停用插件卸载类型时）
    #     if hasattr(self, 'base'):
    #         return

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        window = context.window

        if window in watchers:
            self.watcher = watchers[window]
            self.watcher.input_handler = self

            if DEBUG:
                printx(CCBG, "文本输入处理器启动")

            if len(self.watcher.events) > 0:
                ret = self.process()
                if 'RUNNING_MODAL' not in ret:
                    return ret

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        if self.watcher.input_handelr_event_timer:
            # 有没有收到 TIMER 消息都取消定时器，因为定时器只是用来触发 modal 的保险手段而已
            printx(CCBR, "卸载定时器")
            context.window_manager.event_timer_remove(self.watcher.input_handelr_event_timer)
            self.watcher.input_handelr_event_timer = None

        if len(self.watcher.events) > 0:
            ret = self.process()
            return ret

        return {'RUNNING_MODAL'}

    def process(self) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        last_event = self.watcher.process_event()

        if last_event in ['FINISH', 'CANCEL']:
            self.watcher.input_handler = None
            if DEBUG:
                printx(CCBR, "文本输入处理器关闭")

            # 如果依然存在消息，则准备下一轮的文本输入
            if len(self.watcher.events) > 0:
                self.watcher.register_start_timer()

            return {'FINISHED'} if last_event == 'FINISH' else {'CANCELLED'}

        return {'RUNNING_MODAL'}


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


show_caret = True if DEBUG_BUILD else False

def update_candidate_window_pos(watcher: Watcher):
    ctx = SimpleNamespace()
    ctx.window = watcher.window
    ctx.area = watcher.area
    ctx.region = watcher.region
    ctx.space_data = watcher.space
    ctx.preferences = bpy.context.preferences
    if watcher.space.type == 'VIEW_3D':
        update_candidate_window_pos_font_edit(ctx)
    elif watcher.space.type == 'TEXT_EDITOR':
        update_candidate_window_pos_text_editor(ctx)
    elif watcher.space.type == 'CONSOLE':
        update_candidate_window_pos_console(ctx)

def update_candidate_window_pos_font_edit(context: bpy.types.Context):
    # 注意 ：修改代码时留意 update_candidate_window_pos 中的 _ctx 的属性

    window = context.window

    # 由 native 完成设置
    pref = get_prefs(context)
    print(pref.candidate_window_percent)
    native.candidate_window_position_update_font_edit(
        window.as_pointer(), pref.candidate_window_percent, show_caret)

def update_candidate_window_pos_text_editor(context: bpy.types.Context):
    # 注意 ：修改代码时留意 update_candidate_window_pos 中的 _ctx 的属性

    window = context.window
    region = context.region
    space: bpy.types.SpaceTextEditor = context.space_data
    preferences = context.preferences
    text = space.text

    # 20 是 Blender 界面元素的基准高度，
    # context.preferences.system.ui_scale 是 系统 和 程序 界面缩放系数之积，
    # (space.font_size / 12) 是当前编辑器的缩放系数
    line_height = int(20 * preferences.system.ui_scale * (space.font_size / 12))

    # 偏移（offset）的原点在区块左下角，相对行的底部
    offset_x, offset_y = space.region_location_from_cursor(
        text.current_line_index, text.current_character)

    # 区块（region）的原点在窗口左下角
    client_x = region.x + offset_x
    client_y = window.height - (region.y + offset_y)

    # if DEBUG:
    #     print("offset: ", offset_x, offset_y)
    #     print("region: ", region.x, region.y)
    #     print("client: ", client_x, client_y)

    native.candidate_window_position_update_text_editor(
        window.as_pointer(), client_x, client_y, line_height, show_caret)

def update_candidate_window_pos_console(context: bpy.types.Context):
    # 注意 ：修改代码时留意 update_candidate_window_pos 中的 _ctx 的属性

    window = context.window
    region = context.region
    space: bpy.types.SpaceConsole = context.space_data
    preferences = context.preferences

    # 20 是 Blender 界面元素的基准高度，
    # context.preferences.system.ui_scale 是 系统 和 程序 界面缩放系数之积，
    # (space.font_size / 12) 是当前编辑器的缩放系数
    line_height = int(20 * preferences.system.ui_scale * (space.font_size / 12))

    rect_l = region.x
    rect_t = window.height - region.y - int(line_height * 2)
    rect_r = region.x + region.width
    rect_b = window.height - region.y

    # if DEBUG:
    #     print("rect: ", rect_l, rect_t, rect_r, rect_b)

    native.candidate_window_position_update_console(
        window.as_pointer(),
        rect_l, rect_t, rect_r, rect_b, show_caret)


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


TEXT_HT_header_extend_appended = False
CONSOLE_HT_header_extend_appended = False

def header_extend_draw_func(self: bpy.types.Header, context: bpy.types.Context):
    layout = self.layout

    window = context.window
    prefs = get_prefs(context)

    active = (prefs.use_fix_ime_state and prefs.use_fix_ime_input)

    if context.space_data.type == 'TEXT_EDITOR':
        switcher = prefs.use_fix_ime_input_text_editor
        prop = 'use_fix_ime_input_text_editor'
    else:
        switcher = prefs.use_fix_ime_input_console
        prop = 'use_fix_ime_input_console'
        layout.separator_spacer()

    row = layout.row()
    row.active = active

    icon = 'PROP_OFF'
    if active and switcher:
        watcher: Watcher = None
        if window in watchers:
            watcher = watchers[window]
        if watcher and watcher.space == context.space_data:
            icon = 'PROP_ON'
        else:
            icon = 'PROP_CON'

    row.prop(prefs, prop, text="", icon=icon, emboss=False,
        invert_checkbox=True if switcher else False)


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

def register():
    bpy.utils.register_class(WIRE_FIX_Preferences)
    bpy.utils.register_class(WIRE_OT_fix_ime_input_watcher)
    bpy.utils.register_class(WIRE_OT_fix_ime_input_handler)

    WIRE_OT_fix_ime_input_watcher.add_key_map_item()

    if DEBUG_BUILD:
        test_register()

    if native.dll_load():

        prefs = get_prefs(bpy.context)

        use_debug_update(prefs, bpy.context)

        global use_temp_override
        if bpy.app.version >= (3, 2, 0):
            use_temp_override = True
        if DEBUG:
            printx("use_temp_override:", use_temp_override)

        native.init()

        native.use_hook(True)

        use_fix_ime_update(prefs, bpy.context)

        use_fix_ime_input_update(prefs, bpy.context)

        use_header_extend(prefs, bpy.context)
    pass

def unregister():

    bpy.utils.unregister_class(WIRE_FIX_Preferences)
    bpy.utils.unregister_class(WIRE_OT_fix_ime_input_watcher)
    bpy.utils.unregister_class(WIRE_OT_fix_ime_input_handler)

    WIRE_OT_fix_ime_input_watcher.remove_key_map_item()

    if DEBUG_BUILD:
        test_unregister()

    if native.dll_loaded:

        native.use_hook(False)

        use_fix_ime_update(SimpleNamespace(
            use_fix_ime_state=False,
            use_fix_ime_input=False,
        ), bpy.context)

        use_header_extend(SimpleNamespace(
            use_header_extend_text_editor=False,
            use_header_extend_console=False,
        ), bpy.context)

        native.dll_unload()
    pass
