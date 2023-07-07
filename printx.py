from __future__ import annotations  # 兼容 Python 3.9

from typing import cast, Literal, Union, Protocol, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

    _T_contra = TypeVar("_T_contra", contravariant=True)

    class SupportsWriteAndFlush(SupportsWrite[_T_contra], Protocol[_T_contra]):
        def flush(self) -> None: ...

# ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

all = [
    'printx',

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

def printx(
    *values: object,
    sep: Union[str, None] = ' ',
    end: Union[str, None] = '\n',
    file: Union[SupportsWrite[str], SupportsWriteAndFlush[str], None] = None,
    flush: bool = False,
):
    color: str = None
    if len(values) > 0:
        if (_first := values[0]) in [
            CFHIT1, CFHIT2, CFHIT3, CFWARN, CFERRO, CFSUCC,
            CBHIT1, CBHIT2, CBHIT3, CBWARN, CBERRO, CBSUCC,
            CCFR, CCFG, CCFY, CCFB, CCFP, CCFA,
            CCBR, CCBG, CCBY, CCBB, CCBP, CCBA,
        ]:
            color = _first
    if color:
        # 设置颜色
        print(color, end='', file=file, flush=flush)
        # 输出文本
        print(*values[1:], sep=sep, end='', file=file, flush=flush)
        # 清除颜色
        print('\033[0m', end=end, file=file, flush=flush)
    else:
        print(*values, sep=sep, end=end, file=file, flush=flush)
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
