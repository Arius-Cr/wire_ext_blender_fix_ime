from typing import cast, Literal, Union
from types import SimpleNamespace
import sys
import os
import time

import bpy
import bpy.types

from .mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD
DEBUG = mark.DEBUG

# 状态更新器-轮换定时器 相关的调试信息
DEBUG_UPDATER_1 = mark.DEBUG_UPDATER_1
# 状态更新器-步进定时器 相关的调试信息
DEBUG_UPDATER_2 = mark.DEBUG_UPDATER_2

from .printx import *

from .native import native

if DEBUG_BUILD:
    from .test import register as test_register, unregister as test_unregister

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

'''
关键角色：

    管理器列表 - watchers
    输入管理器 - Manager
    消息处理器 - WIRE_FIX_IME_OT_timer_resolve
    状态更新器 - WIRE_FIX_IME_OT_state_updater
    输入处理器 - WIRE_FIX_IME_OT_input_handler

工作流程：

1. fix_ime_input_enable 和 fix_ime_input_disable 决定了整个功能的启用和停用。
    启用时注册以下快捷键:
        TIMER -> WIRE_FIX_IME_OT_timer_resolve
        MOUSEMOVE -> WIRE_FIX_IME_OT_state_updater

2. 用户将鼠标移入窗口（包括新窗口）时，WIRE_FIX_IME_OT_state_updater 启动。
    启动的时候如果管理器列表中没有和当前窗口对应的管理器，则新建管理器。
    之后，状态更新器以每 0.050s 的频率更新输入法的状态（和 use_fix_ime_state 功能的输入法状态无关）。
    当没有新事件时，状态更新器不会进行更新，但会确保最后一个事件必然进行过状态更新，
    以避免输入法状态和当前状态不匹配。
    然后状态更新器运行 5s 后关闭，等待 0.050s，然后重新启动（设置 updater_start_timer）。
    重新启动由 WIRE_FIX_IME_OT_timer_resolve 完成。
    这样做是为了让 Blender 的自动保存功能能够顺利执行。
    Blender 的自动保存功能在任何窗口存在任何模态操作时都不会执行，然后以 0.010s 的频率不断重试。
    状态更新器以模态方式运行，关闭时就不存在模态操作了，然后 0.050s 的间隔足够让自动保存通过。

    在任何时候都需要重新检查状态，不能仅限于 MOUSEMOVE，
    譬如执行撤销后，可能会从编辑模式退回到物体模式，此时不会触发 MOUSEMOVE，
    但需要重新检查状态，否则输入法依然处于启用状态。

3. 当用户通过输入法进行输入时，输入消息会压入消息堆栈，
    然后会设置处理器启动定时器（handler_start_timer），
    启动由 WIRE_FIX_IME_OT_timer_resolve 完成。
    启动后，输入处理器每次会处理消息堆栈中的一组输入消息（从 START 到 FINISH 或 CANCEL）。
    然后下一组消息由另一个输入处理器处理，否则用户无法分开撤销输入的文本。
    消息开始处理后，如果有新的消息，设置处理器更新定时器（handler_start_timer），
    该定时器由输入处理器自身捕获，然后进行新消息的处理，直到完成一组消息的处理。
    消息堆栈看起来可能是这样：
        OLD:    合成开始
         ↓      合成确认 （在中文模式中输入单个标点符号时就是这种开始紧接着就是结束的模式）
         ↓      合成开始
         ↓      合成更新
        NEW:    ...
'''

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


def use_debug_update(self: Union['WIRE_FIX_IME_Preferences', SimpleNamespace], context: bpy.types.Context) -> None:
    use_debug = self.use_debug

    mark.DEBUG = use_debug
    global DEBUG
    DEBUG = use_debug

    native.use_debug(DEBUG)
    native.use_hook_debug(DEBUG)
    native.use_fix_ime_debug(DEBUG)

def use_fix_ime_update(self: Union['WIRE_FIX_IME_Preferences', SimpleNamespace], context: bpy.types.Context) -> None:
    native.use_fix_ime_state(self.use_fix_ime_state)

    global use_fix_ime_input_is_valid

    use_fix_ime_input_is_valid = (
        self.use_fix_ime_state and
        self.use_fix_ime_input and (
        self.use_fix_ime_input_font_edit or
        self.use_fix_ime_input_text_editor or
        self.use_fix_ime_input_console))

    if DEBUG:
        printx(CCFY, "use_fix_ime_input_is_valid:", use_fix_ime_input_is_valid)

    if use_fix_ime_input_is_valid:
        fix_ime_input_enable()
    else:
        fix_ime_input_disable()
    pass

def use_header_extend(self: Union['WIRE_FIX_IME_Preferences', SimpleNamespace], context: bpy.types.Context) -> None:
    global TEXT_HT_header_extend_appended
    global CONSOLE_HT_header_extend_appended

    use_header_extend_text_editor = self.use_header_extend_text_editor
    use_header_extend_console = self.use_header_extend_console

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

def get_prefs(context: bpy.types.Context) -> 'WIRE_FIX_IME_Preferences':
    return context.preferences.addons[__package__].preferences

class WIRE_FIX_IME_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__  # 必须和插件模块名称相同

    use_fix_ime_state: bpy.props.BoolProperty(
        name="自动管理输入法状态",
        description="当用户激活输入框时，自动启用输入法，退出输入框时，自动停用输入法",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input: bpy.props.BoolProperty(
        name="使用输入法输入文字",
        description="在下面的情景中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_font_edit: bpy.props.BoolProperty(
        name="文本物体编辑模式",
        description="在【3D视图】的【文本物体】的【编辑模式】中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_text_editor: bpy.props.BoolProperty(
        name="文本编辑器",
        description="在【文本编辑器】中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_console: bpy.props.BoolProperty(
        name="控制台",
        description="在【控制台】中直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    candidate_window_percent: bpy.props.FloatProperty(
        name="候选窗口水平位置",
        description="设置候选窗口相对屏幕左侧的位置，最终位置会受系统调整",
        default=0.4,
        min=0,
        max=1,
        subtype='FACTOR',
    )

    use_header_extend_text_editor: bpy.props.BoolProperty(
        name="文本编辑器状态提示",
        description="在【文本编辑器】的标题栏中显示输入状态",
        default=True if DEBUG_BUILD else False,
        update=use_header_extend,
    )

    use_header_extend_console: bpy.props.BoolProperty(
        name="控制台状态提示",
        description="在【控制台】的标题栏中显示输入状态",
        default=True if DEBUG_BUILD else False,
        update=use_header_extend,
    )

    use_debug: bpy.props.BoolProperty(
        name="启用调试",
        description="启用调试模式。调试信息将会输出到控制台",
        default=True if DEBUG_BUILD else False,
        update=use_debug_update,
    )

    def draw(self, context: bpy.types.Context) -> None:
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


fix_ime_input_enabled: bool = False

def fix_ime_input_enable() -> None:
    global fix_ime_input_enabled
    if fix_ime_input_enabled:
        return

    WIRE_FIX_IME_OT_state_updater.add_key_map_item()
    WIRE_FIX_IME_OT_timer_resolve.add_key_map_item()

    native.use_fix_ime_input(True,
        Manager.composition_callback,
        Manager.kill_focus_callback,
        Manager.window_destory_callback)

    fix_ime_input_enabled = True
    pass

def fix_ime_input_disable() -> None:
    global fix_ime_input_enabled
    if not fix_ime_input_enabled:
        return

    WIRE_FIX_IME_OT_state_updater.remove_key_map_item()
    WIRE_FIX_IME_OT_timer_resolve.remove_key_map_item()

    native.use_fix_ime_input(False)

    for manager in list(managers.values()):
        manager.close()

    managers.clear()

    fix_ime_input_enabled = False
    pass


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


EditorType = Literal['FONT', 'TEXT', 'CONSOLE']
CompositionEventMaps = {0: 'START', 1: 'UPDATE', 2: 'FINISH', 3: 'CANCEL'}
CompositionEventType = Literal['START', "UPDATE", 'FINISH', 'CANCEL']

use_temp_override: bool = False

use_fix_ime_input_is_valid: bool = False  # 参考：use_fix_ime_input_update

managers: dict[bpy.types.Window, 'Manager'] = {}

class Manager():
    def __init__(self) -> None:
        self.window: bpy.types.Window = None
        self.wm_pointer: int = None

        self.updater: WIRE_FIX_IME_OT_state_updater = None
        self.updater_start_timer: bpy.types.Timer = None
        self.updater_take_turns: bool = False

        self.handler: WIRE_FIX_IME_OT_input_handler = None
        self.handler_start_timer: bpy.types.Timer = None
        self.handler_update_timer: bpy.types.Timer = None

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

        self.inputting: bool = False
        self.input_events: list[tuple[CompositionEventType, str, int]] = []
        # 上次合成文本的长度
        self.length: int = 0
        # 上次合成文本中光标相对末尾的字符数
        self.move_times: int = 0

    def start(self, context: bpy.types.Context) -> None:
        window = context.window
        managers[window] = self

        self.window = window
        self.wm_pointer = window.as_pointer()

        # 将窗口指针和窗口句柄绑定
        native.window_associate_pointer(self.wm_pointer)

        if DEBUG:
            printx(CCFG, "管理器启动 (现有: %d)：%X (wm)" % (
                len(managers), self.wm_pointer))
        pass

    def close(self, window_destory: bool = False) -> None:
        if self.window in managers:
            managers.pop(self.window)

            if self.updater_start_timer:
                bpy.context.window_manager.event_timer_remove(self.updater_start_timer)
                self.updater_start_timer = None

            if self.handler_start_timer:
                bpy.context.window_manager.event_timer_remove(self.handler_start_timer)
                self.handler_start_timer = None

            if self.handler_update_timer:
                bpy.context.window_manager.event_timer_remove(self.handler_update_timer)
                self.handler_update_timer = None

            if (updater := self.updater):
                updater.close('MANAGER_CLOSE')

            if (handler := self.handler):
                handler.close('MANAGER_CLOSE')

        if DEBUG:
            if not window_destory:
                printx(CCFY, "管理器关闭（剩余：%d）：%X (wm)" % (
                    len(managers), self.wm_pointer))
            else:
                printx(CCFY, "管理器销毁（剩余：%d）：%X (wm)" % (
                    len(managers), self.wm_pointer))
        pass

    def update_ime_state(self, context: bpy.types.Context, event: bpy.types.Event, key_pressed: bool = False, take_turns: bool = False) -> None:
        # key_pressed - 是否曾经有按键按下过

        # 如果用户激活了输入控件，则不会有事件发送到模态操作，因此不用担心和【输入控件】冲突。

        # 因为任务栏中的输入法状态仅反映活动窗口的，所以仅在窗口处于活动状态时维护输入法状态
        if self.inputting or not native.window_is_active(self.wm_pointer):
            return

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
                            editor_type = 'FONT'
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
                            editor_type = 'TEXT'
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
                        editor_type = 'CONSOLE'
                        area = _area
                        region = _region
                        space = _area.spaces[0]
                        break

        if editor_type:
            # 检测到符合条件的区块，如果当前没有启用输入法或当前鼠标所在空间和之前不同，则启用输入法
            if not self.ime_enabled or space != self.space:
                if DEBUG:
                    printx(CCBP, "在区块中启用输入法：%s" % space.type)
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
                    printx(CCFP, "启动后更新光标位置")
                update_candidate_window_pos(self)

            elif key_pressed:
                # 在大部分按键事件中均会重新获取光标位置，以便下次输入的时候，候选框能够在准确的位置显示，不会闪一下
                if DEBUG:
                    printx(CCFP, "按键后更新光标位置")
                update_candidate_window_pos(self)

            elif take_turns:
                if DEBUG and DEBUG_UPDATER_1:
                    printx(CCFP, "轮换后更新光标位置")
                update_candidate_window_pos(self)
        else:
            if self.ime_enabled:
                if DEBUG:
                    printx(CCBB, "在区块中停用输入法")
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
        pass

    @staticmethod
    def kill_focus_callback(wm_pointer: int) -> None:
        manager: Manager = None
        for _v in managers.values():
            if _v.wm_pointer == wm_pointer:
                manager = _v
                break
        if not manager:
            return
        if manager.ime_enabled:
            # kill_focus_callback 比 强制取消文字合成 先执行，
            # 如果不延迟，则强制取消文字合成时，一些标记的状态会不正确。
            def _func():
                if DEBUG:
                    printx(CCBB, "在区块中停用输入法（窗口失去焦点）")
                native.ime_input_disable(manager.wm_pointer)
                manager.ime_enabled = False
                manager.editor_type = None
                manager.area = None
                manager.region = None
                manager.space = None
                manager.op_insert = None
                manager.op_delete = None
                manager.op_move = None
                manager.op_delete = None
            bpy.app.timers.register(_func, first_interval=0.001, persistent=True)

    @staticmethod
    def window_destory_callback(wm_pointer: int) -> None:
        manager: Manager = None
        for _v in managers.values():
            if _v.wm_pointer == wm_pointer:
                manager = _v
                break
        if not manager:
            return
        manager.close(window_destory=True)
        pass

    @staticmethod
    def composition_callback(wm_pointer: int, event_: int, text_: str, pos: int) -> None:
        if DEBUG:
            printx("派送消息(wm: %X)：" % wm_pointer, event_, text_, pos)
        manager: Manager = None
        for k, v in managers.items():
            if k.as_pointer() == wm_pointer:
                manager = v
                break
        if not manager:
            return

        event: CompositionEventType = CompositionEventMaps[event_]

        # 从 Windows 传来的是 UTF-16 字符串，需要编码为 UTF-8
        text = text_.encode('utf-8').decode('utf-8')

        manager.input_events.append((event, text, pos))

        # 收到开始消息，并且当前没有处理文本输入，则注册定时器
        if event == 'START' and not manager.handler:
            # manager.register_start_timer()
            manager.register_handler_start_timer()

        # 收到其它消息，则注册一个定时器，以便在没有输入消息时也能触发 handler 的 modal 函数
        elif event != 'START' and manager.handler:
            manager.register_handler_update_timer()
        pass

    def register_handler_start_timer(self) -> None:
        if self.handler_start_timer:
            return
        if DEBUG:
            printx(f"设置 {CCFA}handler_start_timer{CCZ0}")
        self.handler_start_timer = bpy.context.window_manager.event_timer_add(0.001, window=self.window)

    def register_handler_update_timer(self) -> None:
        if self.handler_update_timer:
            return
        if DEBUG:
            printx(f"设置 {CCFA}handler_update_timer{CCZ0}")
        self.handler_update_timer = bpy.context.window_manager.event_timer_add(0.001, window=self.window)
        pass

    def process_event(self) -> CompositionEventType:
        if len(self.input_events) == 0:
            return

        if DEBUG:
            printx(CCFY, "处理输入事件...(总数：%d)" % len(self.input_events))

        if self.op_insert is None:
            if self.editor_type == 'FONT':
                self.op_insert = bpy.ops.font.text_insert
                self.op_delete = bpy.ops.font.delete
                self.op_move = bpy.ops.font.move
                self.op_select = bpy.ops.font.move_select
            if self.editor_type == 'TEXT':
                self.op_insert = bpy.ops.text.insert
                self.op_delete = bpy.ops.text.delete
                self.op_move = bpy.ops.text.move
                self.op_select = None,  # 虽然有该操作，但 selection 无法用于 delete，等于没用
            elif self.editor_type == 'CONSOLE':
                self.op_insert = bpy.ops.console.insert
                self.op_delete = bpy.ops.console.delete
                self.op_move = bpy.ops.console.move
                self.op_select = None,  # 没有该操作

        # 更新合成文本
        ctx = self.build_context()
        if use_temp_override:
            with bpy.context.temp_override(**ctx):
                last_event = self.process_event_core(ctx)
        else:  # 3.0.0 ~ 3.1.0 不支持 temp_override() ，只能使用旧方法
            last_event = self.process_event_core(ctx)

        # 更新光标位置
        if DEBUG:
            printx(CCFP, "输入后更新光标位置")
        update_candidate_window_pos(self)

        return last_event

    def process_event_core(self, ctx: bpy.types.Context) -> CompositionEventType:
        event: CompositionEventType = None

        args: list[object] = ['EXEC_REGION_WIN', False] if use_temp_override else [ctx, 'EXEC_REGION_WIN', False]

        while len(self.input_events) > 0:
            event, text, pos = self.input_events.pop(0)

            start = (event == 'START')
            update = (event == 'UPDATE')
            finish = (event == 'FINISH')
            cancel = (event == 'CANCEL')

            if DEBUG:
                if event == 'START':
                    printx(CCFA, "开始合成文本")
                elif event == 'UPDATE':
                    printx(CCFA, "更新合成文本")
                elif event == 'FINISH':
                    printx(CCFA, "确认合成文本")
                elif event == 'CANCEL':
                    printx(CCFA, "取消合成文本")

            if start:
                self.inputting = True

            # 删除旧的文本
            if update or finish or cancel:

                if self.move_times != 0:  # 移动光标到最后的位置
                    for _ in range(self.move_times):
                        self.op_move(*args, type='NEXT_CHARACTER')

                if self.editor_type == 'FONT':
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
                if use_temp_override:
                    self.op_insert('INVOKE_DEFAULT', True, text=text)
                else:
                    self.op_insert(ctx, 'INVOKE_DEFAULT', True, text=text)

            if DEBUG:
                if start or update or finish:
                    printx("当前文本 (长度：%d，光标：%d):" % (self.length - 2, pos), CCBY + text + CCZ0)

            if finish or cancel:
                self.inputting = False

                # 注意 ：每次处理事件只处理到文本输入结束，之后的消息属于下一轮的事件
                return event

        return event

    def build_context(self) -> dict:
        ctx = bpy.context.copy()
        ctx['window'] = self.window
        ctx['area'] = self.area
        ctx['region'] = self.region
        ctx['space_data'] = self.space
        if self.editor_type == 'TEXT':
            ctx['edit_text'] = self.space.text
        return ctx

class WIRE_FIX_IME_OT_timer_resolve(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.timer_resolve'
    bl_label = "消息处理器"
    bl_description = "由 wire_fix_ime 插件在内部使用"
    bl_options = set()

    @classmethod
    def poll(clss, context: bpy.types.Context) -> bool:
        if not use_fix_ime_input_is_valid:
            return False
        if (window := context.window) not in managers:
            return False
        # 当鼠标被捕获，则不要结束任何操作，因为操作结束时会导致鼠标位置重置。
        # 还没运行的操作不要运行，已经运行的操作不要结束。
        if native.window_is_mouse_capture(window.as_pointer()):
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        manager = managers[context.window]

        if manager.updater_start_timer:
            if DEBUG and DEBUG_UPDATER_1:
                printx(f"捕获 {CCFA}updater_start_timer{CCZ0}：{event.type}")
            context.window_manager.event_timer_remove(manager.updater_start_timer)
            manager.updater_start_timer = None
            bpy.ops.wire_fix_ime.state_updater('INVOKE_DEFAULT', False)

        if manager.handler_start_timer:
            if DEBUG:
                printx(f"捕获 {CCFA}handler_start_timer{CCZ0}：{event.type}")
            context.window_manager.event_timer_remove(manager.handler_start_timer)
            manager.handler_start_timer = None
            # 注意 ：必须加 UNDO = True，否则标点的输入会无法撤销
            bpy.ops.wire_fix_ime.input_handler('INVOKE_DEFAULT', True)

        return {'FINISHED', 'PASS_THROUGH', 'INTERFACE'}

    @classmethod
    def add_key_map_item(clss) -> None:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        km.keymap_items.new(clss.bl_idname, type='TIMER', value='ANY',
                            ctrl=-1, shift=-1, alt=-1, oskey=-1)  # 注意 ：修饰键

    @classmethod
    def remove_key_map_item(clss) -> None:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        for kmi in reversed(km.keymap_items):
            if kmi.idname == clss.bl_idname:
                km.keymap_items.remove(kmi)

class WIRE_FIX_IME_OT_state_updater(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.state_updater'
    bl_label = "状态更新器"
    bl_description = "由 wire_fix_ime 插件在内部使用"
    bl_options = {'GRAB_CURSOR'}

    @ classmethod
    def poll(clss, context: bpy.types.Context) -> bool:
        if not use_fix_ime_input_is_valid:
            return False

        window = context.window
        if window in managers:
            manager = managers[window]
            if manager.updater or manager.updater_start_timer:
                return False

        return True

    def __init__(self) -> None:
        super().__init__()
        self.manager: Manager = None
        self.valid: bool = True

        self.start_time: int = 0
        self.updater_end_timer: bpy.types.Timer = None

        self.prev_step_time: int = 0
        self.updater_step_timer: bpy.types.Timer = None

        self.key_pressed: bool = False

        self.waitting_for_end_message_printed: bool = False  # 仅用于调试信息的输出

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        self.start_time = time.time_ns()

        wm = context.window_manager
        window = context.window

        if window in managers:
            manager = managers[window]
        else:
            manager = Manager()
            manager.start(context)
        self.manager = manager

        if manager.updater is not None:
            printx(CCBG, "状态更新器重复：%X (wm)" % manager.wm_pointer)

        manager.updater = self

        take_turns = manager.updater_take_turns
        if not manager.updater_take_turns:
            if DEBUG:
                printx(CCBG, "状态更新器启动：%X (wm)" % manager.wm_pointer)
        else:
            if DEBUG and DEBUG_UPDATER_1:
                printx(CCFA, "状态更新器轮换：%X (wm)" % manager.wm_pointer)
        manager.updater_take_turns = False

        self.prev_step_time = self.start_time
        manager.update_ime_state(context, event, take_turns=take_turns)

        self.updater_end_timer = wm.event_timer_add(5, window=window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        wm = context.window_manager
        manager = self.manager

        # 通过选项关闭状态更新器时，无法主动关闭模态操作，因此通过设置标记让其自行在某个时机结束。
        if not self.valid:
            self.close('INVALID')
            return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

        # 注意 ：字体选择窗口中，有时 context 的任何方法都为 None，原因未知，但无害
        # 这里输出信息仅仅是留待观察，没有特殊用意。
        if getattr(context, 'copy', None) is None:
            if DEBUG:
                printx(CCBR, "context methods is None（无危害）", event.type, context.copy)
            # return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

        if not self.key_pressed:
            self.key_pressed = self.has_key_pressed(context, event)

        if self.updater_step_timer:
            if DEBUG and DEBUG_UPDATER_2:
                printx(f"捕获 {CCFB}updater_step_timer{CCZ0}：{event.type}")
            wm.event_timer_remove(self.updater_step_timer)
            self.updater_step_timer = None

        span_step = (_now := time.time_ns()) - self.prev_step_time
        if span_step >= 50 * 1000000:  # 0.050s
            if DEBUG and DEBUG_UPDATER_2:
                # 注意 ：在 modal 中设置的定时器，定时消息似乎会变为 NONE 而不是 TIMER，但对当前情况没有影响。
                printx(f"{CCFA}状态更新{CCZ0}：%s" % event.type)
            self.prev_step_time = _now
            manager.update_ime_state(context, event, key_pressed=self.key_pressed)
            self.key_pressed = False
        else:
            if DEBUG and DEBUG_UPDATER_2:
                printx(f"设置 updater_step_timer：{event.type}")
            self.updater_step_timer = wm.event_timer_add(0.050, window=manager.window)
            pass

        if time.time_ns() - self.start_time >= 5000 * 1000000:  # 5.000s

            if self.updater_end_timer:
                wm.event_timer_remove(self.updater_end_timer)
                # 确保之后必然可以结束。将 step_timer 和 end_timer 的逻辑分离是故意设计的，改动一方不会影响另一方。
                self.updater_end_timer = wm.event_timer_add(0.050, window=manager.window)

            # 注意 ：如果鼠标已经被捕获，则不要结束操作，继续等待，否则会导致鼠标位置被重置
            if not native.window_is_mouse_capture(context.window.as_pointer()):

                self.close('TAKE_TURNS')

                manager.updater_take_turns = True

                # 注意 ：间隔必须大于 0.010s
                self.manager.updater_start_timer = wm.event_timer_add(0.050, window=manager.window)

                return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

            else:
                if not self.waitting_for_end_message_printed:
                    self.waitting_for_end_message_printed = True
                    printx(CCBY, f"等待鼠标释放")

        return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

    def cancel(self, context: bpy.types.Context) -> None:
        self.close('CANCEL')

    def close(self, reason: Literal['TAKE_TURNS', 'CANCEL', 'MANAGER_CLOSE', 'INVALID']) -> None:
        wm = bpy.context.window_manager
        manager = self.manager

        self.valid = False  # 实际上仅用于 MANAGER_CLOSE

        if manager.updater == self:
            manager.updater = None

        if self.updater_end_timer:
            wm.event_timer_remove(self.updater_end_timer)
            self.updater_end_timer = None

        if self.updater_step_timer:
            wm.event_timer_remove(self.updater_step_timer)
            self.updater_step_timer = None

        if DEBUG:
            # 无需在 TAKE_TURNS 时输出任何内容

            # 窗口关闭时（模态操作的 cancel 早于 window_destory_callback 被调用）
            if reason == 'CANCEL':
                printx(CCBP, "状态更新器关闭：%X (wm)" % manager.wm_pointer)
            # 选项关闭或插件停用时（插件停用时模态操作的 modal 不会被调用，但不会有任何影响）
            elif reason == 'MANAGER_CLOSE':
                printx(CCBP, "状态更新器失效（等待）：%X (wm)" % manager.wm_pointer)
            # modal 中检测到 self.valid == False 时
            elif reason == 'INVALID':
                printx(CCBP, "状态更新器失效（完成）：%X (wm)" % manager.wm_pointer)
        pass

    def has_key_pressed(self, context: bpy.types.Context, event: bpy.types.Event) -> bool:
        if event.value == 'RELEASE' and event.type not in [
            'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE',
            'TIMER', 'TIMER0', 'TIMER1', 'TIMER2',
            'TIMER_JOBS', 'TIMER_AUTOSAVE', 'TIMER_REPORT', 'TIMERREGION',
            'NONE',
            'LEFT_CTRL', 'LEFT_SHIFT', 'LEFT_ALT',
            'RIGHT_CTRL', 'RIGHT_SHIFT', 'RIGHT_ALT',
            'OSKEY',
            'NDOF_MOTION',
        ]:
            return True
        return False

    @classmethod
    def add_key_map_item(clss) -> None:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        km.keymap_items.new(clss.bl_idname, type='MOUSEMOVE', value='ANY')

    @classmethod
    def remove_key_map_item(clss) -> None:
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        for _kmi in reversed(km.keymap_items):
            if _kmi.idname == clss.bl_idname:
                km.keymap_items.remove(_kmi)

class WIRE_FIX_IME_OT_input_handler(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.input_handler'
    bl_label = "输入处理器"
    bl_description = "由 wire_fix_ime 插件在内部使用"
    bl_options = set()

    # 注意 ：bl_options 必须不能有 'UNOD'，否则无法在【物体处于编辑模式】时，撤销在【文本编辑器】中输入的文本

    def __init__(self) -> None:
        super().__init__()
        self.manager = None
        self.valid: bool = True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        window = context.window

        if window in managers:
            self.manager = managers[window]
            self.manager.handler = self

            if DEBUG:
                printx(CCBG, "输入处理器启动")

            if len(self.manager.input_events) > 0:
                ret = self.process(context)
                if 'RUNNING_MODAL' not in ret:
                    return ret

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        wm = context.window_manager
        manager = self.manager

        # 通过选项关闭状态更新器时，无法主动关闭模态操作，因此通过设置标记让其自行在某个时机结束。
        if not self.valid:
            self.close('INVALID')
            return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

        if manager.handler_update_timer:
            if DEBUG:
                printx(f"捕获 {CCFA}handler_update_timer{CCZ0}：{event.type}")
            wm.event_timer_remove(manager.handler_update_timer)
            manager.handler_update_timer = None

        if len(manager.input_events) > 0:
            ret = self.process(context)
            return ret

        # TODO ：TIMER 类消息要放行吗？按官方手册的指引，应该不用放行...

        return {'RUNNING_MODAL'}  # 进行文字输入时，屏蔽其它按键

    def process(self, context: bpy.types.Context) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        last_event = self.manager.process_event()

        if last_event in ['FINISH', 'CANCEL']:
            self.manager.handler = None

            if DEBUG:
                printx(CCBR, "输入处理器关闭")

            if len(self.manager.input_events) > 0:
                if DEBUG:
                    printx(CCBR, "等待下一轮进行处理，剩余消息：", len(self.manager.input_events))
                self.manager.register_handler_start_timer()

            return {'FINISHED'} if last_event == 'FINISH' else {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def cancel(self, context: bpy.types.Context) -> None:
        self.close('CANCEL')

    def close(self, reason: Literal['CANCEL', 'MANAGER_CLOSE', 'INVALID']) -> None:
        manager = self.manager

        self.valid = False  # 实际上仅用于 MANAGER_CLOSE

        if manager.handler == self:
            manager.handler = None

        if DEBUG:
            # 窗口关闭时（模态操作的 cancel 早于 window_destory_callback 被调用）
            if reason == 'CANCEL':
                printx(CCBP, "输入处理器关闭：%X (wm)" % manager.wm_pointer)
            # 选项关闭或插件停用时（插件停用时模态操作的 modal 不会被调用，但不会有任何影响）
            elif reason == 'MANAGER_CLOSE':
                printx(CCBP, "输入处理失效（等待）：%X (wm)" % manager.wm_pointer)
            # modal 中检测到 self.valid == False 时
            elif reason == 'INVALID':
                printx(CCBP, "输入处理失效（完成）：%X (wm)" % manager.wm_pointer)
        pass


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


show_caret = True if DEBUG_BUILD else False

def update_candidate_window_pos(manager: Manager) -> None:
    ctx = SimpleNamespace()
    ctx.window = manager.window
    ctx.area = manager.area
    ctx.region = manager.region
    ctx.space_data = manager.space
    ctx.preferences = bpy.context.preferences
    if manager.space.type == 'VIEW_3D':
        update_candidate_window_pos_font_edit(ctx)
    elif manager.space.type == 'TEXT_EDITOR':
        update_candidate_window_pos_text_editor(ctx)
    elif manager.space.type == 'CONSOLE':
        update_candidate_window_pos_console(ctx)

def update_candidate_window_pos_font_edit(context: bpy.types.Context) -> None:
    # 注意 ：修改代码时留意 update_candidate_window_pos 中的 ctx 的属性

    window = context.window

    # 由 native 完成设置
    pref = get_prefs(context)
    native.candidate_window_position_update_font_edit(
        window.as_pointer(), pref.candidate_window_percent, show_caret)

def update_candidate_window_pos_text_editor(context: bpy.types.Context) -> None:
    # 注意 ：修改代码时留意 update_candidate_window_pos 中的 ctx 的属性

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
    # 注意 ：region_location_from_cursor 返回坐标不是准确的，存在问题
    offset_x, offset_y = space.region_location_from_cursor(
        text.current_line_index, text.current_character)

    # 区块（region）的原点在窗口左下角
    client_x = region.x + offset_x
    client_y = window.height - (region.y + offset_y)

    # if DEBUG:
    #     printx("offset: ", offset_x, offset_y)
    #     printx("region: ", region.x, region.y)
    #     printx("client: ", client_x, client_y)

    native.candidate_window_position_update_text_editor(
        window.as_pointer(), client_x, client_y, line_height, show_caret)

def update_candidate_window_pos_console(context: bpy.types.Context) -> None:
    # 注意 ：修改代码时留意 update_candidate_window_pos 中的 ctx 的属性

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
    #     printx("rect: ", rect_l, rect_t, rect_r, rect_b)

    native.candidate_window_position_update_console(
        window.as_pointer(),
        rect_l, rect_t, rect_r, rect_b, show_caret)


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


TEXT_HT_header_extend_appended = False
CONSOLE_HT_header_extend_appended = False

def header_extend_draw_func(self: bpy.types.Header, context: bpy.types.Context) -> None:
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
        manager: Manager = None
        if window in managers:
            manager = managers[window]
        if manager and manager.space == context.space_data:
            icon = 'PROP_ON'
        else:
            icon = 'PROP_CON'

    row.prop(prefs, prop, text="", icon=icon, emboss=False,
        invert_checkbox=True if switcher else False)


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

def register() -> None:
    if DEBUG_BUILD:
        printx(CCFY, f"\n===== {__package__} start =====")

    if mark.mark_debug:
        printx(CCBY, "加载调试信息：")
        for _name in mark.mark_debug_names:
            printx(f"  {CCFA}{_name}{CCZ0}：{getattr(mark, _name)}")

    bpy.utils.register_class(WIRE_FIX_IME_Preferences)
    bpy.utils.register_class(WIRE_FIX_IME_OT_timer_resolve)
    bpy.utils.register_class(WIRE_FIX_IME_OT_state_updater)
    bpy.utils.register_class(WIRE_FIX_IME_OT_input_handler)

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

        use_header_extend(prefs, bpy.context)

    pass

def unregister() -> None:
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

    if DEBUG_BUILD:
        test_unregister()

    bpy.utils.unregister_class(WIRE_FIX_IME_OT_input_handler)
    bpy.utils.unregister_class(WIRE_FIX_IME_OT_state_updater)
    bpy.utils.unregister_class(WIRE_FIX_IME_OT_timer_resolve)
    bpy.utils.unregister_class(WIRE_FIX_IME_Preferences)

    if DEBUG_BUILD:
        printx(CCFY, f"===== {__package__} end =====")
    pass
