import sys
import importlib

# 注意 ：不要在 __init__.py 中直接或间接引用 bpy，参考：make.by: pack()
# 必须要引用，可以通过 try 来防止异常。

bl_info = {
    'name': "wire_fix_ime",
    'author': "阿弩斯(Arius)",
    'description': "修复 Blender 中和 IME 相关的一些问题",
    'blender': (3, 0, 0),
    'version': (2, 0, 0),
    '_pre_release': 'beta.3',
    'location': "",
    'warning': "beta.3（测试版）",
    'category': 'User Interface',
}

_mark = None
_main = None

def register():
    global _mark, _main
    # Blender 会自动重新加载新的 __init__.py，但是不会重新加载其它模块。
    # 因此需要 import_module 和 卸载时删除插件中其它模块 来实现刷新。
    _mark = importlib.import_module('.mark', __package__).mark
    _main = importlib.import_module('.main', __package__)
    _main.register()
    pass

def unregister():
    _main.unregister()

    addon_sub_modules_prefix = __package__ + '.'
    module_keys: list[str] = []
    for k in sys.modules.keys():
        if k.startswith(addon_sub_modules_prefix):
            module_keys.append(k)
    for k in module_keys:
        if _mark.DEBUG:
            print("del: %s" % k)
        del sys.modules[k]
    pass
