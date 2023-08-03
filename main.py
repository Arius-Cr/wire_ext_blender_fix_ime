from typing import cast, Literal, Union
from types import SimpleNamespace
import sys
import os
import time
import traceback

import bpy
import bpy.types

from .mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD
DEBUG = mark.DEBUG
DEBUG_UPDATER_1 = mark.DEBUG_UPDATER_1
DEBUG_UPDATER_2 = mark.DEBUG_UPDATER_2
DEBUG_CANDIDATE_POS = mark.DEBUG_CANDIDATE_POS
DEBUG_HEADER_REDRAW = mark.DEBUG_HEADER_REDRAW

from .printx import *

from .native import native

if DEBUG_BUILD:
    from .test import register as test_register, unregister as test_unregister


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


# 工作机制请参考开发指南中的说明


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
        description="在下面的情况中，允许用户直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_font_edit: bpy.props.BoolProperty(
        name="文本物体编辑模式",
        description="在【3D视图】的【文本物体】的【编辑模式】中允许用户直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_text_editor: bpy.props.BoolProperty(
        name="文本编辑器",
        description="在【文本编辑器】中允许用户直接使用输入法输入文字",
        default=True,
        update=use_fix_ime_update,
    )

    use_fix_ime_input_console: bpy.props.BoolProperty(
        name="控制台",
        description="在【控制台】中允许用户直接使用输入法输入文字",
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
        description="调试信息将会输出到控制台",
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

        from . import bl_info
        if 'release_url' in bl_info:
            column.separator()
            split = column.split(factor=split_factor)
            rowl = split.row()
            rowl.alignment = 'RIGHT'
            rowl.label(text="版本更新")
            rowr = split.row()
            op = rowr.operator('wm.url_open', text="插件发布页", icon='URL')
            op.url = bl_info['release_url']


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


fix_ime_input_enabled: bool = False

def fix_ime_input_enable() -> None:
    global fix_ime_input_enabled
    if fix_ime_input_enabled:
        return

    WIRE_FIX_IME_OT_state_updater.add_key_map_item()

    native.use_fix_ime_input(True,
        Manager.composition_callback,
        Manager.button_down_callback,
        Manager.kill_focus_callback,
        Manager.window_destory_callback)

    fix_ime_input_enabled = True
    pass

def fix_ime_input_disable() -> None:
    global fix_ime_input_enabled
    if not fix_ime_input_enabled:
        return

    WIRE_FIX_IME_OT_state_updater.remove_key_map_item()

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

ns_to_ms: int = 1000000
ns_to_s: int = 1000000000
updater_step_f: float = 0.050  # s
updater_step_i: int = updater_step_f * ns_to_s  # 1s = 1 000 ms 000 μs 000 ns

managers: dict[bpy.types.Window, 'Manager'] = {}

class Manager():
    def __init__(self) -> None:
        self.window: bpy.types.Window = None
        self.wm_pointer: int = None

        self.updater_prev_step_time: int = 0
        self.updater_step_timer: bpy.types.Timer = None
        self.updater_key_pressed: bool = False
        self.updater_skip_message: int = 0

        self.handler: WIRE_FIX_IME_OT_input_handler = None
        self.handler_start_timer: bpy.types.Timer = None
        self.handler_update_timer: bpy.types.Timer = None

        # 当前输入法是否已经启动
        self.ime_enabled = False

        self.editor_type: EditorType = None
        self.prev_area = None
        self.area = None
        self.region = None
        self.space = None

        self.op_insert = None
        self.op_delete = None
        self.op_move = None
        self.op_select = None

        self.inputting: bool = False
        self.input_events: list[tuple[CompositionEventType, str, int]] = []
        # 上次输入消息中合成文本的长度（含作为标记的中括号）
        self.length: int = 0
        # 上次输入消息中合成文本中光标相对合成文本末尾的字符数（含作为标记的中括号）
        self.move_times: int = 0

    def start(self, context: bpy.types.Context) -> None:
        window = context.window
        managers[window] = self

        self.window = window
        self.wm_pointer = window.as_pointer()

        # 将窗口指针和窗口句柄绑定
        native.window_associate(self.wm_pointer)

        if DEBUG:
            printx(CCFG, "管理器启动 (现有: %d)：%X (wm)" % (
                len(managers), self.wm_pointer))
        pass

    def close(self, window_destory: bool = False) -> None:
        if self.window in managers:
            managers.pop(self.window)
            wm = bpy.context.window_manager

            if self.updater_step_timer:
                wm.event_timer_remove(self.updater_step_timer)
                self.updater_step_timer = None

            if self.handler_start_timer:
                wm.event_timer_remove(self.handler_start_timer)
                self.handler_start_timer = None

            if self.handler_update_timer:
                wm.event_timer_remove(self.handler_update_timer)
                self.handler_update_timer = None

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

    def update_ime_state(self, context: bpy.types.Context, event: bpy.types.Event) -> None:
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
                if native.ime_input_enable(self.wm_pointer):
                    self.ime_enabled = True
                    self.editor_type = editor_type
                    self.prev_area = self.area
                    self.area = area
                    self.region = region
                    self.space = space
                    self.op_insert = None  # 延迟到 event_process 中再初始化
                    self.op_delete = None
                    self.op_move = None
                    self.op_delete = None
                    self.update_icon_state()
                    if DEBUG:
                        printx(CCFP, "启动后更新光标位置")
                    update_candidate_window_pos(self)
                else:
                    if DEBUG:
                        printx(CCBR, "启用输入法失败")

            elif self.updater_key_pressed:
                self.updater_key_pressed = False
                # 在大部分按键事件中均会重新获取光标位置，以便下次输入的时候，候选框能够在准确的位置显示，不会闪一下
                if DEBUG:
                    printx(CCFP, "按键后更新光标位置")
                update_candidate_window_pos(self)
        else:
            if self.ime_enabled:
                if DEBUG:
                    printx(CCBB, "在区块中停用输入法")
                if not native.ime_input_disable(self.wm_pointer):  # 返回的是 ime_enabled 的值并不是执行是否成功
                    self.ime_enabled = False
                    self.editor_type = None
                    self.prev_area = self.area
                    self.area = None
                    self.region = None
                    self.space = None
                    self.op_insert = None
                    self.op_delete = None
                    self.op_move = None
                    self.op_delete = None
                    self.update_icon_state()
                else:
                    if DEBUG:
                        printx(CCBR, "停用输入法失败")
        pass

    def update_icon_state(self):
        prefs = get_prefs(bpy.context)
        use_text_editor = prefs.use_header_extend_text_editor
        use_console = prefs.use_header_extend_console
        if use_text_editor or use_console:
            prev_area = self.prev_area
            area = self.area
            try:
                if prev_area:
                    if use_text_editor and prev_area.type == 'TEXT_EDITOR':
                        for region in prev_area.regions:
                            if region.type == 'HEADER':
                                if DEBUG and DEBUG_HEADER_REDRAW:
                                    printx(CCFY, "prev_area TEXT_EDITOR tag_redraw()")
                                region.tag_redraw()
                                break
                    if use_console and prev_area.type == 'CONSOLE':
                        for region in prev_area.regions:
                            if region.type == 'HEADER':
                                if DEBUG and DEBUG_HEADER_REDRAW:
                                    printx(CCFY, "prev_area Console tag_redraw()")
                                region.tag_redraw()
                                break
            except:
                # 有可能 prev_area 已经销毁
                if DEBUG and DEBUG_HEADER_REDRAW:
                    traceback.print_exc()
                pass
            if area:
                if use_text_editor and area.type == 'TEXT_EDITOR':
                    for region in area.regions:
                        if region.type == 'HEADER':
                            if DEBUG and DEBUG_HEADER_REDRAW:
                                printx(CCFY, "area TEXT_EDITOR tag_redraw()")
                            region.tag_redraw()
                            break
                if use_console and area.type == 'CONSOLE':
                    for region in area.regions:
                        if region.type == 'HEADER':
                            if DEBUG and DEBUG_HEADER_REDRAW:
                                printx(CCFY, "area Console tag_redraw()")
                            region.tag_redraw()
                            break
        pass

    def register_updater_step_timer(self) -> Union[float, None]:
        if self.updater_step_timer:
            return
        if (native.window_is_active(self.wm_pointer) and
            not native.is_input_box_active(self.wm_pointer) and
            not native.window_is_mouse_capture(self.wm_pointer) and
            not self.handler and not self.handler_start_timer):
            wm = bpy.context.window_manager
            span = (self.updater_prev_step_time + updater_step_i - time.time_ns()) / ns_to_s + 0.001
            if span <= 0.001:
                span = 0.001
            self.updater_step_timer = wm.event_timer_add(span, window=self.window)
            return span
        return

    def unregister_updater_step_timer(self) -> None:
        if not self.updater_step_timer:
            return
        wm = bpy.context.window_manager
        wm.event_timer_remove(self.updater_step_timer)
        self.updater_step_timer = None

    @staticmethod
    def button_down_callback(wm_pointer: int) -> None:
        manager: Manager = None
        for _v in managers.values():
            if _v.wm_pointer == wm_pointer:
                manager = _v
                break
        if not manager:
            return
        manager.updater_key_pressed = True
        _span_s = manager.register_updater_step_timer()
        if DEBUG and DEBUG_UPDATER_2 and _span_s is not None:
            printx(f"{CCFG}设置{CCZ0} updater_step_timer：BUTTON_DOWN_CALLBACK, 间隔：{_span_s * 1000:.0f}ms")

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
                manager.prev_area = manager.area
                manager.area = None
                manager.region = None
                manager.space = None
                manager.op_insert = None
                manager.op_delete = None
                manager.op_move = None
                manager.op_delete = None
                manager.update_icon_state()
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
        _time = 0
        if DEBUG:
            _time = time.perf_counter_ns()
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

        manager.input_events.append((event, text, pos, _time))

        # 收到开始消息，并且当前没有处理文本输入，则注册定时器
        if event == 'START' and not manager.handler:
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
            event, text, pos, _time = self.input_events.pop(0)

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

                _span = time.perf_counter_ns() - _time
                printx(f"{CCFY}输入消息处理耗时: {round(_span/1000000, 3): >8.3f}ms{CCZ0}")

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

class WIRE_FIX_IME_OT_state_updater(bpy.types.Operator):
    bl_idname = 'wire_fix_ime.state_updater'
    bl_label = "状态更新器"
    bl_description = "由 wire_fix_ime 插件在内部使用"
    bl_options = set()

    @ classmethod
    def poll(clss, context: bpy.types.Context) -> bool:
        if not use_fix_ime_input_is_valid:
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        window = context.window
        event_type = event.type  # 当消息为 'TIMER' 时取消了相关的定时器，会导致消息立即变为 'NONE'

        if window not in managers:
            window = context.window
            manager = Manager()
            manager.start(context)
        manager = managers[window]

        # 注意 ：在输入框激活时，不应该进行状态更新操作。
        # 使用模态操作不监听 'TIMER' 时不存在这个问题，因为输入框会阻挡 'TIMER' 之外的事件的传递，
        # 但使用模态操作会导致自动保存失效，使用轮换式模态操作会导致鼠标捕捉和工具提示异常，
        # 因此无法使用模态操作，所以需要自行确保在输入框激活后，不更新状态。
        # 目前唯一会在输入框激活后触发状态更新的途径有两个：
        #   - button_donw_callback（对应鼠标和键盘按键）
        #   - TIMER 消息
        # 其中，button_donw_callback 在 DLL 一侧通过 himc_custom 来判断当前输入框的激活状态。
        # 在插件这侧也可以通过 native.is_input_box_active 来判断。

        # 注意 ：需要严格过滤 'TIMER' 消息，否则在以下情况会出现问题：
        # 激活属性视图标题栏的搜索框，将鼠标移动到文本物体处于编辑状态的3D视图中，
        # 输入文字后，面板筛选会以动画的形式进行，此时会触发多个 'TIMER' 消息，
        # 而这些 'TIMER' 消息会导致状态更新，
        # 由于鼠标在符合条件的3D视图中，所以会进入自定义的输入法消息处理流程，
        # 阻挡了搜索框中的输入。

        if event_type == 'TIMER':
            is_step_timer = (manager.updater_step_timer and manager.updater_step_timer.time_delta)
            is_start_timer = (manager.handler_start_timer and manager.handler_start_timer.time_delta)
            if not (is_step_timer or is_start_timer):
                if DEBUG and DEBUG_UPDATER_2:
                    printx("无关的 TIMER 消息")
                return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}
        else:  # 非 'TIMER' 消息，则必定为 False
            is_step_timer = False
            is_start_timer = False

        if is_step_timer:
            if DEBUG and DEBUG_UPDATER_2:
                printx(f"{CCFB}捕获{CCZ0} updater_step_timer：{event_type}")
            manager.unregister_updater_step_timer()

        if (native.window_is_active(manager.wm_pointer) and
            not native.is_input_box_active(manager.wm_pointer) and
            not native.window_is_mouse_capture(manager.wm_pointer) and
            not manager.handler and not manager.handler_start_timer):

            span_step = (_now := time.time_ns()) - manager.updater_prev_step_time
            if span_step >= updater_step_i:
                manager.updater_prev_step_time = _now

                if DEBUG and DEBUG_UPDATER_1:
                    _time = time.perf_counter_ns()

                manager.update_ime_state(context, event)

                if DEBUG:
                    if DEBUG_UPDATER_1:
                        _span = time.perf_counter_ns() - _time
                        printx(f"{CCFY}状态更新（间隔: {round(span_step / ns_to_ms, 3): >8.3f}ms，"
                            f"跳过: {manager.updater_skip_message: >2d}）{CCZ0}"
                            f"更新用时：{round(_span / ns_to_ms, 3):.3f}ms，{event_type}")
                    manager.updater_skip_message = 0

                if manager.updater_step_timer:
                    if DEBUG and DEBUG_UPDATER_2:
                        printx(f"{CCFR}取消{CCZ0} updater_step_timer：{event_type}")
                    manager.unregister_updater_step_timer()

            else:
                if DEBUG:
                    manager.updater_skip_message += 1
                    if DEBUG_UPDATER_2:
                        print(f"跳过消息({manager.updater_skip_message}): {event_type}")

                # 在更新间隔内的消息，更新操作统一延迟到之后的 'TIMER' 消息
                if not manager.updater_step_timer:
                    _span_s = manager.register_updater_step_timer()
                    if DEBUG and DEBUG_UPDATER_2:
                        printx(f"{CCFG}设置{CCZ0} updater_step_timer：{event_type}, 间隔：{_span_s * 1000:.0f}ms")

        # -----

        if is_start_timer:
            if DEBUG:
                printx(f"捕获 {CCFA}handler_start_timer{CCZ0}：{event_type}")
            context.window_manager.event_timer_remove(manager.handler_start_timer)
            manager.handler_start_timer = None
            # 注意 ：必须加 UNDO = True，否则标点的输入会无法撤销
            bpy.ops.wire_fix_ime.input_handler('INVOKE_DEFAULT', True)

        return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

    @classmethod
    def add_key_map_item(clss) -> None:
        if DEBUG:
            printx("设置快捷键")
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        km.keymap_items.new(clss.bl_idname, type='MOUSEMOVE', value='ANY')
        km.keymap_items.new(clss.bl_idname, type='TIMER', value='ANY',
                            ctrl=-1, shift=-1, alt=-1, oskey=-1)  # 注意 ：修饰键

    @classmethod
    def remove_key_map_item(clss) -> None:
        if DEBUG:
            printx("卸载快捷键")
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
        event_type = event.type

        # 通过选项关闭状态更新器时，无法主动关闭模态操作，因此通过设置标记让其自行在某个时机结束。
        if not self.valid:
            self.close('INVALID')
            return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

        if manager.handler_update_timer:
            if DEBUG:
                printx(f"捕获 {CCFA}handler_update_timer{CCZ0}：{event_type}")
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
            else:
                # 输入结束后需要手动更新一下状态
                bpy.ops.wire_fix_ime.state_updater('INVOKE_DEFAULT')

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

    if DEBUG and DEBUG_CANDIDATE_POS:
        printx("text_editor offset: ", offset_x, offset_y)
        printx("text_editor region: ", region.x, region.y)
        printx("text_editor client: ", client_x, client_y)

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

    if DEBUG and DEBUG_CANDIDATE_POS:
        printx("console rect: ", rect_l, rect_t, rect_r, rect_b)

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

    if DEBUG and DEBUG_HEADER_REDRAW:
        if context.space_data.type == 'TEXT_EDITOR':
            printx('TEXT_EDITOR 重绘')
        elif context.space_data.type == 'CONSOLE':
            printx('CONSOLE 重绘')

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
    if native.dll:

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
    bpy.utils.unregister_class(WIRE_FIX_IME_Preferences)

    if DEBUG_BUILD:
        printx(CCFY, f"===== {__package__} end =====")
    pass
