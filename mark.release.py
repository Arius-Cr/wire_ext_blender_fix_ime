__all__ = ['mark']

# 似乎在 Python 2.9 中，不同模块导入的相同模块都是不同的模块实例，
# 可以通过 id() 看到地址的不同，而 Python 2.10 中，是相同的模块实例，
# 所以在 2.9 中 mark.py 中的数值型变量无法在多个模块中流通，
# 只能将这些变量包在一个引用型对象里面。

class _Mark():
    def __init__(self) -> None:

        # 生成类型是否为 Debug，否则为 Release
        self.DEBUG_BUILD: bool = False

        # 是否启用调试，启用后会在控制台输出调试信息
        self.DEBUG: bool = None


mark = _Mark()
