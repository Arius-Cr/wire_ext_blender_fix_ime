import sys
import traceback
from typing import cast

import bpy

from .mark import *

from .native import native

def register():

    native.dll_load()

    native.use_debug(DEBUG)
    native.use_hook_debug(DEBUG)
    native.use_fix_ime_state_debug(DEBUG)

    native.init()

    native.use_hook(True)

    native.use_fix_ime_state(True)

    pass

def unregister():

    native.use_hook(False)

    native.dll_unload()

    module_clean()

    pass

def module_clean():
    addon_prefix = "%s." % __package__
    module_keys: list[str] = []
    for k in sys.modules.keys():
        if addon_prefix in k:
            module_keys.append(k)
    for k in module_keys:
        # print("del: %s" % k)
        del sys.modules[k]
