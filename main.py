from typing import cast, Literal, Union
from types import SimpleNamespace

import bpy

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
    use_fix_ime_state = self.use_fix_ime_state
    use_fix_ime_input = self.use_fix_ime_input

    if use_fix_ime_state:
        native.use_fix_ime_state(True)
        native.use_fix_ime_input(use_fix_ime_input,
            WIRE_OT_fix_ime_input_watcher.event_dispatch)
        if use_fix_ime_input:
            fix_ime_input_enable()
        else:
            fix_ime_input_disable()
    else:
        native.use_fix_ime_state(False)
        native.use_fix_ime_input(False)  # 必须关闭
        fix_ime_input_disable()

def use_header_extend(self: Union['WIRE_FIX_Preferences', SimpleNamespace], context: bpy.types.Context):
    global TEXT_HT_header_extend_appended
    global CONSOLE_HT_header_extend_appended

    use_header_extend_text_editor = self.use_header_extend_text_editor
    use_header_extend_console = self.use_header_extend_console

    if use_header_extend_text_editor:
        if not TEXT_HT_header_extend_appended:
            bpy.types.TEXT_HT_header.append(TEXT_HT_header_extend)
            TEXT_HT_header_extend_appended = True
    else:
        if TEXT_HT_header_extend_appended:
            bpy.types.TEXT_HT_header.remove(TEXT_HT_header_extend)
            TEXT_HT_header_extend_appended = False

    if use_header_extend_console:
        if not CONSOLE_HT_header_extend_appended:
            bpy.types.CONSOLE_HT_header.append(CONSOLE_HT_header_extend)
            CONSOLE_HT_header_extend_appended = True
    else:
        if CONSOLE_HT_header_extend_appended:
            bpy.types.CONSOLE_HT_header.remove(CONSOLE_HT_header_extend)
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
    )

    use_fix_ime_input_text_editor: bpy.props.BoolProperty(
        name="文本编辑器",
        description="启用后，可以在【文本编辑器】中直接使用输入法输入文字",
        default=True,
    )

    use_fix_ime_input_console: bpy.props.BoolProperty(
        name="控制台",
        description="启用后，可以在【控制台】中直接使用输入法输入文字",
        default=True,
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
    _fix_ime_input_enabled = True
    pass

def fix_ime_input_disable():
    global _fix_ime_input_enabled
    if not _fix_ime_input_enabled:
        return
    _fix_ime_input_enabled = False

    # 当通过选项关闭相关功能，如果鼠标不移入相关窗口，则检查器是不会主动结束的，
    # 但我们无法主动结束鼠标位置检查器，所以只能设置标记，避免检查器继续运行，
    # 然后当用户将鼠标移入窗口时，已标记的检查器会立即结束不会继续运行。
    # 如果移入窗口前停用了插件，则模态操作会被 Blender 强制结束，
    # 此时会调用 __del__ 函数，但此时已经没有任何需要清理的。
    for _watcher in watchers.values():
        _watcher._valid = False
    watchers.clear()
    pass


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


use_temp_override: bool = False

watchers: dict[bpy.types.Window, 'WIRE_OT_fix_ime_input_watcher'] = {}

EditorType = Literal['font', 'text', 'console']
CompositionEventMaps = {0: 'START', 1: 'UPDATE', 2: 'FINISH', 3: 'CANCEL'}
CompositionEventType = Literal['START', "UPDATE", 'FINISH', 'CANCEL']

class WIRE_OT_fix_ime_input_watcher(bpy.types.Operator):
    bl_idname = 'wire.fix_ime_input_watcher'
    bl_label = "鼠标位置检查器"
    bl_description = "根据鼠标当前位置，在区块中启用或停用输入法"
    bl_options = set()

    @classmethod
    def poll(clss, context: bpy.types.Context) -> bool:
        if not native.dll:
            return False

        prefs = get_prefs(context)
        if not (prefs.use_fix_ime_state and
                prefs.use_fix_ime_input and (
            prefs.use_fix_ime_input_font_edit or
            prefs.use_fix_ime_input_text_editor or
            prefs.use_fix_ime_input_console)):
            return False

        # 每个窗口只需运行一个检查器
        if context.window not in watchers:
            return True
        return False

    def __init__(self) -> None:
        super().__init__()

        # 当通过选项停用相关功能时，会将该属性设为 False
        self._valid = True

        # 当前输入法是否已经启动
        self._enabled = False

        self._window: bpy.types.Window = None
        self._editor_type: EditorType = None
        self._area = None
        self._region = None
        self._space = None
        self._insert = None  # bpy.ops.xxx.insert 操作
        self._delete = None  # bpy.ops.xxx.delete 操作
        self._move = None  # bpy.ops.xxx.move 操作
        self._select = None  # bpy.ops.xxx.select 操作

        # 是否处于文字合成状态，在 START 时开启，在 FINISH 或 CANCEL 时关闭
        self._inputing: bool = False
        # 文字合成消息
        # 在一些情况下，输入法会连续发送多个合成消息，这里就会有多个消息。
        # 譬如确认合成时，UPDATE 和 FINISH 和接续出现，
        # 微软拼音输入法在中文模式下按数字键会连续产生 START、UPDATE、FINISH 三个消息。
        # tuple[合成事件类型, 合成文本, 合成文本中光标的位置]
        self._events: list[tuple[CompositionEventType, str, int]] = []
        # 是否已经启动文字合成消息处理器（bpy.app.timers.register ...）
        self._event_processor_timer_registered: bool = False
        # 上次合成文本的长度
        self._length: int = 0
        # 上次合成文本中光标相对末尾的字符数
        self._move_times: int = 0

    def execute(self, context: bpy.types.Context):
        self.report({'ERROR'}, "必须以 INVOKE 的方式调用")
        return {'CANCELLED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        window = context.window

        watchers[window] = self
        self._window = window

        if DEBUG:
            printx(CFHIT1, "鼠标位置检查器启动 (现有: %d)：%X (wm)" % (
                len(watchers), window.as_pointer()))

        # 将窗口指针和窗口句柄绑定
        native.window_associate_pointer(window.as_pointer())

        self.update_ime_state(context, event)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        # 如果用户激活了输入控件，则所有输入消息都会发送到输入控件，此时不会收到任何消息，
        # 因此不用担心和输入控件中输入法状态的冲突。

        # 已失效的检查器自行结束即可
        if not self._valid:
            if DEBUG:
                printx(CFWARN, "鼠标位置检查器结束")
            return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

        window = context.window

        prefs = get_prefs(context)
        if not (prefs.use_fix_ime_state and
                prefs.use_fix_ime_input and (
            prefs.use_fix_ime_input_font_edit or
            prefs.use_fix_ime_input_text_editor or
            prefs.use_fix_ime_input_console)):
            if window in watchers:
                watchers.pop(window)
            if DEBUG:
                printx(CFWARN, "鼠标位置检查器停用 (剩余: %d)：%X (wm)" % (
                    len(watchers), window.as_pointer()))
            return {'CANCELLED', 'PASS_THROUGH', 'INTERFACE'}

        if not self._inputing:
            if native.window_is_active(window.as_pointer()):
                self.update_ime_state(context, event)

        # 输入时屏蔽所有按键
        else:
            return {'RUNNING_MODAL'}

        return {'RUNNING_MODAL', 'PASS_THROUGH', 'INTERFACE'}

    def cancel(self, context: bpy.types.Context):
        # 窗口关闭的时候 Blender 也会触发 cancel 函数
        window = context.window
        if window in watchers:
            watchers.pop(window)
        if DEBUG:
            printx(CFWARN, "鼠标位置检查器取消 (剩余：%d)：%X (wm)" % (
                len(watchers), window.as_pointer()))
        pass

    def __del__(self):
        # 实例和类型的销毁都会调用该函数（例如停用插件卸载类型时）
        if hasattr(self, 'base'):
            return
        # 目前无需在此处执行任何操作
        pass

    def update_ime_state(self, context: bpy.types.Context, event: bpy.types.Event):
        # 鼠标进入符合条件的区块则启用输入法，否则停用输入法

        prefs = get_prefs(context)
        key = event.type
        value = event.value
        mouse_x = event.mouse_x
        mouse_y = event.mouse_y

        if key == 'WINDOW_DEACTIVATE':
            native.ime_input_disable(context.window.as_pointer())
            self._enabled = False
            self._editor_type = None
            self._area = None
            self._region = None
            self._space = None
            self._insert = None
            self._delete = None
            self._move = None
            self._delete = None

        # 仅在鼠标发生了移动时才检查，否则可能会误判
        # 虽然只是监听 MOUSEMOVE，但实际在鼠标不移动的时候也会触发，譬如按 TAB 切换编辑模式时。
        elif key == 'MOUSEMOVE':

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
                if not self._enabled or space != self._space:
                    if DEBUG:
                        printx(CBHIT2, "在区块中启用输入法：%s" % space.type)
                    native.ime_input_enable(context.window.as_pointer())
                    self._enabled = True
                    self._editor_type = editor_type
                    self._area = area
                    self._region = region
                    self._space = space
                    self._insert = None  # 延迟到 event_process 中再初始化
                    self._delete = None
                    self._move = None
                    self._delete = None
                    if DEBUG:
                        printx(CFHIT2, "启动后更新光标位置")
                    update_candidate_window_pos(self)
            else:
                if self._enabled:
                    if DEBUG:
                        printx(CBHIT3, "在区块中停用输入法")
                    native.ime_input_disable(context.window.as_pointer())  # 此处会间接使得【输入法冲突】被“二次”修复
                    self._enabled = False
                    self._editor_type = None
                    self._area = None
                    self._region = None
                    self._space = None
                    self._insert = None
                    self._delete = None
                    self._move = None
                    self._delete = None

        # 在大部分按键事件中均会重新获取光标位置，以便下次输入的时候，候选框能够在准确的位置显示，不会闪一下
        elif self._enabled and ((key not in [
            '',  # 未知按键类型
            'LEFT_CTRL', 'LEFT_SHIFT', 'LEFT_ALT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT',
            'F16', 'F17', 'F18', 'F19',  # TODO ：原则上需要加入更多不需要的按键，目前先这样
        ] and value == 'RELEASE') and (key not in ['INBETWEEN_MOUSEMOVE'])):
            if DEBUG:
                printx(CFHIT2, "按键后更新光标位置：'%s'" % key)
            update_candidate_window_pos(self)

    @staticmethod
    def event_dispatch(wm_pointer: int, event: int, text: str, pos: int) -> None:
        if DEBUG:
            printx("派送消息(wm: %x)：" % wm_pointer, event, text, pos)
        watcher: WIRE_OT_fix_ime_input_watcher = None
        for k, v in watchers.items():
            if k.as_pointer() == wm_pointer:
                watcher = v
                break
        if watcher:
            # 从 Windows 传来的是 UTF-16 字符串，需要编码为 UTF-8
            watcher.event_push(CompositionEventMaps[event],
                text.encode('utf-8').decode('utf-8'), pos)

    def event_push(self, event: CompositionEventType, text: str, pos: int):
        if DEBUG:
            printx("压入消息(wm: %x)：" % self._window.as_pointer(), event, text, pos)
        self._events.append((event, text, pos))
        if not self._event_processor_timer_registered:
            self._event_processor_timer_registered = True
            # 不能直接调用，大概是因为 Blender 处理消息是有阶段的，
            # 不在特定阶段，就无法使用界面相关的功能？
            # 而这个定时器不管时间设为什么，似乎都只会在能处理界面的阶段才触发。

            def _func():
                return self.event_process()
            bpy.app.timers.register(_func, first_interval=0.000001)
        pass

    def event_process(self) -> Union[float, None]:
        self._event_processor_timer_registered = False

        if DEBUG:
            printx(CCFY, "处理输入事件...(总数：%d)" % len(self._events))

        if self._insert is None:
            if self._editor_type == 'font':
                self._insert = bpy.ops.font.text_insert
                self._delete = bpy.ops.font.delete
                self._move = bpy.ops.font.move
                self._select = bpy.ops.font.move_select
            if self._editor_type == 'text':
                self._insert = bpy.ops.text.insert
                self._delete = bpy.ops.text.delete
                self._move = bpy.ops.text.move
                self._select = None,  # 虽然有该操作，但 selection 无法用于 delete，等于没用
            elif self._editor_type == 'console':
                self._insert = bpy.ops.console.insert
                self._delete = bpy.ops.console.delete
                self._move = bpy.ops.console.move
                self._select = None,  # 没有该操作

        ctx = bpy.context.copy()
        ctx['window'] = self._window
        ctx['area'] = self._area
        ctx['region'] = self._region
        ctx['space_data'] = self._space
        if self._editor_type == 'text':
            ctx['edit_text'] = self._space.text

        # 更新合成文本
        if use_temp_override:
            self.event_process_core_temp_override(ctx)
        else:
            # 3.0.0 ~ 3.1.0 不支持 temp_override() ，只能使用旧方法
            self.event_process_core_context_override(ctx)

        # 更新光标位置
        if DEBUG:
            printx(CFHIT2, "输入后更新光标位置")
        update_candidate_window_pos(self)

        return None

    def event_process_core_temp_override(self, ctx: bpy.types.Context):
        with bpy.context.temp_override(**ctx):
            while len(self._events) > 0:
                event, text, pos = self._events.pop(0)

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
                    self._inputing = True
                elif finish or cancel:
                    self._inputing = False

                # 删除旧的文本
                if update or finish or cancel:

                    if self._move_times != 0:  # 移动光标到最后的位置
                        for _ in range(self._move_times):
                            self._move('EXEC_REGION_WIN', type='NEXT_CHARACTER')

                    if self._editor_type == 'font':
                        # 该方法速度更快，但是不能用于文本编辑器和控制台
                        for _ in range(self._length):
                            self._select('EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')
                        self._delete('EXEC_REGION_WIN', type='SELECTION')
                    else:
                        for _ in range(self._length):
                            self._delete('EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')

                # 插入新的文本
                if start or update:
                    self._length = len(text) + 2  # 加上中括号两个字符
                    self._move_times = self._length - pos - 1  # -1 = -2 + 1，-2 是减去之前多加的 2，+1 是右侧的中括号
                    self._insert('EXEC_REGION_WIN', text='[' + text + ']')
                    for _ in range(self._move_times):
                        self._move('EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')
                elif finish:
                    self._insert('EXEC_REGION_WIN', text=text)

                if DEBUG:
                    if start or update or finish:
                        printx("当前文本 (长度：%d，光标：%d):" % (self._length - 2, pos), CCBY + text + CCZ0)
        pass

    def event_process_core_context_override(self, ctx: bpy.types.Context):
        while len(self._events) > 0:
            event, text, pos = self._events.pop(0)

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
                self._inputing = True
            elif finish or cancel:
                self._inputing = False

            # 删除旧的文本
            if update or finish or cancel:

                if self._move_times != 0:  # 移动光标到最后的位置
                    for _ in range(self._move_times):
                        self._move(ctx, 'EXEC_REGION_WIN', type='NEXT_CHARACTER')

                if self._editor_type == 'font':
                    # 该方法速度更快，但是不能用于文本编辑器和控制台
                    for _ in range(self._length):
                        self._select(ctx, 'EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')
                    self._delete(ctx, 'EXEC_REGION_WIN', type='SELECTION')
                else:
                    for _ in range(self._length):
                        self._delete(ctx, 'EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')

            # 插入新的文本
            if start or update:
                self._length = len(text) + 2  # 加上中括号两个字符
                self._move_times = self._length - pos - 1  # -1 = -2 + 1，-2 是减去之前多加的 2，+1 是右侧的中括号
                self._insert(ctx, 'EXEC_REGION_WIN', text='[' + text + ']')
                for _ in range(self._move_times):
                    self._move(ctx, 'EXEC_REGION_WIN', type='PREVIOUS_CHARACTER')
            elif finish:
                self._insert(ctx, 'EXEC_REGION_WIN', text=text)

            if DEBUG:
                if start or update or finish:
                    printx("当前文本 (长度：%d，光标：%d):" % (self._length - 2, pos), CCBY + text + CCZ0)
        pass

    @classmethod
    def add_key_map_item(clss):
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        km.keymap_items.new(clss.bl_idname, type='MOUSEMOVE', value='ANY')

    @classmethod
    def remove_key_map_item(clss):
        km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            'Screen Editing', space_type='EMPTY', region_type='WINDOW')
        for _kmi in reversed(km.keymap_items):
            if _kmi.idname == clss.bl_idname:
                km.keymap_items.remove(_kmi)


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


show_caret = True if DEBUG_BUILD else False

def update_candidate_window_pos(watcher: 'WIRE_OT_fix_ime_input_watcher'):
        ctx = SimpleNamespace()
        ctx.window = watcher._window
        ctx.area = watcher._area
        ctx.region = watcher._region
        ctx.space_data = watcher._space
        ctx.preferences = bpy.context.preferences
        if watcher._space.type == 'VIEW_3D':
            update_candidate_window_pos_font_edit(ctx)
        elif watcher._space.type == 'TEXT_EDITOR':
            update_candidate_window_pos_text_editor(ctx)
        elif watcher._space.type == 'CONSOLE':
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

def TEXT_HT_header_extend(self: bpy.types.Header, context: bpy.types.Context):
    layout = self.layout

    window = context.window

    prefs = get_prefs(context)

    active = (prefs.use_fix_ime_state and prefs.use_fix_ime_input)

    row = layout.row()
    row.active = active

    icon = 'PROP_OFF'
    if active and prefs.use_fix_ime_input_text_editor:
        watcher: WIRE_OT_fix_ime_input_watcher = None
        if window in watchers:
            watcher = watchers[window]
        if watcher and watcher._space == context.space_data:
            icon = 'PROP_ON'
        else:
            icon = 'PROP_CON'

    row.prop(prefs, 'use_fix_ime_input_text_editor', text="", icon=icon, emboss=False,
        invert_checkbox=True if prefs.use_fix_ime_input_text_editor else False)

def CONSOLE_HT_header_extend(self: bpy.types.Header, context: bpy.types.Context):
    layout = self.layout

    window = context.window

    prefs = get_prefs(context)

    active = (prefs.use_fix_ime_state and prefs.use_fix_ime_input)

    layout.separator_spacer()

    row = layout.row()
    row.active = active

    icon = 'PROP_OFF'
    if active and prefs.use_fix_ime_input_console:
        watcher: WIRE_OT_fix_ime_input_watcher = None
        if window in watchers:
            watcher = watchers[window]
        if watcher and watcher._space == context.space_data:
            icon = 'PROP_ON'
        else:
            icon = 'PROP_CON'

    row.prop(prefs, 'use_fix_ime_input_console', text="", icon=icon, emboss=False,
        invert_checkbox=True if prefs.use_fix_ime_input_console else False)


# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰


def register():
    if not native.dll_load():
        return

    native.init()

    native.use_hook(True)

    global use_temp_override

    m, s, _ = bpy.app.version
    if m >= 3 and s >= 2:
        use_temp_override = True

    bpy.utils.register_class(WIRE_FIX_Preferences)

    bpy.utils.register_class(WIRE_OT_fix_ime_input_watcher)

    WIRE_OT_fix_ime_input_watcher.add_key_map_item()

    prefs = get_prefs(bpy.context)

    use_debug_update(prefs, bpy.context)

    use_fix_ime_update(prefs, bpy.context)

    use_header_extend(prefs, bpy.context)

    if DEBUG_BUILD:
        test_register()

    pass

def unregister():
    if not native.dll_loaded:
        return

    if DEBUG_BUILD:
        test_unregister()

    use_header_extend(SimpleNamespace(
        use_header_extend_text_editor=False,
        use_header_extend_console=False,
    ), bpy.context)

    use_fix_ime_update(SimpleNamespace(
        use_fix_ime_state=False,
        use_fix_ime_input=False,
    ), bpy.context)

    WIRE_OT_fix_ime_input_watcher.remove_key_map_item()

    bpy.utils.unregister_class(WIRE_OT_fix_ime_input_watcher)

    bpy.utils.unregister_class(WIRE_FIX_Preferences)

    native.use_hook(False)

    native.dll_unload()
    pass
