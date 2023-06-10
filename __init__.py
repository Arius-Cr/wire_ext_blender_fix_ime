import sys

from . mark import *

# 不要在 __init__.py 中引用 bpy，参考：make.by: pack()

bl_info = {
    'name': "wire_fix_ime",
    'author': "阿弩斯(Arius)",
    'description': "修复输入文字后输入法状态不正确的问题",
    'blender': (3, 0, 0),
    'version': (1, 0, 0),
    'location': "",
    'warning': "",
    'category': 'Generic',
}

def register():
    if (modu_main := __name__ + '.main') in sys.modules:
        del sys.modules[modu_main]
    from . import main
    main.register()

def unregister():
    from . import main
    main.unregister()
