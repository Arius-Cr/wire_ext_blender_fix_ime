from typing import cast, Literal, Union
from types import SimpleNamespace
from pathlib import Path
import time

import bpy
from bpy.types import Context, Event, Operator, Region
from bpy.types import SpaceView3D, SpaceTextEditor, TextLine, SpaceConsole, ConsoleLine
import gpu
import gpu_extras
from gpu_extras.batch import batch_for_shader
import blf
from mathutils import Color

from .debug.mark import mark
DEBUG_BUILD = mark.DEBUG_BUILD
DEBUG = mark.DEBUG
DEBUG_UPDATER_1 = mark.DEBUG_UPDATER_1
DEBUG_UPDATER_2 = mark.DEBUG_UPDATER_2
DEBUG_UPDATER_3 = mark.DEBUG_UPDATER_3
DEBUG_CANDIDATE_POS = mark.DEBUG_CANDIDATE_POS
DEBUG_GET_MODAL_HANDLER_SIZE = mark.DEBUG_GET_MODAL_HANDLER_SIZE

from .utils.printx import *

from .native import native, IMEData, IMEInvoker, IMEInvokerMaps
from .native import (
    FIEV_NONE,
    FIEV_COMP_START,
    FIEV_COMP_INPUT,
    FIEV_COMP_END,
    FIEV_BUTTON_DOWN,
    FIEV_LOST_FOCUS,
    FIEV_WINDOW_DESTORY,
    FIEVMaps)

from .prefs import get_prefs, Prefs

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

def register():
    bpy.utils.register_class(WIRE_FIX_IME_OT_state_updater)
    bpy.utils.register_class(WIRE_FIX_IME_OT_input_handler)
    pass

def unregister():
    bpy.utils.unregister_class(WIRE_FIX_IME_OT_state_updater)
    bpy.utils.unregister_class(WIRE_FIX_IME_OT_input_handler)
    pass

def use_debug_update():
    global DEBUG
    global DEBUG_UPDATER_1, DEBUG_UPDATER_2, DEBUG_UPDATER_3, DEBUG_CANDIDATE_POS
    global DEBUG_GET_MODAL_HANDLER_SIZE
    DEBUG = mark.DEBUG
    DEBUG_UPDATER_1 = mark.DEBUG_UPDATER_1
    DEBUG_UPDATER_2 = mark.DEBUG_UPDATER_2
    DEBUG_UPDATER_3 = mark.DEBUG_UPDATER_3
    DEBUG_CANDIDATE_POS = mark.DEBUG_CANDIDATE_POS
    DEBUG_GET_MODAL_HANDLER_SIZE = mark.DEBUG_GET_MODAL_HANDLER_SIZE
    pass

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


SpaceType = Literal['VIEW_3D', 'TEXT_EDITOR', 'CONSOLE']

CompositionEventType = Literal['START', 'INPUT', 'END']

# 用于将 FIEV 映射为 CompositionEventType
CompositionEventMaps = {1: 'START', 2: 'INPUT', 3: 'END'}

show_caret = True if DEBUG_BUILD else False

ns_to_ms: int = 1000000
ns_to_s: int = 1000000000
updater_step_f: float = 0.050  # s

updater_step_i: int = updater_step_f * ns_to_s  # 1s = 1 000 ms 000 μs 000 ns

# font_path, font_size, cwidth
cwidth_cache: list[tuple[str, float, int]] = []

managers: dict[bpy.types.Window, 'Manager'] = {}


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

class Manager():
    fix_field_enabled: bool = False
    fix_space_enabled: bool = False
    _redraw_listener_view3d_text_edit = None
    _redraw_listener_text_editor = None
    _redraw_listener_console = None

    @classmethod
    def get_manager(clss, wm_pointer: int):
        manager: Manager = None
        for k, v in managers.items():
            if k.as_pointer() == wm_pointer:
                manager = v
                break
        return manager

    def __init__(self):
        self.window: bpy.types.Window = None
        self.wm_pointer: int = None

        # -----
        # 输入法状态更新

        # 上次状态更新的时间（time_ns）
        self.updater_prev_step_time: int = 0

        # 已注册的用于引发状态更新的 'TIMER' 消息的 Timer 对象
        self.updater_start_timer: bpy.types.Timer = None

        # 表示更新间隔中被跳过的消息数量（仅用于调试）
        self.updater_skip_message: int = 0

        # -----
        # 输入法文本合成

        # 已启动的输入处理器
        self.handler: WIRE_FIX_IME_OT_input_handler = None

        # 通过 'TIMER' 消息触发 ime_compose 操作
        self.handler_start_timer: bpy.types.Timer = None

        # 通过 'TIMER' 消息触发 ime_compose 操作
        self.handler_update_timer: bpy.types.Timer = None

        # 文本合成消息，包括：开始、刷新（更新、确认、取消）
        self.input_events: list[tuple[CompositionEventType, IMEData, int]] = []

        pass

    # ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    # 选项开启和关闭

    @classmethod
    def option_update(clss, prefs: Union[Prefs, SimpleNamespace], context: Context):
        _fix_field = prefs.use_fix_ime_for_field
        _fix_space = prefs.use_fix_ime_for_space and (
                     prefs.use_fix_ime_font_edit or
                     prefs.use_fix_ime_text_editor or
                     prefs.use_fix_ime_console)

        from .main import blender_data
        if not blender_data.is_compatible:
            _fix_field = False
            _fix_space = False

        native.use_fix_direct_input_caps_lock(True)
        native.use_fix_direct_input_all(True)

        # 启动或停止对消息的捕获

        if _fix_field or _fix_space:
            if not (clss.fix_field_enabled or clss.fix_space_enabled):
                native.use_fix_ime(True, Manager.event_callback)

                if DEBUG:
                    printx("设置快捷键")
                op_clss = WIRE_FIX_IME_OT_state_updater
                km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
                    'Screen Editing', space_type='EMPTY', region_type='WINDOW')
                km.keymap_items.new(op_clss.bl_idname, type='TIMER', value='ANY',
                                    ctrl=-1, shift=-1, alt=-1, oskey=-1)  # 注意 ：修饰键
                km.keymap_items.new(op_clss.bl_idname, type='MOUSEMOVE', value='ANY')
        else:
            if clss.fix_space_enabled or clss.fix_space_enabled:
                native.use_fix_ime(False)

                if DEBUG:
                    printx("卸载快捷键")
                op_clss = WIRE_FIX_IME_OT_state_updater
                km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
                    'Screen Editing', space_type='EMPTY', region_type='WINDOW')
                for _kmi in reversed(km.keymap_items):
                    if _kmi.idname == op_clss.bl_idname:
                        km.keymap_items.remove(_kmi)

        # 启动或停止对输入框的修复

        if _fix_field:
            if not clss.fix_field_enabled:
                native.use_fix_ime_for_field(True)

                clss.fix_field_enabled = True
        else:
            if clss.fix_field_enabled:
                native.use_fix_ime_for_field(False)

                clss.fix_field_enabled = False

        # 启动或停止对编辑器的修复

        if _fix_space:
            if not clss.fix_space_enabled:
                native.use_fix_ime_for_space(True)

                clss.fix_space_enabled = True

            if prefs.use_fix_ime_font_edit:
                if not clss._redraw_listener_view3d_text_edit:
                    clss._redraw_listener_view3d_text_edit = SpaceView3D.draw_handler_add(
                        clss.redraw_listener_view3d_text_edit, tuple(), 'WINDOW', 'POST_PIXEL')
            else:
                if clss._redraw_listener_view3d_text_edit:
                    SpaceView3D.draw_handler_remove(clss._redraw_listener_view3d_text_edit, 'WINDOW')
                    clss._redraw_listener_view3d_text_edit = None

            if prefs.use_fix_ime_text_editor:
                if not clss._redraw_listener_text_editor:
                    clss._redraw_listener_text_editor = SpaceTextEditor.draw_handler_add(
                    clss.redraw_listener_text_editor, tuple(), 'WINDOW', 'POST_PIXEL')
            else:
                if clss._redraw_listener_text_editor:
                    SpaceTextEditor.draw_handler_remove(clss._redraw_listener_text_editor, 'WINDOW')
                    clss._redraw_listener_text_editor = None

            if prefs.use_fix_ime_console:
                if not clss._redraw_listener_console:
                    clss._redraw_listener_console = SpaceConsole.draw_handler_add(
                    clss.redraw_listener_console, tuple(), 'WINDOW', 'POST_PIXEL')
            else:
                if clss._redraw_listener_console:
                    SpaceConsole.draw_handler_remove(clss._redraw_listener_console, 'WINDOW')
                    clss._redraw_listener_console = None
        else:
            if clss._redraw_listener_view3d_text_edit:
                SpaceView3D.draw_handler_remove(clss._redraw_listener_view3d_text_edit, 'WINDOW')
                clss._redraw_listener_view3d_text_edit = None

            if clss._redraw_listener_text_editor:
                SpaceTextEditor.draw_handler_remove(clss._redraw_listener_text_editor, 'WINDOW')
                clss._redraw_listener_text_editor = None

            if clss._redraw_listener_console:
                SpaceConsole.draw_handler_remove(clss._redraw_listener_console, 'WINDOW')
                clss._redraw_listener_console = None

            if clss.fix_space_enabled:
                native.use_fix_ime_for_space(False)

                for manager in list(managers.values()):
                    manager.close()

                managers.clear()

                clss.fix_space_enabled = False

        pass

    # ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    # 捕获和释放窗口

    def start(self, context: Context):
        window = context.window
        managers[window] = self

        self.window = window
        self.wm_pointer = window.as_pointer()

        # 将窗口指针和窗口句柄绑定
        native.hook_window(self.wm_pointer)

        if DEBUG:
            printx(CCFG, "管理器启动 (现有: %d)：%X (wm)" % (len(managers), self.wm_pointer))
        pass

    def close(self, window_destory: bool = False):
        if self.window in managers:
            managers.pop(self.window)
            wm = bpy.context.window_manager

            if self.updater_start_timer:
                wm.event_timer_remove(self.updater_start_timer)
                self.updater_start_timer = None

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
                printx(CCFY, "管理器关闭（剩余：%d）：%X (wm)" % (len(managers), self.wm_pointer))
            else:
                printx(CCFY, "管理器销毁（剩余：%d）：%X (wm)" % (len(managers), self.wm_pointer))
        pass

    @staticmethod
    def event_callback(wm_pointer: int, event: int, data_ptr: int):
        manager = Manager.get_manager(wm_pointer)
        if not manager:
            return

        if event in {FIEV_COMP_START, FIEV_COMP_END, FIEV_COMP_INPUT}:
            manager.composition_callback(event, data_ptr)

        elif event == FIEV_WINDOW_DESTORY:
            manager.close(window_destory=True)

        elif event == FIEV_BUTTON_DOWN:
            manager.button_down_callback()
        pass

    # ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    # 输入法状态更新

    def button_down_callback(self):
        _span_s = self.register_updater_start_timer()
        if DEBUG and DEBUG_UPDATER_2 and _span_s is not None:
            printx(f"{CCFG}设置{CCZ0} 更新器 - 启动 - 计时器：BUTTON_DOWN_CALLBACK, 间隔：{_span_s * 1000:.0f}ms")

    def register_updater_start_timer(self) -> Union[float, None]:
        if self.updater_start_timer:
            return
        # if (native.window_is_active(self.wm_pointer) and
        #     not native.window_is_mouse_capture(self.wm_pointer) and
        #     not self.handler and not self.handler_start_timer):
        #     wm = bpy.context.window_manager
        #     span = (self.updater_prev_step_time + updater_step_i - time.time_ns()) / ns_to_s + 0.001
        #     if span <= 0.001:
        #         span = 0.001
        #     self.updater_start_timer = wm.event_timer_add(span, window=self.window)
        #     return span
        # return
        wm = bpy.context.window_manager
        span = (self.updater_prev_step_time + updater_step_i - time.time_ns()) / ns_to_s + 0.001
        if span <= 0.001:
            span = 0.001
        self.updater_start_timer = wm.event_timer_add(span, window=self.window)
        return span

    def unregister_updater_start_timer(self):
        if not self.updater_start_timer:
            return
        wm = bpy.context.window_manager
        wm.event_timer_remove(self.updater_start_timer)
        self.updater_start_timer = None

    def ime_state_update(self, context: Context, event: Event):
        '''
        更新输入法状态。
        该函数同时处理文本框和编辑器中输入法启停状态的更新。
        '''

        # 窗口处于非活动状态无需更新输入法状态
        if not native.window_is_active(self.wm_pointer):
            if DEBUG:
                printx(CCBP, "取消更新：窗口非活动")
            return

        # 即将合成文本或正在合成文本时都无需更新
        if self.handler or self.handler_start_timer:
            if DEBUG:
                printx(CCBP, "取消更新：正在输入文字")
            return

        invoker_now = native.ime_invoker_get(self.wm_pointer)

        # 文本框激活时，无需执行任何处理
        if invoker_now == 'FIELD':
            if DEBUG:
                printx(CCBP, "取消更新：文本框已激活")
            return

        # 弹出菜单或弹出面板出现时，停用 IME
        if native.wmWindow_is_pop_active(self.wm_pointer):
            if DEBUG:
                printx(CCBP, "取消更新：浮动窗已开启")
            self.ime_disable()
            return

        # 鼠标被捕获时表示正在执行某种操作，此时无需更新
        # 该判断必须放在“弹出菜单”后，因为弹出菜单本身会捕获鼠标
        if native.window_is_mouse_capture(self.wm_pointer):
            if DEBUG:
                printx(CCBP, "取消更新：鼠标被捕获")
            return

        invoker_new: IMEInvoker = None

        prefs = get_prefs(context)

        obj = context.active_object
        area = context.area
        space = context.space_data
        region = context.region

        if not invoker_new and prefs.use_fix_ime_for_space:

            if prefs.use_fix_ime_font_edit:
                if (obj and obj.type == 'FONT' and obj.mode == 'EDIT' and
                    area and space and region and
                    space.type == 'VIEW_3D' and
                    region.type == 'WINDOW'
                ):
                    invoker_new = 'VIEW_3D'

            if prefs.use_fix_ime_text_editor:
                if (area and space and region and
                    space.type == 'TEXT_EDITOR' and
                    space.text is not None and
                    region.type == 'WINDOW'
                ):
                    invoker_new = 'TEXT_EDITOR'

            if prefs.use_fix_ime_console:
                if (area and space and region and
                    space.type == 'CONSOLE' and
                    region.type == 'WINDOW'
                ):
                    invoker_new = 'CONSOLE'

        if invoker_new:
            # 检测到符合条件的区块，如果当前没有启用输入法或当前鼠标所在空间和之前不同，则启用输入法
            if invoker_new != invoker_now:
                self.ime_enable(context, invoker_new)

            if DEBUG:
                printx(f"{CCFP}更新后{CCZ0} 重新定位候选窗口：", context.space_data.type)
            self.ime_window_pos_update(context)
        else:
            self.ime_disable()
        pass

    def ime_enable(self, context: Context, invoker: IMEInvoker):
        if DEBUG:
            printx(CCBA, "在区块中启用输入法：%s" % context.space_data.type)
        if not native.ime_enable(self.wm_pointer, invoker):
            raise Exception("启用输入法失败")

    def ime_disable(self):
        if DEBUG:
            printx(CCBB, f"在区块中停用输入法")
        if native.ime_disable(self.wm_pointer):
            pass
        else:
            raise Exception("停用输入法失败")

    # ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    # 候选框位置更新（输入前和输入时）

    @classmethod
    def redraw_listener_view3d_text_edit(clss):
        # 该函数仅为了捕获绘制消息，没有任何绘制操作
        # 绘制时，如果绘制的区块为活动区块，且启用了输入法，且处于非输入状态，
        # 则总是更新输入法候选框的位置。
        context = cast(Context, bpy.context)
        prefs = get_prefs(context)
        if prefs.use_fix_ime_text_editor:
            wm_pointer = context.window.as_pointer()
            manager = clss.get_manager(wm_pointer)
            if manager and not manager.handler:
                region_pointer = context.region.as_pointer()
                if native.wmWindow_active_region_get(wm_pointer) == region_pointer:
                    if native.ime_invoker_get(wm_pointer) == 'VIEW_3D':
                        if DEBUG:
                            printx(f"{CCFP}绘制后{CCZ0} 重新定位候选窗口")
                        manager.ime_window_pos_update_view3d_text_edit(context, None)
        pass

    @classmethod
    def redraw_listener_text_editor(clss):
        # 该函数仅为了捕获绘制消息，没有任何绘制操作
        # 绘制时，如果绘制的区块为活动区块，且启用了输入法，且处于非输入状态，
        # 则总是更新输入法候选框的位置。
        context = cast(Context, bpy.context)
        prefs = get_prefs(context)
        if prefs.use_fix_ime_text_editor:
            wm_pointer = context.window.as_pointer()
            manager = clss.get_manager(wm_pointer)
            if manager and not manager.handler:
                region_pointer = context.region.as_pointer()
                if native.wmWindow_active_region_get(wm_pointer) == region_pointer:
                    if native.ime_invoker_get(wm_pointer) == 'TEXT_EDITOR':
                        if DEBUG:
                            printx(f"{CCFP}绘制后{CCZ0} 重新定位候选窗口")
                        manager.ime_window_pos_update_text_editor(context, None)
        pass

    @classmethod
    def redraw_listener_console(clss):
        # 该函数仅为了捕获绘制消息，没有任何绘制操作
        # 绘制时，如果绘制的区块为活动区块，且启用了输入法，且处于非输入状态，
        # 则总是更新输入法候选框的位置。
        context = cast(Context, bpy.context)
        prefs = get_prefs(context)
        if prefs.use_fix_ime_text_editor:
            wm_pointer = context.window.as_pointer()
            manager = clss.get_manager(wm_pointer)
            if manager and not manager.handler:
                region_pointer = context.region.as_pointer()
                if native.wmWindow_active_region_get(wm_pointer) == region_pointer:
                    if native.ime_invoker_get(wm_pointer) == 'CONSOLE':
                        if DEBUG:
                            printx(f"{CCFP}绘制后{CCZ0} 重新定位候选窗口")
                        manager.ime_window_pos_update_console(context, None)
        pass

    def ime_window_pos_update(self, context: Context):
        space = context.space_data
        if space.type == 'VIEW_3D':
            self.ime_window_pos_update_view3d_text_edit(context)
        elif space.type == 'TEXT_EDITOR':
            self.ime_window_pos_update_text_editor(context)
        elif space.type == 'CONSOLE':
            self.ime_window_pos_update_console(context)
        pass

    def ime_window_pos_update_view3d_text_edit(self, context: Context, op: 'WIRE_FIX_IME_OT_input_handler' = None):
        window = context.window
        region = context.region
        space = cast(SpaceView3D, context.space_data)
        pref = get_prefs(context)

        c_l = region.width * pref.candidate_window_percent
        c_b = region.y
        c_w = 0
        c_h = 0

        # 转为基于窗口左上角的坐标
        c_l = int(region.x + c_l)
        c_t = int(window.height - (c_b + c_h))

        native.ime_move_candidate_window(window.as_pointer(),
            c_l, c_t, c_w, c_h, c_l, c_t, c_w, c_h, True if DEBUG else False)

    def ime_window_pos_update_text_editor(self, context: Context, op: 'WIRE_FIX_IME_OT_input_handler' = None):
        window = context.window
        region = context.region
        space = cast(SpaceTextEditor, context.space_data)
        text = space.text

        lheight, _, _ = self.get_text_editor_draw_params(context)
        pixelsize: float = context.preferences.system.pixel_size

        c_x: int = 0
        c_y: int = 0
        c_w: int = 0
        c_h: int = lheight
        e_x: int = region.x
        e_y: int = 0
        e_w: int = region.width
        e_h: int = 0

        if not op:
            cur_l, cur_b = self.text_editor_region_location_from_cursor(
                context, region, space,
                text.current_line_index,
                text.current_character)
            cur_l += region.x
            cur_b += region.y

            c_x = cur_l
            c_y = cur_b

            # 无论何时排除合成字符串的纵向空间
            e_y = cur_b
            e_h = lheight

        else:
            sta_l, sta_b = self.text_editor_region_location_from_cursor(
                context, region, space,
                text.current_line_index,
                op.stac_i)
            sta_l += region.x
            sta_b += region.y
            end_l, end_b = self.text_editor_region_location_from_cursor(
                context, region, space,
                text.current_line_index,
                op.endc_i)
            end_l += region.x
            end_b += region.y

            if op.clause_stac_i != -1 and op.clause_stac_i != op.clause_endc_i:
                # 存在焦点区时，将候选窗口定位到焦点区开头
                clause_l, clause_b = self.text_editor_region_location_from_cursor(
                    context, region, space,
                    text.current_line_index,
                    op.clause_stac_i)
                clause_l += region.x
                clause_b += region.y
                c_x = clause_l
                c_y = clause_b
            else:
                # 合成字符串为单行时，将候选窗口定位到合成字符串开头
                if sta_b == end_b:
                    c_x = sta_l
                    c_y = sta_b

                # 合成字符串为多行时，将候选窗口定位到合成字符串末尾
                else:
                    c_x = end_l
                    c_y = end_b
                    pass

            # 无论何时排除合成字符串的纵向空间
            e_y = end_b
            e_h = sta_b + lheight - end_b

        # 在上下方增加空间
        c_y -= 5 * pixelsize
        c_h += 10 * pixelsize
        e_y -= 5 * pixelsize
        e_h += 10 * pixelsize

        # 从左下角坐标转为左上角坐标
        c_y = window.height - (c_y + c_h)
        e_y = window.height - (e_y + e_h)

        native.ime_move_candidate_window(window.as_pointer(),
            int(c_x), int(c_y), int(c_w), int(c_h),
            int(e_x), int(e_y), int(e_w), int(e_h), True if DEBUG else False)
        pass

    def ime_window_pos_update_console(self, context: Context, op: 'WIRE_FIX_IME_OT_input_handler' = None):
        window = context.window
        region = context.region
        space = cast(SpaceConsole, context.space_data)
        text = cast(ConsoleLine, space.history[-1])

        scale_factor: float = context.preferences.system.ui_scale
        pixelsize: float = context.preferences.system.pixel_size
        widget_unit: int = int(int(round(18.0 * scale_factor)) + (2 * pixelsize))

        UI_SCALE_FAC = scale_factor

        lheight = space.font_size * UI_SCALE_FAC

        c_x: int = 0
        c_y: int = 0
        c_w: int = 0
        c_h: int = lheight
        e_x: int = region.x
        e_y: int = 0
        e_w: int = region.width
        e_h: int = 0

        if not op:
            cur_l, cur_b = self.console_region_location_from_cursor(
                context, region, space, self.get_console_cursor_i(text))
            cur_l += region.x
            cur_b += region.y

            c_x = cur_l
            c_y = cur_b

            # 无论何时排除合成字符串的纵向空间
            e_y = cur_b
            e_h = lheight

        else:
            sta_l, sta_b = self.console_region_location_from_cursor(
                context, region, space, op.stac_i)
            sta_l += region.x
            sta_b += region.y
            end_l, end_b = self.console_region_location_from_cursor(
                context, region, space, op.endc_i)
            end_l += region.x
            end_b += region.y

            if op.clause_stac_i != -1 and op.clause_stac_i != op.clause_endc_i:
                # 存在焦点区时，将候选窗口定位到焦点区开头
                clause_l, clause_b = self.console_region_location_from_cursor(
                context, region, space, op.clause_stac_i)
                clause_l += region.x
                clause_b += region.y
                c_x = clause_l
                c_y = clause_b
            else:
                # 合成字符串为单行时，将候选窗口定位到合成字符串开头
                if sta_b == end_b:
                    c_x = sta_l
                    c_y = sta_b

                # 合成字符串为多行时，将候选窗口定位到合成字符串末尾
                else:
                    c_x = end_l
                    c_y = end_b
                    pass

            # 无论何时排除合成字符串的纵向空间
            e_y = end_b
            e_h = sta_b + lheight - end_b

        # 在上下方增加空间
        c_y -= 5 * pixelsize
        c_h += 10 * pixelsize
        e_y -= 5 * pixelsize
        e_h += 10 * pixelsize

        # 从左下角坐标转为左上角坐标
        c_y = window.height - (c_y + c_h)
        e_y = window.height - (e_y + e_h)

        native.ime_move_candidate_window(window.as_pointer(),
            int(c_x), int(c_y), int(c_w), int(c_h),
            int(e_x), int(e_y), int(e_w), int(e_h), True if DEBUG else False)
        pass

    # -----
    # 获取文本编辑器相关的尺寸信息，以便定位候选框和绘制下划线

    @classmethod
    def text_editor_region_location_from_cursor(clss, context: Context, region: Region, space: SpaceTextEditor, line_i: int, char_i: int) -> tuple[int, int]:
        text = space.text
        line = cast(TextLine, text.lines[line_i])

        if bpy.app.version >= (4, 2, 2):
            # 4.2.2 及以上版本已经修正问题
            x, y = space.region_location_from_cursor(line_i, char_i)
        else:
            x, y = space.region_location_from_cursor(line_i, len(line.body[:char_i].encode('utf-8')))

            '''
            region_location_from_cursor 返回的坐标存在以下问题：
            1、第二个参数传入错误的值会导致返回的 X 坐标出现偏移。
            第二个参数从文档来看，要求输入字符索引，但源码中似乎出现了差错，被当成字节偏移来使用，因此需要传入字节偏移而非索引。
            2、返回的 Y 坐标存在一定的偏移。
            y1 为官方计算公式（存在错误），y2 为正确的计算公式
            y1 = (region->winy - (r_pixel_co[1] + (TXT_BODY_LPAD * st->runtime.cwidth_px))) - st->runtime.lheight_px;
            y1 = (region->winy - r_pixel_co[1]) - (TXT_BODY_LPAD * st->runtime.cwidth_px) - st->runtime.lheight_px;
            y2 = (region->winy - r_pixel_co[1]) - line_height;
            y2 = y1 + st->runtime.lheight_px + (TXT_BODY_LPAD * st->runtime.cwidth_px) - line_height;
            设 correct = st->runtime.lheight_px + (TXT_BODY_LPAD * st->runtime.cwidth_px) - line_height，
            则 y1 + correct 则为正确的 Y 坐标。
            '''

            # 参考源码：region_location_from_cursor

            lheight_px = native.SpaceText_lheight_px_get(space.as_pointer())

            TXT_LINE_VPAD: float = 0.3
            TXT_LINE_HEIGHT = int((1 + TXT_LINE_VPAD) * lheight_px)
            lheight = TXT_LINE_HEIGHT

            TXT_BODY_LPAD = 1.0

            cwidth_px = native.SpaceText_cwidth_px_get(space.as_pointer())

            correct = lheight_px + int(TXT_BODY_LPAD * cwidth_px) - lheight

            y = y + correct

        return x, y

    @classmethod
    def get_text_editor_draw_params(clss, context: Context) -> tuple[
        int,  # lheight, 行高
        int,  # draw_xmin, 区块中的绘制区域
        int,  # draw_xmax
    ]:
        '''
        return: lheight, draw_xmin, draw_xmax,
        '''
        region = context.region
        st = cast(SpaceTextEditor, context.space_data)

        scale_factor: float = context.preferences.system.ui_scale  # U.scale_factor
        pixelsize: float = context.preferences.system.pixel_size
        widget_unit: int = int(int(round(18.0 * scale_factor)) + (2 * pixelsize))

        lheight_px = native.SpaceText_lheight_px_get(st.as_pointer())
        TXT_LINE_VPAD: float = 0.3
        TXT_LINE_HEIGHT = int((1 + TXT_LINE_VPAD) * lheight_px)
        lheight = TXT_LINE_HEIGHT

        cwidth_px = native.SpaceText_cwidth_px_get(st.as_pointer())

        TXT_BODY_LPAD = 1.0

        TXT_NUMCOL_PAD = 1.0

        linenr_offset: int = 0
        if st.show_line_numbers:
            linenr_offset = (cwidth_px *
                             (native.SpaceText_line_number_display_digits_get(st.as_pointer()) + 2 * TXT_NUMCOL_PAD)
                            ) + (TXT_BODY_LPAD * cwidth_px)
        else:
            linenr_offset = 0 + (TXT_BODY_LPAD * cwidth_px)
        linenr_offset = int(linenr_offset)

        TXT_SCROLL_WIDTH: int = widget_unit

        draw_xmin: int = linenr_offset
        draw_xmax: int = region.width - TXT_SCROLL_WIDTH

        return (lheight, draw_xmin, draw_xmax)

    # -----
    # 获取控制台相关的尺寸信息，以便定位候选框和绘制下划线

    @classmethod
    def console_region_location_from_cursor(clss, context: Context, region: Region, space: SpaceConsole, cursor: int) -> tuple[int, int]:
        text = cast(ConsoleLine, space.history[-1])

        scale_factor: float = context.preferences.system.ui_scale

        lheight, draw_xmin, draw_xmax, draw_ymin, draw_ymax = clss.get_console_draw_params(context)

        # printx(CCFA, "console font_size", space.font_size)
        # printx(CCFA, "console lheight", lheight)
        # printx(CCFA, "console draw_xmin", draw_xmin)
        # printx(CCFA, "console draw_xmax", draw_xmax)
        # printx(CCFA, "console draw_ymin", draw_ymin)
        # printx(CCFA, "console draw_ymax", draw_ymax)

        # 参考源码：textview_font_begin()

        if context.preferences.view.font_path_ui_mono:
            font_path = context.preferences.view.font_path_ui_mono
        else:
            local = Path(bpy.utils.resource_path('LOCAL'))
            if bpy.app.version >= (3, 4, 0):
                font_path = str(local.joinpath('datafiles', 'fonts', 'DejaVuSansMono.woff2'))
            else:
                font_path = str(local.joinpath('datafiles', 'fonts', 'bmonofont-i18n.ttf'))

        # 参考源码：textview_draw() 中 tds.cwidth
        if bpy.app.version >= (3, 1, 0):
            font_size = lheight * 0.8
        else:
            font_size = int(lheight * 0.8)

        cwidth: Union[int, None] = None

        global cwidth_cache
        for _font_path, _font_size, _cwidth in cwidth_cache:
            if _font_path == font_path and _font_size == font_size:
                cwidth = _cwidth
                break
        if cwidth is None:
            cwidth = native.BLF_fixed_width(font_path, font_size)
            cwidth_cache.append((font_path, font_size, cwidth))

        if cwidth < 1:  # 获取失败会返回 -1，此时无视失败即可，界面上会看出异常
            cwidth = 1

        # printx(CCFA, "console cwidth", cwidth, scale_factor, cwidth * scale_factor)

        # printx(CCFA, "text_str", space.prompt + text.body)

        columns = int((draw_xmax - draw_xmin) / cwidth)
        if columns < 1:
            columns = 1

        # printx(CCFA, "columns", columns)

        offl = 0
        offc = 0
        # printx(CCFA, "cursor:", cursor)
        offl, offc = clss.console_cursor_wrap_offset(space.prompt, 0, -1, columns, offl, offc)
        # printx(CCFA, "offl, offc 1:", offl, offc)
        offl, offc = clss.console_cursor_wrap_offset(text.body, 0, cursor, columns, offl, offc)
        # printx(CCFA, "offl, offc 2:", offl, offc)
        x = cwidth * offc
        y = -lheight * offl

        offl, offc = clss.console_cursor_wrap_offset(text.body, cursor, -1, columns, offl, offc)
        # printx(CCFA, "offl, offc 3:", offl, offc)
        y += lheight * offl

        x += draw_xmin
        y += draw_ymin

        return (x, y)

    @classmethod
    def get_console_draw_params(clss, context: Context) -> tuple[
        int,  # lheight, 行高
        int,  # draw_xmin, 区块中的绘制区域
        int,  # draw_xmax
        int,  # draw_ymin
        int,  # draw_ymax
    ]:
        region = context.region
        space = cast(SpaceConsole, context.space_data)

        scale_factor: float = context.preferences.system.ui_scale
        pixelsize: float = context.preferences.system.pixel_size
        widget_unit: int = int(int(round(18.0 * scale_factor)) + (2 * pixelsize))

        UI_SCALE_FAC = scale_factor
        V2D_SCROLL_WIDTH = 0.45 * widget_unit + 2.00 * pixelsize

        # 参考源码：

        lheight = int(space.font_size * scale_factor)

        # printx(CCFA, "space.font_size: ", space.font_size, scale_factor)

        # 参考源码：

        margin = 4 * UI_SCALE_FAC

        draw_xmin = margin
        draw_xmax = region.width - V2D_SCROLL_WIDTH
        draw_ymin = margin
        draw_ymax = region.height

        return (lheight, draw_xmin, draw_xmax, draw_ymin, draw_ymax)

        pass

    @classmethod
    def console_cursor_wrap_offset(clss, chars: str, start: int, end: int, columns: int, row: int, column: int) -> tuple[int, int]:
        tab_width = 4

        index = 0
        for char in chars:
            if index < start:
                index += 1
                continue

            if char == '\t':
                col = column % tab_width
            else:
                ucs = ord(char)
                if ((ucs >= 0xF0000) or
                    (ucs >= 0x0E000 and ucs < 0x0F8FF) or
                    (ucs >= 0x1F300 and ucs < 0x1FBFF) or
                    (ucs >= 0x1100 and
                     (
                        (ucs <= 0x115f) or
                        (ucs == 0x2329) or (ucs == 0x232a) or
                        (ucs >= 0x2E80 and ucs <= 0xA4CF and ucs != 0x303F) or  # CJK
                        (ucs >= 0xac00 and ucs <= 0xd7a3) or  # Hangul Syllables
                        (ucs >= 0xf900 and ucs <= 0xfaff) or  # CJK Compatibility Ideographs
                        (ucs >= 0xfe10 and ucs <= 0xfe19) or  # Vertical forms
                        (ucs >= 0xfe30 and ucs <= 0xfe6f) or  # CJK Compatibility Forms
                        (ucs >= 0xff00 and ucs <= 0xff60) or  # Fullwidth Forms
                        (ucs >= 0xffe0 and ucs <= 0xffe6) or
                        (ucs >= 0x20000 and ucs <= 0x2fffd) or
                        (ucs >= 0x30000 and ucs <= 0x3fffd)
                     )
                    )
                   ):
                    # printx(CCFA, "全角", char)
                    col = 2
                else:
                    # 忽略 \0 等特殊字符
                    # printx(CCFA, "半角", char)
                    col = 1

            if column + col > columns:
                row += 1
                column = 0

            if end >= 0 and index >= end:
                break

            column += col

            index += 1

        return (row, column)

    @classmethod
    def get_console_cursor_i(clss, text: ConsoleLine) -> int:
        # 4.1.0 之前的版本中，text.current_character 返回的是字节偏移，此处要计算出其索引
        # 在 4.1.0 及其后的版本中 text.current_character 就是索引。
        if bpy.app.version >= (4, 1, 0):
            return text.current_character
        else:
            str_bytes = text.body.encode('utf-8')[:text.current_character]
            return len(str_bytes.decode('utf-8'))

    # ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    # 输入法文本合成

    def composition_callback(self, _event: int, data_ptr: int):
        ime_data = native.get_ime_data(data_ptr) if data_ptr else None

        _time = 0
        if DEBUG:
            _time = time.perf_counter_ns()
            _composite_str = ime_data.composite_str if ime_data else None
            _result_str = ime_data.result_str if ime_data else None
            printx("派送消息(wm: %X)：" % self.wm_pointer,
                FIEVMaps[_event], _composite_str, _result_str)

        event = cast(CompositionEventType, CompositionEventMaps[_event])

        self.input_events.append((event, ime_data, _time))

        self.register_input_handler_timer()
        pass

    def register_input_handler_timer(self) -> bool:
        if len(self.input_events) > 0:
            event, _, _ = self.input_events[0]
            if event == 'START':
                if not self.handler and not self.handler_start_timer:
                    self.register_input_handler_start_timer()
            else:
                if self.handler and not self.handler_update_timer:
                    self.register_input_handler_update_timer()
        return False

    def register_input_handler_start_timer(self):
        if self.handler_start_timer:
            return
        if DEBUG:
            printx(f"{CCFA}设置{CCZ0} 处理器 - 启动 - 计时器")
        self.handler_start_timer = bpy.context.window_manager.event_timer_add(0.001, window=self.window)
        pass

    def unregister_input_handler_start_timer(self):
        if not self.handler_start_timer:
            return
        wm = bpy.context.window_manager
        wm.event_timer_remove(self.handler_start_timer)
        self.handler_start_timer = None
        pass

    def register_input_handler_update_timer(self):
        if self.handler_update_timer:
            return
        if DEBUG:
            printx(f"{CCFA}设置{CCZ0} 处理器 - 更新 - 计时器")
        self.handler_update_timer = bpy.context.window_manager.event_timer_add(0.001, window=self.window)
        pass

    def unregister_input_handler_update_timer(self):
        if not self.handler_update_timer:
            return
        wm = bpy.context.window_manager
        wm.event_timer_remove(self.handler_update_timer)
        self.handler_update_timer = None
        pass


class WIRE_FIX_IME_OT_state_updater(Operator):
    bl_idname = 'wire_fix_ime.state_updater'
    bl_label = "状态更新器"
    bl_description = "(仅供输入法助手内部使用)"
    bl_options = set()

    @ classmethod
    def poll(clss, context: Context) -> bool:
        if Manager.fix_field_enabled or Manager.fix_space_enabled:
            return True
        return False

    def invoke(self, context: Context, event: Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        window = context.window
        event_type = event.type  # 当消息为 'TIMER' 时取消了相关的定时器，会导致消息立即变为 'NONE'

        if window not in managers:
            window = context.window
            manager = Manager()
            manager.start(context)
        manager = managers[window]

        # 此处仅会接收到 MOUSEMOVE 和 TIMER 两种消息。
        # 其中 TIMER 消息有三种信源：
        # 1、manager.register_updater_start_timer()
        # 2、manager.register_input_handler_start_timer()
        # 3、其它
        # 其中 TIMER 消息的第三种信源是计划外的，需要排除。
        # 不排除也可以，因为状态更新逻辑并不依赖 MOUSEMOVE 或 TIMER 消息发生的时机，
        # 因此何时执行更新都可以，都会得到正确的结果。

        if event_type == 'TIMER':
            is_updater_start_timer = (manager.updater_start_timer and manager.updater_start_timer.time_delta)
            is_handler_start_timer = (manager.handler_start_timer and manager.handler_start_timer.time_delta)
            if not (is_updater_start_timer or is_handler_start_timer):
                if DEBUG and DEBUG_UPDATER_2:
                    printx("无关的 TIMER 消息")
                    printx(manager.updater_start_timer)
                    printx(manager.handler_start_timer)
                return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}
        else:
            is_updater_start_timer = False
            is_handler_start_timer = False

        # -----

        if event_type == 'MOUSEMOVE' or is_updater_start_timer:

            if is_updater_start_timer:
                if DEBUG and DEBUG_UPDATER_2:
                    printx(f"{CCFB}捕获{CCZ0} 更新器 - 启动 - 计时器：{event_type}")
                manager.unregister_updater_start_timer()

            span_step = (_now := time.time_ns()) - manager.updater_prev_step_time
            if span_step >= updater_step_i:
                manager.updater_prev_step_time = _now

                if DEBUG and DEBUG_UPDATER_1:
                    _time = time.perf_counter_ns()

                manager.ime_state_update(context, event)

                if DEBUG:
                    if DEBUG_UPDATER_1:
                        _span = time.perf_counter_ns() - _time
                        printx(f"{CCFY}状态已更新（间隔: {round(span_step / ns_to_ms, 3): >8.3f}ms，"
                            f"跳过: {manager.updater_skip_message: >2d}）{CCZ0}"
                            f"更新用时：{round(_span / ns_to_ms, 3):.3f}ms，{event_type}")
                    manager.updater_skip_message = 0

                if manager.updater_start_timer:
                    if DEBUG and DEBUG_UPDATER_2:
                        printx(f"{CCFR}取消{CCZ0} 更新器 - 启动 - 计时器：{event_type}")
                    manager.unregister_updater_start_timer()

            else:
                if DEBUG:
                    manager.updater_skip_message += 1
                    if DEBUG_UPDATER_2:
                        print(f"跳过消息({manager.updater_skip_message}): {event_type}")

                # 在更新间隔内的消息，更新操作统一延迟到之后的 'TIMER' 消息
                if not manager.updater_start_timer:
                    _span_s = manager.register_updater_start_timer()
                    if DEBUG and DEBUG_UPDATER_2 and _span_s is not None:
                        printx(f"{CCFG}设置{CCZ0} 更新器 - 启动 - 计时器：{event_type}, 间隔：{_span_s * 1000:.0f}ms")

        # -----

        if is_handler_start_timer:
            if DEBUG:
                printx(f"{CCFA}捕获{CCZ0} 处理器 - 启动 - 计时器：{event_type}")
            manager.unregister_input_handler_start_timer()

            # 注意 ：必须加 UNDO = True，否则标点的输入会无法撤销
            bpy.ops.wire_fix_ime.input_handler('INVOKE_DEFAULT', True)

        return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

class WIRE_FIX_IME_OT_input_handler(Operator):
    bl_idname = 'wire_fix_ime.input_handler'
    bl_label = "输入处理器"
    bl_description = "(仅供输入法助手内部使用)"
    bl_options = set()

    # 注意 ：bl_options 必须不能有 'UNOD'，否则无法在【物体处于编辑模式】时，撤销在【文本编辑器】中输入的文本

    @classmethod
    def poll(clss, context: Context) -> bool:
        window = context.window
        if window not in managers:
            return False
        manager = managers[window]
        if len(manager.input_events) <= 0:
            return False

        space = context.space_data
        if space:
            if space.type == 'VIEW_3D':
                obj = context.active_object
                if obj and obj.type == 'FONT' and obj.mode == 'EDIT':
                    if manager.input_events[0][0] == 'START':
                        return True

            elif space.type == 'TEXT_EDITOR':
                if cast(SpaceTextEditor, space).text:
                    if manager.input_events[0][0] == 'START':
                        return True

            elif space.type == 'CONSOLE':
                if manager.input_events[0][0] == 'START':
                    return True
        return False

    def __init__(self):
        super().__init__()
        self.manager = None
        self.valid: bool = True

        self.op_args: list[object] = ['EXEC_REGION_WIN', False]

        self.space: Union[SpaceTextEditor, SpaceConsole] = None
        self.draw_handler = None

        self.op_insert = None
        self.op_delete = None
        self.op_move = None
        self.op_select = None

        # 记录合成文本和待选文本在当前行中的开始和结束位置
        self.stac_i: int = -1
        self.endc_i: int = -1
        self.clause_stac_i: int = -1
        self.clause_endc_i: int = -1

        # 上次输入消息中合成文本的长度（含作为标记的中括号）
        self.length: int = 0

        # 上次输入消息中合成文本中光标相对合成文本末尾的字符数（含作为标记的中括号）
        self.move_times: int = 0

        # 主要用于微软韩语输入法
        self.extra_chars: list[str] = []
        pass

    def invoke(self, context: Context, event: Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        window = context.window
        space: Union[SpaceTextEditor, SpaceConsole] = context.space_data
        space_type = context.space_data.type
        self.manager = managers[window]
        self.manager.handler = self

        if DEBUG:
            printx(CCBG, "输入处理器启动")

        if space_type == 'VIEW_3D':
            self.op_insert = bpy.ops.font.text_insert
            self.op_delete = bpy.ops.font.delete
            self.op_move = bpy.ops.font.move
            self.op_select = bpy.ops.font.move_select
        if space_type == 'TEXT_EDITOR':
            self.op_insert = bpy.ops.text.insert
            self.op_delete = bpy.ops.text.delete
            self.op_move = bpy.ops.text.move
            self.op_select = bpy.ops.text.move_select
        elif space_type == 'CONSOLE':
            self.op_insert = bpy.ops.console.insert
            self.op_delete = bpy.ops.console.delete
            self.op_move = bpy.ops.console.move
            self.op_select = None,  # 该操作由 move 提供

        manager = self.manager
        event_type = event.type

        if manager.handler_update_timer:
            if DEBUG:
                printx(f"{CCFA}捕获{CCZ0} 处理器 - 更新 - 计时器：{event_type}")
            manager.unregister_input_handler_update_timer()

        if len(self.manager.input_events) > 0:
            ret = self.process_ime_events(context, event)
            if 'RUNNING_MODAL' not in ret:
                return ret

        self.space = space

        if space_type == 'TEXT_EDITOR':
            self.draw_handler = space.draw_handler_add(
                self.draw_comp_underline_text_editor, (context,), 'WINDOW', 'POST_PIXEL')
        elif space_type == 'CONSOLE':
            self.draw_handler = space.draw_handler_add(
                self.draw_comp_underline_console, (context,), 'WINDOW', 'POST_PIXEL')

        context.workspace.status_text_set("正在通过输入法输入文本...")

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context: Context, event: Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        manager = self.manager
        event_type = event.type

        # 通过选项关闭状态更新器时，无法主动关闭模态操作，因此通过设置标记让其自行在某个时机结束。
        if not self.valid:
            self.close('INVALID')
            return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

        if manager.handler_update_timer:
            if DEBUG:
                printx(f"{CCFA}捕获{CCZ0} 处理器 - 更新 - 计时器：{event_type}")
            manager.unregister_input_handler_update_timer()

        if len(manager.input_events) > 0:
            ret = self.process_ime_events(context, event)
            return ret

        return {'RUNNING_MODAL'}

    def cancel(self, context: Context):
        self.close('CANCEL', context)

    def close(self, reason: Literal['FINISH', 'CANCEL', 'MANAGER_CLOSE', 'INVALID'], context: Context = None):
        manager = self.manager

        self.valid = False  # 实际上仅用于 MANAGER_CLOSE

        if context:
            context.workspace.status_text_set(None)

        if manager.handler == self:
            manager.handler = None

        if self.draw_handler:
            self.space.draw_handler_remove(self.draw_handler, 'WINDOW')
            self.draw_handler = None

        if DEBUG:
            if reason == 'FINISH':
                if DEBUG:
                    printx(CCBP, "输入处理器结束：%X (wm)" % manager.wm_pointer)
            # 窗口关闭时（模态操作的 cancel 早于 window_destory_callback 被调用）
            if reason == 'CANCEL':
                if DEBUG:
                    printx(CCBP, "输入处理器关闭：%X (wm)" % manager.wm_pointer)
            # 选项关闭或插件停用时（插件停用时模态操作的 modal 不会被调用，但不会有任何影响）
            elif reason == 'MANAGER_CLOSE':
                if DEBUG:
                    printx(CCBP, "输入处理失效（等待）：%X (wm)" % manager.wm_pointer)
            # modal 中检测到 self.valid == False 时
            elif reason == 'INVALID':
                if DEBUG:
                    printx(CCBP, "输入处理失效（完成）：%X (wm)" % manager.wm_pointer)
        pass

    # -----

    def process_ime_events(self, context: Context, event: Event) -> Literal['RUNNING_MODAL', 'CANCELLED', 'FINISHED', 'PASS_THROUGH', 'INTERFACE']:
        event_type = cast(str, event.type)
        space = cast(SpaceTextEditor, context.space_data)
        space_type = space.type

        # 针对微软韩语输入法及其类似输入法而特意存在的代码。
        # 捕捉IME没有处理的单独字符键（该操作用于类微软韩语输入法的输入法）
        if event.value == 'PRESS':
            if event.ascii:
                if DEBUG:
                    printx(CCFA, "捕获结束字符（用于韩语）：[%s]" % event.ascii)
                self.extra_chars.append(event.ascii)
            elif event_type in ['RET', 'NUMPAD_ENTER']:
                if DEBUG:
                    printx(CCFA, "捕获结束字符（用于韩语）：回车", event.ascii)
                self.extra_chars.append('\n')

        manager = self.manager
        while len(manager.input_events) > 0:
            event, data, _ = (ime_event := manager.input_events.pop(0))

            if space_type == 'VIEW_3D':
                self.process_view3d_text_edit(context, ime_event)
            elif space_type == 'TEXT_EDITOR':
                self.process_text_editor(context, ime_event)
            elif space_type == 'CONSOLE':
                self.process_console(context, ime_event)

            if event == 'END':

                # 针对微软韩语输入法及其类似输入法而特意存在的代码
                # 输入韩语文字的时候，最后一个待定字符会在 'END' 事件后，以 'INPUT' 事件传递过来。
                ev_next = manager.input_events[0] if len(manager.input_events) > 0 else None
                if ev_next and ev_next[0] == 'INPUT':
                    manager.input_events.pop(0)
                    if ev_next[1].result_str is not None:
                        if DEBUG:
                            printx(CCFA, "插入末尾字符（用于韩语）：", ev_next[1].result_str)
                        self.op_insert('INVOKE_DEFAULT', True, text=ev_next[1].result_str)
                # 输入韩语文字的时候，最后按下空格、标点等按键时，会强制结束合成，同时这些按键也会产生字符。
                if self.extra_chars:
                    for char in self.extra_chars:
                        if DEBUG:
                            printx(CCFA, "插入结束字符（用于韩语）：[%s]" % char)
                        self.op_insert('INVOKE_DEFAULT', True, text=char)

                self.close('FINISH', context)

                if len(manager.input_events) > 0:
                    if DEBUG:
                        printx(CCBR, "等待下一轮进行处理，剩余消息：", len(manager.input_events))
                    manager.register_input_handler_timer()
                else:
                    # 输入结束后更新状态
                    manager.register_updater_start_timer()

                break  # 中止当前这轮处理

        return {'RUNNING_MODAL'} if manager.handler else {'CANCELLED'}

    def process_view3d_text_edit(self, context: Context, ime_event: tuple[CompositionEventType, IMEData, int]):
        event, data, _ = ime_event
        args = self.op_args

        if event == 'START':
            if DEBUG:
                printx(CCFR, "删除选择")
            self.op_delete(*self.op_args, type='SELECTION')
        else:
            # 删除之前的合成字符串
            if self.length != 0:
                if DEBUG:
                    printx(CCFA, "删除之前的合成字符串")

                # 移动光标到最后的位置
                if self.move_times != 0:
                    for _ in range(self.move_times):
                        self.op_move(*args, type='NEXT_CHARACTER')
                # 往前选择字符
                for _ in range(self.length):
                    self.op_select(*args, type='PREVIOUS_CHARACTER')
                # 删除选择
                self.op_delete(*args, type='SELECTION')

                self.length = 0
                self.move_times = 0

            if event == 'INPUT':
                # 插入结果字符串
                if data.result_str is not None:
                    if DEBUG:
                        printx(CCFA, "插入结果字符串: [%s]" % data.result_str, len(data.result_str))

                    self.op_insert('INVOKE_DEFAULT', True, text=data.result_str)

                    self.length = 0
                    self.move_times = 0

                # 插入合成字符串
                if data.composite_str is not None:
                    if DEBUG:
                        printx(CCFA, "插入合成字符串: [%s]" % data.composite_str, len(data.composite_str))

                    self.op_insert(*args, text=f'[{data.composite_str}]')

                    self.length = data.composite_len_c + 2

                    # 设置光标位置
                    self.move_times = data.composite_len_c - data.composite_cur_i + 1
                    for _ in range(self.move_times):
                        self.op_move(*args, type='PREVIOUS_CHARACTER')
        pass

    def process_text_editor(self, context: Context, ime_event: tuple[CompositionEventType, IMEData, int]):
        event, data, _ = ime_event
        args = self.op_args
        space = cast(SpaceTextEditor, context.space_data)
        text = space.text
        use_overwrite = space.use_overwrite  # 插入模式

        space.use_overwrite = False

        if event == 'START':
            if (text.select_end_line_index != text.current_line_index or
                text.select_end_character != text.current_character):
                if DEBUG:
                    printx(CCFR, "删除选择")
                self.op_insert(*args, text=' ')
                self.op_delete(*args, type='PREVIOUS_CHARACTER')

            self.length = 0
            self.move_times = 0
            self.stac_i = text.current_character
            self.endc_i = self.stac_i
            self.clause_stac_i = -1
            self.clause_endc_i = -1

        else:

            # 删除之前的合成字符串
            if self.length != 0:
                if DEBUG:
                    printx(CCFA, "删除之前的合成字符串")

                # 移动光标到最后的位置
                if self.move_times != 0:
                    for _ in range(self.move_times):
                        self.op_move(*args, type='NEXT_CHARACTER')
                # 往前选择字符
                for _ in range(self.length):
                    self.op_select(*args, type='PREVIOUS_CHARACTER')
                # 删除选择
                self.op_insert(*args, text=' ')
                self.op_delete(*args, type='PREVIOUS_CHARACTER')

                self.length = 0
                self.move_times = 0
                self.endc_i = self.stac_i
                self.clause_stac_i = -1
                self.clause_endc_i = -1

            if event == 'INPUT':
                # 插入结果字符串
                if data.result_str is not None:
                    if DEBUG:
                        printx(CCFA, "插入结果字符串: [%s]" % data.result_str, len(data.result_str))

                    if use_overwrite:
                        space.use_overwrite = True

                    self.op_insert('INVOKE_DEFAULT', True, text=data.result_str)

                    space.use_overwrite = False

                    self.length = 0
                    self.move_times = 0
                    self.stac_i = text.current_character
                    self.endc_i = self.stac_i
                    self.clause_stac_i = -1
                    self.clause_endc_i = -1

                # 插入合成字符串
                if data.composite_str is not None:
                    if DEBUG:
                        printx(CCFA, "插入合成字符串: [%s]" % data.composite_str, len(data.composite_str))

                    self.op_insert(*args, text=data.composite_str)

                    self.length = data.composite_len_c
                    self.endc_i = text.current_character

                    if data.composite_sta_i == -1:
                        self.clause_stac_i = -1
                        self.clause_endc_i = -1

                    elif data.composite_sta_i != data.composite_end_i:
                        self.clause_stac_i = self.stac_i + data.composite_sta_i
                        self.clause_endc_i = self.stac_i + data.composite_end_i

                    # 设置光标位置
                    self.move_times = data.composite_len_c - data.composite_cur_i
                    for _ in range(self.move_times):
                        self.op_move(*args, type='PREVIOUS_CHARACTER')

        space.use_overwrite = use_overwrite

        pass

    def process_console(self, context: Context, ime_event: tuple[CompositionEventType, IMEData, int]):
        manager = self.manager
        event, data, _ = ime_event
        args = self.op_args
        space = cast(SpaceConsole, context.space_data)
        text = cast(ConsoleLine, space.history[len(space.history) - 1])

        if event == 'START':
            space.select_start
            if (space.select_start != space.select_end):
                if DEBUG:
                    printx(CCFR, "删除选择")
                self.op_insert(*args, text=' ')
                self.op_delete(*args, type='PREVIOUS_CHARACTER')

            self.length = 0
            self.move_times = 0
            self.stac_i = manager.get_console_cursor_i(text)
            self.endc_i = self.stac_i
            self.clause_stac_i = -1
            self.clause_endc_i = -1

        else:

            # 删除之前的合成字符串
            if self.length != 0:
                if DEBUG:
                    printx(CCFA, "删除之前的合成字符串")

                # 移动光标到最后的位置
                if self.move_times != 0:
                    for _ in range(self.move_times):
                        self.op_move(*args, type='NEXT_CHARACTER')
                # 逐个字符删除
                for _ in range(self.length):
                    self.op_delete(*args, type='PREVIOUS_CHARACTER')

                self.length = 0
                self.move_times = 0
                self.endc_i = self.stac_i
                self.clause_stac_i = -1
                self.clause_endc_i = -1

            if event == 'INPUT':

                # 插入结果字符串

                if data.result_str is not None:
                    if DEBUG:
                        printx(CCFA, "插入结果字符串: [%s]" % data.result_str, len(data.result_str))

                    self.op_insert('INVOKE_DEFAULT', True, text=data.result_str)

                    self.length = 0
                    self.move_times = 0
                    self.stac_i = manager.get_console_cursor_i(text)
                    self.endc_i = self.stac_i
                    self.clause_stac_i = -1
                    self.clause_endc_i = -1

                # 插入合成字符串

                if data.composite_str is not None:
                    if DEBUG:
                        printx(CCFA, "插入合成字符串: [%s]" % data.composite_str, len(data.composite_str))

                    self.op_insert(*args, text=data.composite_str)

                    self.length = data.composite_len_c
                    self.endc_i = manager.get_console_cursor_i(text)

                    if data.composite_sta_i == -1:
                        self.clause_stac_i = -1
                        self.clause_endc_i = -1

                    elif data.composite_sta_i != data.composite_end_i:
                        self.clause_stac_i = self.stac_i + data.composite_sta_i
                        self.clause_endc_i = self.stac_i + data.composite_end_i

                    # 设置光标位置
                    self.move_times = data.composite_len_c - data.composite_cur_i
                    for _ in range(self.move_times):
                        self.op_move(*args, type='PREVIOUS_CHARACTER')
        pass

    # -----

    def draw_comp_underline_text_editor(self, context: Context):
        if context.space_data.text != self.space.text:
            return

        # 1. 更新候选窗口位置
        # 2. 绘制下划线
        manager = self.manager

        if context.space_data == self.space:
            manager.ime_window_pos_update_text_editor(context, self)

        if bpy.app.version >= (4, 0, 0):
            shader = cast(gpu.types.GPUShader, gpu.shader.from_builtin('UNIFORM_COLOR'))
        else:
            shader = cast(gpu.types.GPUShader, gpu.shader.from_builtin('2D_UNIFORM_COLOR'))
        hold_blend = gpu.state.blend_get()
        hold_line_width = gpu.state.line_width_get()

        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(1)
        gpu.state.point_size_set(1)

        # -----

        region = context.region
        space = cast(SpaceTextEditor, context.space_data)
        text = space.text

        lheight, draw_rect_xmin, draw_rect_xmax = manager.get_text_editor_draw_params(context)

        pixelsize: float = context.preferences.system.pixel_size

        color = [*context.preferences.themes[0].text_editor.space.text, 1.0]

        # 绘制光标
        if DEBUG:
            x, y = manager.text_editor_region_location_from_cursor(
                context, region, space, text.current_line_index, text.current_character)
            w, h = 2 * pixelsize, lheight
            cur_l = x - pixelsize
            cur_b = y
            cur_r = x + w - pixelsize
            cur_t = y + h
            self.draw_rect(cur_l, cur_b, cur_r, cur_t, shader, (1, 1, 0, 1))

        # 绘制下划线

        draw_underline = False
        draw_clause_underline = False
        uheight = 0
        clause_uheight = 0

        if self.stac_i != -1 and self.endc_i != self.stac_i:
            draw_underline = True
            if self.clause_stac_i != -1 and self.clause_endc_i != self.clause_stac_i:
                uheight = pixelsize
                clause_uheight = pixelsize
                draw_clause_underline = True
            else:
                uheight = 2 * pixelsize

        # 绘制合成字符串的下划线

        if draw_underline:
            sta_l, sta_b = manager.text_editor_region_location_from_cursor(context, region, space, text.current_line_index, self.stac_i)
            end_l, end_b = manager.text_editor_region_location_from_cursor(context, region, space, text.current_line_index, self.endc_i)
            if end_b == sta_b:
                self.draw_rect(sta_l, sta_b, end_l, sta_b + uheight, shader, color)
            else:
                self.draw_rect(sta_l, sta_b, draw_rect_xmax, sta_b + uheight, shader, color)
                self.draw_rect(draw_rect_xmin, end_b, end_l, end_b + uheight, shader, color)
                y = end_b + lheight
                while y < sta_b:
                    self.draw_rect(draw_rect_xmin, y, draw_rect_xmax, y + uheight, shader, color)
                    y += lheight

        # 绘制选择字符串的下划线

        if draw_clause_underline:
            sta_l, sta_b = manager.text_editor_region_location_from_cursor(context, region, space, text.current_line_index, self.clause_stac_i)
            end_l, end_b = manager.text_editor_region_location_from_cursor(context, region, space, text.current_line_index, self.clause_endc_i)
            sta_b += uheight  # 抬升位置，避免覆盖“合成字符串的下划线”
            end_b += uheight
            if end_b == sta_b:
                self.draw_rect(sta_l, sta_b, end_l, sta_b + clause_uheight, shader, color)
            else:
                self.draw_rect(sta_l, sta_b, draw_rect_xmax, sta_b + clause_uheight, shader, color)
                self.draw_rect(draw_rect_xmin, end_b, end_l, end_b + clause_uheight, shader, color)
                y = end_b + lheight
                while y < sta_b:
                    self.draw_rect(draw_rect_xmin, y, draw_rect_xmax, y + clause_uheight, shader, color)
                    y += lheight

        # -----

        gpu.state.blend_set(hold_blend)
        gpu.state.line_width_set(hold_line_width)
        pass

    def draw_comp_underline_console(self, context: Context):
        if context.space_data != self.space:
            return

        # 1. 更新候选窗口位置
        # 2. 绘制下划线
        manager = self.manager

        manager.ime_window_pos_update_console(context, self)

        if bpy.app.version >= (4, 0, 0):
            shader = cast(gpu.types.GPUShader, gpu.shader.from_builtin('UNIFORM_COLOR'))
        else:
            shader = cast(gpu.types.GPUShader, gpu.shader.from_builtin('2D_UNIFORM_COLOR'))
        hold_blend = gpu.state.blend_get()
        hold_line_width = gpu.state.line_width_get()

        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(1)
        gpu.state.point_size_set(1)

        # -----

        region = context.region
        space = cast(SpaceConsole, context.space_data)
        text = cast(ConsoleLine, space.history[len(space.history) - 1])

        lheight, draw_xmin, draw_xmax, _, _ = manager.get_console_draw_params(context)

        pixelsize: float = context.preferences.system.pixel_size

        color = [*context.preferences.themes[0].text_editor.space.text, 1.0]

        # 绘制光标

        if DEBUG:
            x, y = manager.console_region_location_from_cursor(
                context, region, space, manager.get_console_cursor_i(text))
            w, h = 2 * pixelsize, lheight
            cur_l = x - pixelsize
            cur_b = y
            cur_r = x + w - pixelsize
            cur_t = y + h
            self.draw_rect(cur_l, cur_b, cur_r, cur_t, shader, (1, 1, 0, 1))

        # 绘制下划线

        draw_underline = False
        draw_clause_underline = False
        uheight = 0
        clause_uheight = 0

        if self.stac_i != -1 and self.endc_i != self.stac_i:
            draw_underline = True
            if self.clause_stac_i != -1 and self.clause_endc_i != self.clause_stac_i:
                uheight = pixelsize
                clause_uheight = pixelsize
                draw_clause_underline = True
            else:
                uheight = 2 * pixelsize

        # 绘制合成字符串的下划线

        if draw_underline:
            sta_l, sta_b = manager.console_region_location_from_cursor(
                context, region, space, self.stac_i)
            end_l, end_b = manager.console_region_location_from_cursor(
                context, region, space, self.endc_i)
            if end_b == sta_b:
                self.draw_rect(sta_l, sta_b, end_l, sta_b + uheight, shader, color)
            else:
                self.draw_rect(sta_l, sta_b, draw_xmax, sta_b + uheight, shader, color)
                self.draw_rect(draw_xmin, end_b, end_l, end_b + uheight, shader, color)
                y = end_b + lheight
                while y < sta_b:
                    self.draw_rect(draw_xmin, y, draw_xmax, y + uheight, shader, color)
                    y += lheight

        # 绘制待转字符串的下划线

        if draw_clause_underline:
            sta_l, sta_b = manager.console_region_location_from_cursor(
                context, region, space, self.clause_stac_i)
            end_l, end_b = manager.console_region_location_from_cursor(
                context, region, space, self.clause_endc_i)
            sta_b += uheight  # 抬升位置，避免覆盖“合成字符串的下划线”
            end_b += uheight
            if end_b == sta_b:
                self.draw_rect(sta_l, sta_b, end_l, sta_b + clause_uheight, shader, color)
            else:
                self.draw_rect(sta_l, sta_b, draw_xmax, sta_b + clause_uheight, shader, color)
                self.draw_rect(draw_xmin, end_b, end_l, end_b + clause_uheight, shader, color)
                y = end_b + lheight
                while y < sta_b:
                    self.draw_rect(draw_xmin, y, draw_xmax, y + clause_uheight, shader, color)
                    y += lheight

        # -----

        gpu.state.blend_set(hold_blend)
        gpu.state.line_width_set(hold_line_width)
        pass

    # -----

    def draw_rect(self, l: int, b: int, r: int, t: int, shader: gpu.types.GPUShader, color: Color):
        batch = batch_for_shader(shader, 'TRIS', {'pos': [
            (l, t), (r, t), (l, b),
            (r, t), (l, b), (r, b),
        ]})
        shader.bind()
        shader.uniform_float('color', color)
        batch.draw(shader)
        pass
