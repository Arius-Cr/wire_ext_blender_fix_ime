__all__ = ['mark']

try:  # mark_debug.py 不受版本管理，在本地目录自由改动
    from . import mark_debug
except:
    mark_debug = None

# 似乎在 Python 2.9 中，不同模块导入的相同模块都是不同的模块实例，
# 可以通过 id() 看到地址的不同，而 Python 2.10 中，是相同的模块实例，
# 所以在 2.9 中 mark.py 中的数值型变量无法在多个模块中流通，
# 只能将这些变量包在一个引用型对象里面。

class _Mark():
    def __init__(self) -> None:

        # 是否启用调试，启用后会在控制台输出调试信息
        self.DEBUG: bool = False

        # 生成类型是否为 Debug，否则为 Release
        self.DEBUG_BUILD: bool = False

        self.DEBUG_UPDATER_1: bool = False
        self.DEBUG_UPDATER_2: bool = False

        if mark_debug:
            print("加载调试信息：")
            mark_debug_keys = dir(mark_debug)
            for _name in dir(self):
                if _name.startswith("__"):
                    continue
                if _name in mark_debug_keys:
                    _value = getattr(mark_debug, _name)
                    setattr(self, _name, _value)
                    print("%s: %s" % (_name, _value))


mark = _Mark()
