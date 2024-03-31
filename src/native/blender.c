#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <windows.h>
// Self
#include "main.h"
#include "utils.h"
#include "blender.h"

/**
 * 本文件提供的函数主要根据 BPY 提供的 as_pointer() 函数，
 * 获取的数据结构的内存地址，然后根据结构的成员偏移量获取结构中成员的值。
 * 
 * 从 Blender 源码中可以找到结构的声明，然后通过计算可以获取成员的偏移量。
 * 由于偏移量可能随版本不同而不同，因此需要整理出该结构在所有版本中的声明，
 * 然后分别计算不同版本中该结构成员的偏移量。
 * 
 * 从源码中提取的结构的声明记录在 `offset` 目录中，
 * 具体请查看该目录中的 `README.txt` 文件。
 */

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

#define UNKNOWN 0

#define Z 99999

#define VER_GTE(m, s, r) \
    ((ver_m > m) || (ver_m == m && ver_s > s) || (ver_m == m && ver_s == s && ver_r >= r))

#define VER_LTE(m, s, r) \
    ((ver_m < m) || (ver_m == m && ver_s < s) || (ver_m == m && ver_s == s && ver_r <= r))

#define GEN_ADDR(base, offset) ((size_t)base + offset)

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

/**
 * 获知输入框是否激活，浮动窗是否弹出的方法：
 *
 * 首先是没有直接的方法的，但可以根据相关数据判断出来。
 *
 * 通过分析源码，可知输入框和浮动窗激活时，会向窗口的模态处理器列表中添加一个模态处理器节点，
 * 且该模态处理器总是该列表中的第一个，根据这个模态处理器节点的相关数据即可进行判断。
 *
 * 窗口 - wmWindow
 * 窗口的模态处理器列表 - wmWindow.modalhandlers
 * 模态处理器节点 - wmEventHandler、wmEventHandler_UI
 *
 * 不止输入框和浮动窗会使用注册模态处理器，其它的功能也会，以下是对所有情况的归纳：
 *
 * 因为我们关心的输入框和浮动窗的模态处理器类型为 WM_HANDLER_TYPE_UI，
 * 因此只需要关注 WM_HANDLER_TYPE_UI 类型的模态处理器的所有可能情况即可。
 *
 * 检索源码可知所有 WM_HANDLER_TYPE_UI 类型的模态处理器均由 WM_event_add_ui_handler 函数添加，
 * 因此查看 WM_event_add_ui_handler 函数的调用者即可溯源所有注册 WM_HANDLER_TYPE_UI 类型模态处理器的对象。
 * WM_event_add_ui_handler 函数的调用者：
 *      1. ui_but_drag_init
 *      2. button_activate_state (输入框)
 *      3. UI_region_handlers_add
 *      4. UI_popup_handlers_add (浮动窗)
 *      5. ui_panel_drag_collapse_handler_add、UI_panel_drag_collapse_handler_add
 *      6. panel_handle_data_ensure
 *      7. WM_operator_name_call_ptr_with_depends_on_cursor
 *      8. wm_exit_schedule_delayed
 * 注册信息归纳如下：
 *   | context | handle_fn | remove_fn | user_data                  | flag
 * 1 |    Y    |     Y     |     Y     | uiDragToggleHandle*        | WM_HANDLER_BLOCKING
 * 2 |    Y    |     Y     |     N     | uiHandleButtonData*        | 0
 * 3 |    N    |     Y     |     Y     | N                          | 0
 * 4 |    Y    |     Y     |     Y     | uiPopupBlockHandle*        | 0 / WM_HANDLER_ACCEPT_DBL_CLICK
 * 5 |    Y    |     Y     |     Y     | uiPanelDragCollapseHandle* | 0
 * 6 |    Y    |     Y     |     Y     | Panel*                     | 0
 * 7 |    Y    |     Y     |     Y     | uiOperatorWaitForInput*    | WM_HANDLER_BLOCKING
 * 8 |    Y    |     Y     |     N     | N                          | 0
 * 
 * 1 - uiDragToggleHandle 为非 DNA 类型，       大小约 40  字节。
 * 2 - uiHandleButtonData 为 DNA 类型，         大小约 376 字节。（输入框）
 * 4 - uiPopupBlockHandle 为非 DNA 类型，       大小约 262 字节。（浮动窗）
 * 5 - uiPanelDragCollapseHandle 为非 DNA 类型，大小约 16  字节。
 * 6 - Panel 为 DNA 类型，                      大小约 176 字节。
 * 7 - uiOperatorWaitForInput 为非 DNA 类型，   大小约 40  字节。
 * 
 * 由于上述我们关心的几个结构的大小的差异较大，因此直接根据结构的大小即可判断出来。
 * 结构的大小根据 MSVC (64 Bit) 的习惯，存储在结构头部往前 8 字节处。
 * 
 * 具体判断逻辑，请参考下面的 wmWindow_is_but_active 和 wmWindow_is_pop_active 函数。
 */

// ----------

// 文件：source\blender\makesdna\DNA_listBase.h
// typedef struct ListBase { void *first, *last; } ListBase;
// ListBase.first: void *
static size_t offset_ListBase__first = UNKNOWN;

// ----------

// 文件：source\blender\makesdna\DNA_windowmanager_types.h
// wmWindow.modalhandlers: ListBase<wmEventHandler>
static size_t offset_wmWindow__modalhandlers = UNKNOWN;

// 文件：source\blender\windowmanager\wm_event_system.h
// wmEventHandler_UI.head.type: int
static size_t offset_wmEventHandler__type = UNKNOWN;
// wmEventHandler_UI.head.flag: char / eWM_EventHandlerFlag
static size_t offset_wmEventHandler__flag = UNKNOWN;
// wmEventHandler_UI.handle_fn: function
static size_t offset_wmEventHandler__handle_fn = UNKNOWN;
// wmEventHandler_UI.remove_fn: function
static size_t offset_wmEventHandler__remove_fn = UNKNOWN;
// wmEventHandler_UI.user_data: void *
static size_t offset_wmEventHandler__user_data = UNKNOWN;
// wmEventHandler_UI.context.area: ScrArea *
static size_t offset_wmEventHandler__area = UNKNOWN;
// wmEventHandler_UI.context.region: ARegion *
static size_t offset_wmEventHandler__region = UNKNOWN;
// wmEventHandler_UI.context.menu: ARegion *
static size_t offset_wmEventHandler__menu = UNKNOWN;

// 关联：wmEventHandler.head.type
// 文件：source\blender\windowmanager\wm_event_system.h
static int WM_HANDLER_TYPE_UI = UNKNOWN;

// 关联：wmEventHandler.user_data
// 文件：source\blender\editors\interface\interface_handlers.c
// sizeof(uiHandleButtonData)
static size_t sizeof_uiHandleButtonData = UNKNOWN;

// 关联：wmEventHandler.user_data
// 文件：source\blender\editors\interface\interface_intern.h
// sizeof(uiPopupBlockHandle)
static size_t sizeof_uiPopupBlockHandle = UNKNOWN;

// 关联：wmEventHandler.flag
static int WM_HANDLER_BLOCKING = UNKNOWN;
static int WM_HANDLER_ACCEPT_DBL_CLICK = UNKNOWN;
static int WM_HANDLER_DO_FREE = UNKNOWN;

// ----------

// 文件：source\blender\makesdna\DNA_windowmanager_types.h
// wmWindow.workspace_hook: WorkSpaceInstanceHook*
static size_t offset_wmWindow__workspace_hook = UNKNOWN;

// 文件：source\blender\makesdna\DNA_workspace_types.h
// WorkSpaceInstanceHook.active: WorkSpace *
static size_t offset_WorkSpaceInstanceHook__active = UNKNOWN;
// WorkSpaceInstanceHook.act_layout: WorkSpaceLayout *
static size_t offset_WorkSpaceInstanceHook__act_layout = UNKNOWN;

// 文件：source\blender\makesdna\DNA_workspace_types.h
// WorkSpaceLayout.screen: bScreen*
static size_t offset_WorkSpaceLayout__screen = UNKNOWN;

// 文件：source\blender\makesdna\DNA_screen_types.h
// bScreen.active_region: ARegion*
static size_t offset_bScreen__active_region = UNKNOWN;

extern __declspec(dllexport) bool wmWindow_is_but_active(void *wm_pointer)
{
    // 获取窗口模态处理器链表中的第一个节点
    size_t addr_handler = *(size_t *)GEN_ADDR(wm_pointer,
                                              offset_wmWindow__modalhandlers + offset_ListBase__first);
    // printx(D_IME, CCFR "addr_handler: %zu", addr_handler);
    if (addr_handler)
    {
        // 获取模态处理器类型
        int handler_type = *(int *)GEN_ADDR(addr_handler,
                                            offset_wmEventHandler__type);
        // printx(D_IME, CCFR "handler_type: %d, %d", handler_type, WM_HANDLER_TYPE_UI);
        if (handler_type == WM_HANDLER_TYPE_UI)
        {
            size_t handle_fn = *(size_t *)GEN_ADDR(addr_handler,
                                                   offset_wmEventHandler__handle_fn);
            size_t remove_fn = *(size_t *)GEN_ADDR(addr_handler,
                                                   offset_wmEventHandler__remove_fn);
            size_t user_data = *(size_t *)GEN_ADDR(addr_handler,
                                                   offset_wmEventHandler__user_data);
            if (handle_fn && !remove_fn && user_data)
            {
                // printx(D_IME, CCFR "handle_fn && !remove_fn && user_data");
                size_t user_data_len = *(size_t *)GEN_ADDR(user_data, -sizeof(size_t));
                printx(D_IME, CCFR "wmWindow_is_but_active handler_type: %d, target: %d",
                       handler_type, WM_HANDLER_TYPE_UI);
                printx(D_IME, CCFR "wmWindow_is_but_active user_data_len: %zu, target: %zu",
                       user_data_len, sizeof_uiHandleButtonData);
                if (user_data_len == sizeof_uiHandleButtonData)
                {
                    return true;
                }
            }
        }
    }
    return false;
}

extern __declspec(dllexport) bool wmWindow_is_pop_active(void *wm_pointer)
{
    // 获取窗口模态处理器链表中的第一个节点
    size_t addr_handler = *(size_t *)GEN_ADDR(wm_pointer,
                                              offset_wmWindow__modalhandlers + offset_ListBase__first);
    // printx(D_IME, CCFR "addr_handler: %zu", addr_handler);
    if (addr_handler)
    {
        // 获取模态处理器类型
        int handler_type = *(int *)GEN_ADDR(addr_handler,
                                            offset_wmEventHandler__type);
        // printx(D_IME, CCFR "handler_type: %d, %d", handler_type, WM_HANDLER_TYPE_UI);
        if (handler_type == WM_HANDLER_TYPE_UI)
        {
            size_t handle_fn = *(size_t *)GEN_ADDR(addr_handler,
                                                   offset_wmEventHandler__handle_fn);
            size_t remove_fn = *(size_t *)GEN_ADDR(addr_handler,
                                                   offset_wmEventHandler__remove_fn);
            size_t user_data = *(size_t *)GEN_ADDR(addr_handler,
                                                   offset_wmEventHandler__user_data);
            if (handle_fn && remove_fn && user_data)
            {
                // printx(D_IME, CCFR "handle_fn && remove_fn && user_data");
                size_t user_data_len = *(size_t *)GEN_ADDR(user_data, -sizeof(size_t));
                printx(D_IME, CCFR "wmWindow_is_pop_active handler_type: %d, target: %d",
                       handler_type, WM_HANDLER_TYPE_UI);
                printx(D_IME, CCFR "wmWindow_is_pop_active user_data_len: %zu, target: %zu",
                       user_data_len, sizeof_uiPopupBlockHandle);
                if (user_data_len == sizeof_uiPopupBlockHandle)
                {
                    return true;
                }
            }
        }
    }
    return false;
}

extern __declspec(dllexport) void *wmWindow_active_screen_get(void *wm_pointer)
{
    // 参考源码：WM_window_get_active_screen
    size_t p = *(size_t *)GEN_ADDR(wm_pointer, offset_wmWindow__workspace_hook);
    size_t p_workspace = *(size_t *)GEN_ADDR(p, offset_WorkSpaceInstanceHook__active);
    if (p_workspace)
    {
        size_t p_layout = *(size_t *)GEN_ADDR(p, offset_WorkSpaceInstanceHook__act_layout);
        size_t p_screen = *(size_t *)GEN_ADDR(p_layout, offset_WorkSpaceLayout__screen);
        return (void *)p_screen;
    }
    return NULL;
}

extern __declspec(dllexport) void *wmWindow_active_region_get(void *wm_pointer)
{
    size_t p_screen = (size_t)wmWindow_active_screen_get(wm_pointer);
    if (p_screen)
    {
        size_t p_region = *(size_t *)GEN_ADDR(p_screen, offset_bScreen__active_region);
        return (void *)p_region;
    }
    return NULL;
}

static void blender_data_init_wmWindow()
{
    offset_ListBase__first = 0;

    WM_HANDLER_TYPE_UI = 2;

    WM_HANDLER_BLOCKING = 1;
    WM_HANDLER_ACCEPT_DBL_CLICK = 2;
    WM_HANDLER_DO_FREE = 128;

    // ----- DNA 类型 wmWindow

    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V4
    {
        offset_wmWindow__workspace_hook = 128;
        offset_wmWindow__modalhandlers = 304;
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V3
             (VER_GTE(3, 5, 0) && VER_LTE(3, 6, 9)))   // V3
    {
        offset_wmWindow__workspace_hook = 128;
        offset_wmWindow__modalhandlers = 296;
    }
    else if ((VER_GTE(3, 3, 0) && VER_LTE(3, 4, Z))) //// V2
    {
        offset_wmWindow__workspace_hook = 128;
        offset_wmWindow__modalhandlers = 280;
    }
    else if ((VER_GTE(3, 0, 0) && VER_LTE(3, 2, Z))) //// V1
    {

        offset_wmWindow__workspace_hook = 120;
        offset_wmWindow__modalhandlers = 272;
    }

    // ----- DNA 类型 WorkSpaceInstanceHook

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        offset_WorkSpaceInstanceHook__active = 0;
        offset_WorkSpaceInstanceHook__act_layout = 8;
    }

    // ----- DNA 类型 WorkSpaceLayout

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        offset_WorkSpaceLayout__screen = 16;
    }

    // ----- DNA 类型 bScreen

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        offset_bScreen__active_region = 280;
    }

    // ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

    // ----- 非 DNA 类型 wmEventHandler、wmEventHandler_UI

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0)) || // V2
             (VER_GTE(3, 5, 0) && VER_LTE(3, 6, 9)) || // V2
             (VER_GTE(3, 0, 0) && VER_LTE(3, 4, Z)))   // V1
    {
        // V1、V2 内存对齐后相同

        offset_wmEventHandler__type = 16;

        offset_wmEventHandler__handle_fn = 32;
        offset_wmEventHandler__remove_fn = 40;
        offset_wmEventHandler__user_data = 48;
        offset_wmEventHandler__area = 56;
        offset_wmEventHandler__region = 64;
        offset_wmEventHandler__menu = 72;

        WM_HANDLER_TYPE_UI = 2;
    }

    // ----- 非 DNA 类型 uiHandleButtonData

    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0)) || // V3
             (VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V2
             (VER_GTE(3, 2, 0) && VER_LTE(3, 6, 9)) || // V2
             (VER_GTE(3, 0, 0) && VER_LTE(3, 1, Z)))   // V1
    {
        // V1、V2、V3 内存对齐后相同

        sizeof_uiHandleButtonData = 376;
    }

    // ----- 非 DNA 类型 uiPopupBlockHandle

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0))) // V2
    {
        sizeof_uiPopupBlockHandle = 328;
    }
    else if ((VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9))) // V1
    {
        sizeof_uiPopupBlockHandle = 264;
    }
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

// 文件：source\blender\makesdna\DNA_space_types.h
// SpaceText.runtime: SpaceText_Runtime
static size_t offset_SpaceText__runtime = UNKNOWN;
// SpaceText_Runtime.lheight_px: int
static size_t offset_SpaceText_Runtime__lheight_px = UNKNOWN;
// SpaceText_Runtime.cwidth_px: int
static size_t offset_SpaceText_Runtime__cwidth_px = UNKNOWN;
// SpaceText_Runtime.line_number_display_digits: int
static size_t offset_SpaceText_Runtime__line_number_display_digits = UNKNOWN;

extern __declspec(dllexport) int SpaceText_lheight_px_get(void *SpaceText)
{
    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V2
    {
        size_t p_runtime = *(size_t *)GEN_ADDR(SpaceText, offset_SpaceText__runtime);
        if (p_runtime)
        {
            int value = *(int *)GEN_ADDR(p_runtime, offset_SpaceText_Runtime__lheight_px);
            return value;
        }
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        size_t runtime = (size_t)SpaceText + offset_SpaceText__runtime;
        int value = *(int *)GEN_ADDR(runtime, offset_SpaceText_Runtime__lheight_px);
        return value;
    }

    return 1000;
}

extern __declspec(dllexport) int SpaceText_cwidth_px_get(void *SpaceText)
{
    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V2
    {
        size_t p_runtime = *(size_t *)GEN_ADDR(SpaceText, offset_SpaceText__runtime);
        if (p_runtime)
        {
            int value = *(int *)GEN_ADDR(p_runtime, offset_SpaceText_Runtime__cwidth_px);
            return value;
        }
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        size_t runtime = (size_t)SpaceText + offset_SpaceText__runtime;
        int value = *(int *)GEN_ADDR(runtime, offset_SpaceText_Runtime__cwidth_px);
        return value;
    }

    return 1000;
}

extern __declspec(dllexport) int SpaceText_line_number_display_digits_get(void *SpaceText)
{
    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V2
    {
        size_t p_runtime = *(size_t *)GEN_ADDR(SpaceText, offset_SpaceText__runtime);
        if (p_runtime)
        {
            int value = *(int *)GEN_ADDR(p_runtime, offset_SpaceText_Runtime__line_number_display_digits);
            return value;
        }
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        size_t runtime = (size_t)SpaceText + offset_SpaceText__runtime;
        int value = *(int *)GEN_ADDR(runtime, offset_SpaceText_Runtime__line_number_display_digits);
        return value;
    }

    return 0;
}

static void blender_data_init_SpaceText()
{
    // ----- DNA 类型 SpaceText、SpaceText_Runtime

    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V2
    {
        offset_SpaceText__runtime = 592;
        offset_SpaceText_Runtime__lheight_px = 0;
        offset_SpaceText_Runtime__cwidth_px = 4;
        offset_SpaceText_Runtime__line_number_display_digits = 40;
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        offset_SpaceText__runtime = 592;
        offset_SpaceText_Runtime__lheight_px = 0;
        offset_SpaceText_Runtime__cwidth_px = 4;
        offset_SpaceText_Runtime__line_number_display_digits = 40;
    }
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) void blender_data_init()
{
    blender_data_init_wmWindow();

    blender_data_init_SpaceText();
}
