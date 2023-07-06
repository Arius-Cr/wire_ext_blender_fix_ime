import sys
import importlib

from . import mark

# 不要在 __init__.py 中引用直接或间接引用 bpy，参考：make.by: pack()
# 或者用 try ？

# 注意 ：3.0.X 版的 Blender 自带的 Python (3.9) 不支持 "A | B" 形式的类型注解。

bl_info = {
    'name': "wire_fix_ime",
    'author': "阿弩斯(Arius)",
    'description': "修复 Blender 中和 IME 相关的一些问题",
    'blender': (3, 0, 0),
    'version': (2, 0, 0),
    '_pre_release': 'beta.2',
    'location': "",
    'warning': "beta.2（测试版）",
    'category': 'User Interface',
}

def register():
    main = importlib.import_module('.main', __package__)
    main.register()
    pass

def unregister():
    main = importlib.import_module('.main', __package__)
    main.unregister()
    module_clean()  # 以便重新加载时可以载入最新的文件（Blender 会自动重新加载最新的 __init__.py 文件）
    pass

def module_clean():
    addon_name = __package__
    addon_prefix = "%s." % addon_name
    module_keys: list[str] = []
    for k in sys.modules.keys():
        if k.startswith(addon_prefix):
            module_keys.append(k)
    for k in module_keys:
        if mark.DEBUG:
            print("del: %s" % k)
        del sys.modules[k]
    pass
