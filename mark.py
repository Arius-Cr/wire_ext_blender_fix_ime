__all__ = ['mark']

try:  # mark_debug.py 不受版本管理，在本地目录自由改动
    from . import mark_debug
except:
    mark_debug = None

class _Mark():
    def __init__(self) -> None:

        # 是否启用调试，启用后会在控制台输出调试信息
        self.DEBUG: bool = False

        # 生成类型是否为 Debug，否则为 Release
        self.DEBUG_BUILD: bool = False

        # 状态更新器 状态更新时 相关的调试信息
        self.DEBUG_UPDATER_1: bool = False

        # 状态更新器 步进计时器 相关的调试信息
        self.DEBUG_UPDATER_2: bool = False

        # 更新候选窗口位置时 相关的调试信息
        self.DEBUG_CANDIDATE_POS: bool = False

        # 标题栏状态图标重绘 相关的调试信息
        self.DEBUG_HEADER_REDRAW: bool = False

        # -----

        self.mark_debug = mark_debug
        self.mark_debug_names: list[str] = []

        if mark_debug:
            mark_debug_keys = dir(mark_debug)
            for _name in dir(self):
                if _name.startswith("__"):
                    continue
                if _name in mark_debug_keys:
                    _value = getattr(mark_debug, _name)
                    setattr(self, _name, _value)
                    self.mark_debug_names.append(_name)


mark = _Mark()
