import sys
import importlib
import traceback

# 注意 ：不要在 __init__.py 中直接或间接引用 bpy，参考：make.by: pack()
# 必须要引用，可以通过 try 来防止异常。

bl_info = {
    'name': "wire_fix_ime",
    'author': "阿弩斯(Arius)",
    'description': "修复 Blender 中和 IME 相关的一些问题",
    'blender': (3, 0, 0),
    'version': (2, 0, 0),
    '_pre_release': 'beta.6',
    'location': "",
    'warning': "beta.6（测试版）",
    'doc_url': "https://github.com/Arius-Cr/wire_ext_blender_fix_ime",
    'support': 'COMMUNITY',
    'category': 'User Interface',
}

_mark = None
_main = None

def register():
    if sys.platform != 'win32':
        raise Exception("本插件仅支持 Windows 平台")
    
    import bpy
    if bpy.app.background:
        print(f'{__package__} 在 Blender 处于后台（--background）模式时不生效')
        return

    global _mark, _main
    # Blender 会自动重新加载新的 __init__.py，但是不会重新加载其它模块。
    # 因此需要 import_module 和 卸载时删除插件中的其它模块 来实现刷新。
    _mark = importlib.import_module('.mark', __package__).mark
    _main = importlib.import_module('.main', __package__)
    _main.register()
    pass

def unregister():
    import bpy
    if bpy.app.background:
        return
    
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
