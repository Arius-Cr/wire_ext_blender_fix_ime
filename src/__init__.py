import sys

bl_info = {
    'name': "输入法助手",
    'author': "阿弩斯(Arius)",
    'description': "增强 Blender 对 Windows 平台上输入法的支持",
    'blender': (3, 0, 0),
    'version': (3, 0, 16),
    'location': "",
    'support': 'COMMUNITY',
    'category': 'User Interface',
    'doc_url': '',
    'tracker_url': '',
}

# Blender 4.2.0 及以上以 Extension 的方式加载插件时，会在启用插件时删除 bl_info，
# 此处备份该信息以便后续使用
_bl_info = bl_info

def register():
    from . import main
    main.register()

    pass

def unregister():
    from .debug.mark import mark
    from . import main
    main.unregister()

    # 删除模块，以便下次加载时能够自动加载最新的模块
    if __package__ in sys.modules:
        if mark.DEBUG_BUILD:
            print("del:", __package__)
        del sys.modules[__package__]
    sub_module_prefix = __package__ + '.'
    for m in tuple(sys.modules):
        if m.startswith(sub_module_prefix):
            if mark.DEBUG_BUILD:
                print("del:", m)
            del sys.modules[m]
    pass
