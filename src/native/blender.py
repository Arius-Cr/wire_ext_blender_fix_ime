import typing
from typing import cast, Literal, Union
from datetime import datetime
dtfmt = '%Y-%m-%d %H:%M %z'

__all__ = ['get_data']

_bl_ver: tuple[int, int, int] = None
_ex_ver: tuple[int, int, int] = None

A = 0
Z = 99999
_3__6__X_ = (3, 6, 99)  # 人工核对偏移量的最后一个版本为 3.6.14 ，之后均假设偏移量没有变动
_4__2__X_ = (4, 2, 99)  # 人工核对偏移量的最后一个版本为 4.2.0  ，之后均假设偏移量没有变动
_4__3__X_ = (4, 3, 99)  # 人工核对偏移量的最后一个版本为 4.3.0  ，之后均假设偏移量没有变动
_4__4__X_ = (4, 4, 00)  # 开发版

def MAP(items: dict, item_name: str, maps: list[tuple[tuple[int, int, int], tuple[int, int, int], int]]):
    for map in maps:
        # map[0] - 最小版本号
        # map[1] - 最大版本号
        # map[2] - 值
        if map[0] <= _bl_ver <= map[1]:
            items[item_name] = map[2]
            return

def get_data(ex_ver: tuple[int, int, int], bl_ver: tuple[int, int, int]) -> Union[dict, None]:
    global _ex_ver, _bl_ver
    _ex_ver = ex_ver
    _bl_ver = bl_ver

    if (3, 0, 5) <= ex_ver <= (3, 0, 12):
        return get_data_3_0_5()

    return None

def get_data_3_0_5() -> dict:

    data = {
        # 数据更新时间
        'mtime': datetime.strptime('2024-12-28 13:47 +08:00', dtfmt),
        # 当前数据适用 Blender 版本范围
        'blender_vers': [
            ((3, 0, 0), _4__3__X_, None, None),
            # 开发版带有额外信息：提交日期、提交Hash（在 Blender 的关于窗口中可以看到）
            ((4, 4, 0), _4__4__X_, '2024-12-26 21:30', 'becaeac6da20'),
        ],
        'items': {},
    }

    # 需要 3.0.11 及以上才支持 Blender 4.4.0
    if _ex_ver <= (3, 0, 10):
        _blender_vers = []
        for _item in data['blender_vers']:
            if _item[0] < (4, 4, 0):
                _blender_vers.append(_item)
        data['blender_vers'] = _blender_vers

    items = cast(dict[str, int], data['items'])

    items['offset_ListBase__first'] = 0
    items['offset_ListBase__last'] = 8
    items['offset_Link__next'] = 0
    items['offset_Link__prev'] = 8

    # DNA 类型 wmWindow

    MAP(items, 'offset_wmWindow__modalhandlers', [
        ((3, 0, 0), (3, 2, Z), 272),  # V1
        ((3, 3, 0), (3, 4, Z), 280),  # V2
        ((3, 5, 0), _3__6__X_, 296),  # V3
        ((4, 0, 0), (4, 0, Z), 296),  # V3
        ((4, 1, 0), _4__2__X_, 304),  # V4
        ((4, 3, 0), _4__3__X_, 304),  # V4
        ((4, 4, 0), _4__4__X_, 304),  # V4
    ])

    MAP(items, 'offset_wmWindow__workspace_hook', [
        ((3, 0, 0), (3, 2, Z), 120),  # V1
        ((3, 3, 0), (3, 4, Z), 128),  # V2
        ((3, 5, 0), _3__6__X_, 128),  # V3
        ((4, 0, 0), (4, 0, Z), 128),  # V3
        ((4, 1, 0), _4__2__X_, 128),  # V4
        ((4, 3, 0), _4__3__X_, 128),  # V4
        ((4, 4, 0), _4__4__X_, 128),  # V4
    ])

    # DNA 类型 WorkSpaceInstanceHook

    MAP(items, 'offset_WorkSpaceInstanceHook__active', [
        ((3, 0, 0), _3__6__X_, 0),  # V1
        ((4, 0, 0), _4__2__X_, 0),  # V1
        ((4, 3, 0), _4__3__X_, 0),  # V1
        ((4, 4, 0), _4__4__X_, 0),  # V1
    ])

    MAP(items, 'offset_WorkSpaceInstanceHook__act_layout', [
        ((3, 0, 0), _3__6__X_, 8),  # V1
        ((4, 0, 0), _4__2__X_, 8),  # V1
        ((4, 3, 0), _4__3__X_, 8),  # V1
        ((4, 4, 0), _4__4__X_, 8),  # V1
    ])

    # DNA 类型 WorkSpaceLayout

    MAP(items, 'offset_WorkSpaceLayout__screen', [
        ((3, 0, 0), _3__6__X_, 16),  # V1
        ((4, 0, 0), _4__2__X_, 16),  # V1
        ((4, 3, 0), _4__3__X_, 16),  # V1
        ((4, 4, 0), _4__4__X_, 16),  # V1
    ])

    # DNA 类型 bScreen

    MAP(items, 'offset_bScreen__active_region', [
        ((3, 0, 0), _3__6__X_, 280),  # V1
        ((4, 0, 0), _4__2__X_, 280),  # V1
        ((4, 3, 0), _4__3__X_, 280),  # V1
        ((4, 3, 0), _4__4__X_, 280),  # V1
    ])

    # DNA 类型 ARegion (3.0 - 4.3)

    MAP(items, 'offset_ARegion__uiblocks', [
        ((3, 0, 0), (3, 5, Z), 232),  # V1
        ((3, 6, 0), _3__6__X_, 240),  # V2
        ((4, 0, 0), _4__2__X_, 240),  # V2
        ((4, 3, 0), _4__3__X_, 240),  # V2
    ])

    # DNA 类型 ARegion (4.4 及以上)，插件需要 3.0.11 及以上才支持

    if _ex_ver >= (3, 0, 11):
        MAP(items, 'offset_ARegion__runtime', [
            ((4, 4, 0), _4__4__X_, 296),  # V3
        ])
        MAP(items, 'offset_ARegionRuntime__uiblocks', [
            ((4, 4, 0), _4__4__X_, 496),  # V1 # 注意：Release 配置下的偏移量和 Debug 配置下的不同
        ])

    # 非 DNA 类型 wmEventHandler、wmEventHandler_UI
    # V1、V2 内存对齐后相同

    MAP(items, 'offset_wmEventHandler__type', [
        ((3, 0, 0), (3, 4, Z), 16),  # V1
        ((3, 5, 0), _3__6__X_, 16),  # V2
        ((4, 0, 0), _4__2__X_, 16),  # V2
        ((4, 3, 0), _4__3__X_, 16),  # V2
        ((4, 4, 0), _4__4__X_, 16),  # V2
    ])
    MAP(items, 'offset_wmEventHandler__handle_fn', [
        ((3, 0, 0), (3, 4, Z), 32),  # V1
        ((3, 5, 0), _3__6__X_, 32),  # V2
        ((4, 0, 0), _4__2__X_, 32),  # V2
        ((4, 3, 0), _4__3__X_, 32),  # V2
        ((4, 4, 0), _4__4__X_, 32),  # V2
    ])
    MAP(items, 'offset_wmEventHandler__remove_fn', [
        ((3, 0, 0), (3, 4, Z), 40),  # V1
        ((3, 5, 0), _3__6__X_, 40),  # V2
        ((4, 0, 0), _4__2__X_, 40),  # V2
        ((4, 3, 0), _4__3__X_, 40),  # V2
        ((4, 4, 0), _4__4__X_, 40),  # V2
    ])
    MAP(items, 'offset_wmEventHandler__user_data', [
        ((3, 0, 0), (3, 4, Z), 48),  # V1
        ((3, 5, 0), _3__6__X_, 48),  # V2
        ((4, 0, 0), _4__2__X_, 48),  # V2
        ((4, 3, 0), _4__3__X_, 48),  # V2
        ((4, 4, 0), _4__4__X_, 48),  # V2
    ])
    MAP(items, 'offset_wmEventHandler__area', [
        ((3, 0, 0), (3, 4, Z), 56),  # V1
        ((3, 5, 0), _3__6__X_, 56),  # V2
        ((4, 0, 0), _4__2__X_, 56),  # V2
        ((4, 3, 0), _4__3__X_, 56),  # V2
        ((4, 4, 0), _4__4__X_, 56),  # V2
    ])
    MAP(items, 'offset_wmEventHandler__region', [
        ((3, 0, 0), (3, 4, Z), 64),  # V1
        ((3, 5, 0), _3__6__X_, 64),  # V2
        ((4, 0, 0), _4__2__X_, 64),  # V2
        ((4, 3, 0), _4__3__X_, 64),  # V2
        ((4, 4, 0), _4__4__X_, 64),  # V2
    ])
    MAP(items, 'offset_wmEventHandler__menu', [
        ((3, 0, 0), (3, 4, Z), 72),  # V1
        ((3, 5, 0), _3__6__X_, 72),  # V2
        ((4, 0, 0), _4__2__X_, 72),  # V2
        ((4, 3, 0), _4__3__X_, 72),  # V2
        ((4, 4, 0), _4__4__X_, 72),  # V2
    ])

    MAP(items, 'WM_HANDLER_TYPE_UI', [
        ((3, 0, 0), _3__6__X_, 2),  # V1
        ((4, 0, 0), _4__2__X_, 2),  # V2
        ((4, 3, 0), _4__3__X_, 2),  # V2
        ((4, 4, 0), _4__4__X_, 2),  # V2
    ])

    # 非 DNA 类型 uiHandleButtonData
    MAP(items, 'sizeof_uiHandleButtonData', [
        ((3, 0, 0), (3, 1, Z), 376),  # V1
        ((3, 2, 0), _3__6__X_, 376),  # V2 内存对齐后和 V1 相同
        ((4, 0, 0), (4, 1, 1), 376),  # V2
        ((4, 2, 0), _4__2__X_, 360),  # V3
        ((4, 3, 0), _4__3__X_, 360),  # V4 开发版 uiHandleButtonData 总有差异，需要通过调试信息确定大小
        ((4, 4, 0), _4__4__X_, 360),  # V4 开发版 uiHandleButtonData 总有差异，需要通过调试信息确定大小
    ])

    # 非 DNA 类型 uiPopupBlockHandle

    MAP(items, 'sizeof_uiPopupBlockHandle', [
        ((3, 0, 0), _3__6__X_, 264),  # V1
        ((4, 0, 0), _4__2__X_, 328),  # V2
        ((4, 3, 0), _4__3__X_, 328),  # V2
        ((4, 4, 0), _4__4__X_, 328),  # V2
    ])

    MAP(items, 'offset_uiPopupBlockHandle__region', [
        ((3, 0, 0), _3__6__X_, 0),  # V1
        ((4, 0, 0), _4__2__X_, 0),  # V2
        ((4, 3, 0), _4__3__X_, 0),  # V2
        ((4, 4, 0), _4__4__X_, 0),  # V2
    ])

    # 非 DNA 类型 uiBlock

    MAP(items, 'offset_uiBlock__buttons', [
        ((3, 0, 0), (3, 3, Z), 16),  # V1
        ((3, 4, 0), (3, 4, Z), 16),  # V2
        ((3, 5, 0), _3__6__X_, 16),  # V3
        ((4, 0, 0), (4, 0, Z), 16),  # V4
        ((4, 1, 0), (4, 1, 1), 16),  # V5
        ((4, 2, 0), _4__2__X_, 16),  # V6
        ((4, 3, 0), _4__3__X_, 16),  # V7 开发版 uiBlock 总有差异，但不影响该成员
        ((4, 4, 0), _4__4__X_, 16),  # V7 开发版 uiBlock 总有差异，但不影响该成员
    ])

    # 非 DNA 类型 uiBut

    MAP(items, 'offset_uiBut__flag', [
        ((3, 0, 0), (3, 0, Z), 24),  # V1
        ((3, 1, 0), (3, 1, Z), 24),  # V2
        ((3, 2, 0), (3, 2, Z), 24),  # V3
        ((3, 3, 0), (3, 3, Z), 24),  # V4
        ((3, 4, 0), _3__6__X_, 24),  # V5
        ((4, 0, 0), (4, 0, Z), 24),  # V6
        ((4, 1, 0), (4, 1, 1), 24),  # V7
        ((4, 2, 0), _4__2__X_, 24),  # V8
        ((4, 3, 0), _4__3__X_, 24),  # V9 开发版 uiBut 总有差异，但不影响该成员
        ((4, 4, 0), _4__4__X_, 24),  # V9 开发版 uiBut 总有差异，但不影响该成员
    ])

    MAP(items, 'offset_uiBut__type', [
        ((3, 0, 0), (3, 0, Z), 32),  # V1
        ((3, 1, 0), (3, 1, Z), 32),  # V2
        ((3, 2, 0), (3, 2, Z), 32),  # V3
        ((3, 3, 0), (3, 3, Z), 32),  # V4
        ((3, 4, 0), _3__6__X_, 32),  # V5
        ((4, 0, 0), (4, 0, Z), 36),  # V6
        ((4, 1, 0), (4, 1, 1), 36),  # V7
        ((4, 2, 0), _4__2__X_, 36),  # V8
        ((4, 3, 0), _4__3__X_, 36),  # V9 开发版 uiBut 总有差异，但不影响该成员
        ((4, 4, 0), _4__4__X_, 36),  # V9 开发版 uiBut 总有差异，但不影响该成员
    ])

    MAP(items, 'UI_SELECT', [
        ((3, 0, 0), _3__6__X_, (1 << 0)),  # V1
        ((4, 0, 0), _4__2__X_, (1 << 0)),  # V2
        ((4, 3, 0), _4__3__X_, (1 << 0)),  # V2
        ((4, 4, 0), _4__4__X_, (1 << 0)),  # V2
    ])  # 十六进制：   1，( 1 << 0)

    MAP(items, 'UI_BTYPE_TEXT', [
        ((3, 0, 0), _3__6__X_, (3 << 9)),  # V1
        ((4, 0, 0), _4__2__X_, (3 << 9)),  # V2
        ((4, 3, 0), _4__3__X_, (3 << 9)),  # V2
        ((4, 4, 0), _4__4__X_, (3 << 9)),  # V2
    ])  # 十六进制： 600，( 3 << 9)

    MAP(items, 'UI_BTYPE_NUM', [
        ((3, 0, 0), _3__6__X_, (6 << 9)),  # V1
        ((4, 0, 0), _4__2__X_, (6 << 9)),  # V2
        ((4, 3, 0), _4__3__X_, (6 << 9)),  # V2
        ((4, 4, 0), _4__4__X_, (6 << 9)),  # V2
    ])  # 十六进制： C00，( 6 << 9)

    MAP(items, 'UI_BTYPE_SEARCH_MENU', [
        ((3, 0, 0), _3__6__X_, (41 << 9)),  # V1
        ((4, 0, 0), _4__2__X_, (41 << 9)),  # V2
        ((4, 3, 0), _4__3__X_, (41 << 9)),  # V2
        ((4, 4, 0), _4__4__X_, (41 << 9)),  # V2
    ])  # 十六进制：5200，(41 << 9)

    # DNA 类型 SpaceText、SpaceText_Runtime

    MAP(items, 'offset_SpaceText__runtime', [
        ((3, 0, 0), _3__6__X_, 592),  # V1
        ((4, 0, 0), (4, 0, Z), 592),  # V1
        ((4, 1, 0), _4__2__X_, 592),  # V2
        ((4, 3, 0), _4__3__X_, 592),  # V2
        ((4, 4, 0), _4__4__X_, 592),  # V2
    ])

    MAP(items, 'offset_SpaceText_Runtime__lheight_px', [
        ((3, 0, 0), _3__6__X_, 0),  # V1
        ((4, 0, 0), (4, 0, Z), 0),  # V1
        ((4, 1, 0), _4__2__X_, 0),  # V2
        ((4, 3, 0), _4__3__X_, 0),  # V2
        ((4, 4, 0), _4__4__X_, 0),  # V2
    ])

    MAP(items, 'offset_SpaceText_Runtime__cwidth_px', [
        ((3, 0, 0), _3__6__X_, 4),  # V1
        ((4, 0, 0), (4, 0, Z), 4),  # V1
        ((4, 1, 0), _4__2__X_, 4),  # V2
        ((4, 3, 0), _4__3__X_, 4),  # V2
        ((4, 4, 0), _4__4__X_, 4),  # V2
    ])

    MAP(items, 'offset_SpaceText_Runtime__line_number_display_digits', [
        ((3, 0, 0), _3__6__X_, 40),  # V1
        ((4, 0, 0), (4, 0, Z), 40),  # V1
        ((4, 1, 0), _4__2__X_, 40),  # V2
        ((4, 3, 0), _4__3__X_, 40),  # V2
        ((4, 4, 0), _4__4__X_, 40),  # V2
    ])

    MAP(items, 'SpaceText_ver', [
        ((3, 0, 0), _3__6__X_, 1),  # V1
        ((4, 0, 0), (4, 0, Z), 1),  # V1
        ((4, 1, 0), _4__2__X_, 2),  # V2
        ((4, 3, 0), _4__3__X_, 2),  # V2
        ((4, 4, 0), _4__4__X_, 2),  # V2
    ])

    return data
