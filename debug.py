from typing import cast, Literal, Union, Protocol

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
from typing import Any

all = [
    'print',

    'CC',
    'CCZ0',

    'CCFR',
    'CCFG',
    'CCFY',
    'CCFB',
    'CCFP',
    'CCFA',

    'CCBR',
    'CCBG',
    'CCBY',
    'CCBB',
    'CCBP',
    'CCBA',

    'CFHIT1',
    'CFHIT2',
    'CFHIT3',
    'CFWARN',
    'CFERRO',
    'CFSUCC',

    'CBHIT1',
    'CBHIT2',
    'CBHIT3',
    'CBWARN',
    'CBERRO',
    'CBSUCC',
]

# 保存旧 print
_print = print

def print(
        *values: object,
        sep: str | None = None,
        end: str | None = None,
        # file: SupportsWrite[str] | None = None,
        file: str | None = None,
        flush: str | None = None,
    ):
    _color: str = None
    _values: list = None
    kwargs = {
        'sep': sep,
        'end': end,
        'file': file,
        'flush': flush
    }
    if len(values) > 0:
        if (_first := values[0]) in [
            CFHIT1, CFHIT2, CFHIT3, CFWARN, CFERRO, CFSUCC,
            CBHIT1, CBHIT2, CBHIT3, CBWARN, CBERRO, CBSUCC,
            CCFR, CCFG, CCFY, CCFB, CCFP, CCFA,
            CCBR, CCBG, CCBY, CCBB, CCBP, CCBA,
        ]:
            _color = _first
            _values = values[1:]

    if _color:
        # 设置颜色
        _print(_color, end='')
        # 输出文本（不要换行）
        kwargs['end'] = ''
        _print(*_values, **kwargs)
        # 清除颜色（使用原来的结束字符）
        _print(CCZ0, end=end)
    else:
        _print(*values, **kwargs)
    pass

def CC(code=0) -> str:
    '''
    code: 格式：显示方式;背景颜色;前景颜色，不传值时表示使用默认设置。
    '''
    return f'\033[{code}m'

# 显示方式 0-默认 1-高亮显示 4-下划线 5-闪烁 7-反白显示 8-不可见
#         黑色 红色 绿色 黄色 蓝色 紫色 青色 白色
# 文字颜色  30  31   32  33   34   35  36   37
# 背景颜色  40  41   42  43   44   45  46   47


CCZ0 = CC()

CCFR = CC('1;31;40')  # 红字，黑底
CCFG = CC('1;32;40')  # 绿字，黑底
CCFY = CC('1;33;40')  # 黄字，黑底
CCFB = CC('1;34;40')  # 蓝字，黑底
CCFP = CC('1;35;40')  # 紫字，黑底
CCFA = CC('1;36;40')  # 青字，黑底

CCBR = CC('1;37;41')  # 白字，红底
CCBG = CC('1;37;42')  # 白字，绿底
CCBY = CC('1;37;43')  # 白字，黄底
CCBB = CC('1;37;44')  # 白字，蓝底
CCBP = CC('1;37;45')  # 白字，紫底
CCBA = CC('1;37;46')  # 白字，青底

CFHIT1 = CCFA
CFHIT2 = CCFP
CFHIT3 = CCFB
CFWARN = CCFY
CFERRO = CCFR
CFSUCC = CCFG

CBHIT1 = CCBA
CBHIT2 = CCBP
CBHIT3 = CCBB
CBWARN = CCBY
CBERRO = CCBR
CBSUCC = CCBG
