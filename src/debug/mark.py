__all__ = ['mark']

try:  # mark_locale.py 不受版本管理，该文件在本地目录自由改动
    from . import mark_locale
except:
    mark_locale = None

class _Mark():
    def __init__(self) -> None:

        # 生成类型是否为 Debug，否则为 Release
        self.DEBUG_BUILD: bool = False

        # 是否启用调试，启用后会在控制台输出调试信息
        self.DEBUG: bool = False

        # 状态更新器 状态更新时 相关的调试信息
        self.DEBUG_UPDATER_1: bool = False

        # 状态更新器 步进计时器 相关的调试信息
        self.DEBUG_UPDATER_2: bool = False

        # 状态更新器 状态更新前 相关的调试信息
        self.DEBUG_UPDATER_3: bool = False

        # 更新候选窗口位置时 相关的调试信息
        self.DEBUG_CANDIDATE_POS: bool = False

        # 输出当前模态处理器的 user_data 数据的大小
        self.DEBUG_GET_MODAL_HANDLER_SIZE: bool = False

        # -----

        self.mark_locale = mark_locale
        self.mark_names: list[str] = []

        for _name in self.__dict__.keys():
            if _name.startswith("DEBUG"):
                self.mark_names.append(_name)
                
                if mark_locale and hasattr(mark_locale, _name):
                    _value = getattr(mark_locale, _name)
                    setattr(self, _name, _value)


mark = _Mark()
