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
#define GET_VALUE(type, base, offset) *(type *)GEN_ADDR(base, offset)

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

// 文件：source\blender\makesdna\DNA_listBase.h
// typedef struct ListBase { void *first, *last; } ListBase;
// ListBase.first: void *
static size_t offset_ListBase__first = UNKNOWN;
static size_t offset_ListBase__last = UNKNOWN;
static size_t offset_Link__next = UNKNOWN;
static size_t offset_Link__prev = UNKNOWN;

// ----------

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
 *
 * ==========
 *
 * 关于浮动窗口中的文本框是否被激活的判断方式，需要参考源码：ui_popup_handler，
 * 该函数负责浮动窗口的所有事件的处理。
 *
 * 浮动窗口中的文本框在激活的时候不会向窗口的模态处理器列表注册模态处理器，
 * 此时，浮动窗口的模态处理器实际上同时担任文本框的模态处理器。
 * 消息经过一定的处理后，最终到达 ui_handle_menu_button，
 * 该函数的主要逻辑就是判断当前区块(Region)是否存在活动按钮（uiBut），
 * 如果存在则消息由其处理，否则...
 *
 * 在该函数的头部，通过函数 ui_region_find_active_but 查找活动按钮。
 *
 * 那么我们只要在存在浮动窗口的时候，检查是否存在活动按钮，且按钮为文本框，
 * 即可判断出是单纯存在浮动窗口还是浮动窗口中由文本框被激活。
 *
 * 之所以要区分是因为遇到前者时要停用输入法，而遇到后者时不能干扰输入法状态。
 *
 * 经过具体的实践后，判断浮动窗口中是否存在活动文本框的方法定为：
 * 1. 遍历 ARegion 中的 uiBlock 中的 uiBut，
 * 2. 如果某个 uiBut 的类型为文本或数值，且存在 UI_SELECT 标记，则存在活动文本框。
 *
 * 虽然具有 UI_SELECT 标记的按钮不一定是活动按钮，
 * 譬如当该按钮正在弹出枚举列表、菜单或面板时，也会具有该标记，但此时按钮为非活动按钮。
 * 但是对于文本和数据框而言，有 UI_SELECT 时，它必定为活动按钮。
 *
 * 第二方案：按照 ui_region_find_active_but 的方法，通过 uiBut 的 active 成员判断其是否为活动，
 * 从而替代对 UI_SELECT 标记的检查。但 active 成员的偏移量在多个版本中变化巨大，获取比较困难。
 *
 * 第三方案：通过 Blender 自带的 .pdb 文件，用 PDBView 等程序找到 ui_region_find_active_but 的
 * 偏移量，然后通过模块基地址+偏移量，获取函数的内存地址，然后调用该函数。（...知识所限，未能成功调用）
 *
 */

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
// uiPopupBlockHandle.region: ARegion *
static size_t offset_uiPopupBlockHandle__region = UNKNOWN;

// 文件：source\blender\makesdna\DNA_screen_types.h
// ARegion.uiblocks: ListBase<uiBlock>
static size_t offset_ARegion__uiblocks = UNKNOWN;

// 文件：source\blender\editors\interface\interface_intern.hh
// uiBlock.buttons: uiBut *
static size_t offset_uiBlock__buttons = UNKNOWN;

// 文件：source\blender\editors\interface\interface_intern.hh
// uiBut.flag: int  -->  UI_SELECT、UI_HOVER、...
static size_t offset_uiBut__flag = UNKNOWN;
// uiBut.type: eButType  -->  UI_BTYPE_TEXT...
static size_t offset_uiBut__type;

// 文件：source\blender\editors\interface\interface_intern.hh
static int UI_SELECT = UNKNOWN;

// 文件：source\blender\editors\include\UI_interface.h
// 文件：source\blender\editors\include\UI_interface_c.hh (4.0.0)
static int UI_BTYPE_TEXT = UNKNOWN;
static int UI_BTYPE_NUM = UNKNOWN;
static int UI_BTYPE_SEARCH_MENU = UNKNOWN;

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
    printx(D_IME, CCFR "wmWindow_is_but_active");
    // 获取窗口模态处理器链表中的第一个节点
    size_t addr_handler = GET_VALUE(size_t, wm_pointer,
                                    offset_wmWindow__modalhandlers + offset_ListBase__first);
    if (addr_handler)
    {
        // 获取模态处理器类型
        int handler_type = GET_VALUE(int, addr_handler,
                                     offset_wmEventHandler__type);
        printx(D_IME, CCFR "\thandler_type: %d, target: %d",
               handler_type, WM_HANDLER_TYPE_UI);
        if (handler_type == WM_HANDLER_TYPE_UI)
        {
            size_t handle_fn = GET_VALUE(size_t, addr_handler,
                                         offset_wmEventHandler__handle_fn);
            size_t remove_fn = GET_VALUE(size_t, addr_handler,
                                         offset_wmEventHandler__remove_fn);
            size_t user_data = GET_VALUE(size_t, addr_handler,
                                         offset_wmEventHandler__user_data);
            printx(D_IME, CCFR "\thandle_fn: %zu", handle_fn);
            printx(D_IME, CCFR "\tremove_fn: %zu", remove_fn);
            printx(D_IME, CCFR "\tuser_data: %zu", user_data);
            if (user_data)
            {
                size_t user_data_len = GET_VALUE(size_t, user_data, -sizeof(size_t));

                printx(D_IME, CCFR "\tuser_data_len: %zu, target: but(%zu), pop(%zu)", user_data_len,
                       sizeof_uiHandleButtonData, sizeof_uiPopupBlockHandle);

                // 检查是否激活普通区块中的输入框
                if (handle_fn && !remove_fn && user_data_len == sizeof_uiHandleButtonData)
                {
                    return true;
                }

                // 检查是否激活临时区块中的输入框（即弹出菜单或面板）
                if (handle_fn && remove_fn && user_data_len == sizeof_uiPopupBlockHandle)
                {
                    printx(D_IME, CCFR "\t??? input field on popup ???");
                    size_t addr_region = GET_VALUE(size_t, user_data, offset_uiPopupBlockHandle__region);
                    printx(D_IME, CCFR "\taddr_region: %zu", addr_region);

                    // 遍历 blocks
                    size_t addr_uiblocks = GEN_ADDR(addr_region, offset_ARegion__uiblocks);
                    printx(D_IME, CCFR "\taddr_uiblocks: %zu (offset %zu)", addr_uiblocks, offset_ARegion__uiblocks);
                    for (size_t addr_uiBlock = GET_VALUE(size_t, addr_uiblocks, offset_ListBase__first);
                         addr_uiBlock != 0;
                         addr_uiBlock = GET_VALUE(size_t, addr_uiBlock, offset_Link__next))
                    {
                        printx(D_IME, CCFR "\taddr_uiBlock: %zu", addr_uiBlock);

                        // 遍历 buttons
                        size_t addr_buttons = GEN_ADDR(addr_uiBlock, offset_uiBlock__buttons);
                        printx(D_IME, CCFR "\taddr_buttons: %zu (offset %zu)", addr_buttons, offset_uiBlock__buttons);
                        for (size_t addr_uiBut = GET_VALUE(size_t, addr_buttons, offset_ListBase__first);
                             addr_uiBut != 0;
                             addr_uiBut = GET_VALUE(size_t, addr_uiBut, offset_Link__next))
                        {
                            printx(D_IME, CCFR "\taddr_uiBut: %zu", addr_uiBut);

                            int uiBut_flag = GET_VALUE(int, addr_uiBut, offset_uiBut__flag);
                            int uiBut_type = GET_VALUE(int, addr_uiBut, offset_uiBut__type);

                            printx(D_IME, CCFR "\tuiBut_flag: %x, %s", uiBut_flag,
                                   (uiBut_flag & UI_SELECT) ? "True" : "False");
                            printx(D_IME, CCFR "\tuiBut_type: %x, %s", uiBut_type,
                                   (uiBut_type == UI_BTYPE_TEXT || uiBut_type == UI_BTYPE_NUM ||
                                    uiBut_type == UI_BTYPE_SEARCH_MENU)
                                       ? "True"
                                       : "False");

                            if ((uiBut_flag & UI_SELECT) &&
                                (uiBut_type == UI_BTYPE_TEXT || uiBut_type == UI_BTYPE_NUM ||
                                 uiBut_type == UI_BTYPE_SEARCH_MENU))
                            {
                                return true;
                            }
                        }
                    }
                }
            }
        }
    }

    return false;
}

extern __declspec(dllexport) bool wmWindow_is_pop_active(void *wm_pointer)
{
    printx(D_IME, CCFR "wmWindow_is_pop_active");
    // 获取窗口模态处理器链表中的第一个节点
    size_t addr_handler = GET_VALUE(size_t, wm_pointer,
                                    offset_wmWindow__modalhandlers + offset_ListBase__first);
    if (addr_handler)
    {
        // 获取模态处理器类型
        int handler_type = GET_VALUE(int, addr_handler,
                                     offset_wmEventHandler__type);
        printx(D_IME, CCFR "\thandler_type: %d, target: %d",
               handler_type, WM_HANDLER_TYPE_UI);
        if (handler_type == WM_HANDLER_TYPE_UI)
        {
            size_t handle_fn = GET_VALUE(size_t, addr_handler,
                                         offset_wmEventHandler__handle_fn);
            size_t remove_fn = GET_VALUE(size_t, addr_handler,
                                         offset_wmEventHandler__remove_fn);
            size_t user_data = GET_VALUE(size_t, addr_handler,
                                         offset_wmEventHandler__user_data);
            printx(D_IME, CCFR "\thandle_fn: %zu", handle_fn);
            printx(D_IME, CCFR "\tremove_fn: %zu", remove_fn);
            printx(D_IME, CCFR "\tuser_data: %zu", user_data);
            if (handle_fn && remove_fn && user_data)
            {
                size_t user_data_len = GET_VALUE(size_t, user_data, -sizeof(size_t));
                printx(D_IME, CCFR "\tuser_data_len: %zu, target: but(%zu), pop(%zu)", user_data_len,
                       sizeof_uiHandleButtonData, sizeof_uiPopupBlockHandle);
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
    size_t p = GET_VALUE(size_t, wm_pointer, offset_wmWindow__workspace_hook);
    size_t p_workspace = GET_VALUE(size_t, p, offset_WorkSpaceInstanceHook__active);
    if (p_workspace)
    {
        size_t p_layout = GET_VALUE(size_t, p, offset_WorkSpaceInstanceHook__act_layout);
        size_t p_screen = GET_VALUE(size_t, p_layout, offset_WorkSpaceLayout__screen);
        return (void *)p_screen;
    }
    return NULL;
}

extern __declspec(dllexport) void *wmWindow_active_region_get(void *wm_pointer)
{
    size_t p_screen = (size_t)wmWindow_active_screen_get(wm_pointer);
    if (p_screen)
    {
        size_t p_region = GET_VALUE(size_t, p_screen, offset_bScreen__active_region);
        return (void *)p_region;
    }
    return NULL;
}

static void blender_data_init_wmWindow()
{
    // 无需区分版本
    WM_HANDLER_TYPE_UI = 2;

    // 无需区分版本（当前无使用）
    WM_HANDLER_BLOCKING = 1;
    WM_HANDLER_ACCEPT_DBL_CLICK = 2;
    WM_HANDLER_DO_FREE = 128;

    // ----- DNA 类型 wmWindow

    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V4
    {
        offset_wmWindow__workspace_hook = 128;
        offset_wmWindow__modalhandlers = 304;
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, Z)) || // V3
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

    // ----- DNA 类型 ARegion

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0)) || // V2
             (VER_GTE(3, 6, 0) && VER_LTE(3, 6, 9)))   // V2
    {
        offset_ARegion__uiblocks = 240;
    }
    else if ((VER_GTE(3, 0, 0) && VER_LTE(3, 5, Z))) //// V1
    {
        offset_ARegion__uiblocks = 232;
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
             (VER_GTE(4, 0, 0) && VER_LTE(4, 0, Z)) || // V2
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
        offset_uiPopupBlockHandle__region = 0;
    }
    else if ((VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9))) // V1
    {
        sizeof_uiPopupBlockHandle = 264;
        offset_uiPopupBlockHandle__region = 0;
    }

    // ----- 非 DNA 类型 uiBlock

    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0)) || // V5
             (VER_GTE(4, 0, 0) && VER_LTE(4, 0, Z)) || // V4
             (VER_GTE(3, 5, 0) && VER_LTE(3, 6, 9)) || // V3
             (VER_GTE(3, 4, 0) && VER_LTE(3, 4, Z)) || // V2
             (VER_GTE(3, 0, 0) && VER_LTE(3, 3, Z)))   // V1
    {
        offset_uiBlock__buttons = 16;
    }

    // ----- 非 DNA 类型 uiBut

    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0)) || // V7
             (VER_GTE(4, 0, 0) && VER_LTE(4, 0, Z)))   // V6
    {
        offset_uiBut__flag = 24;
        offset_uiBut__type = 36;
    }
    else if ((VER_GTE(3, 4, 0) && VER_LTE(3, 6, 9)) || // V5
             (VER_GTE(3, 3, 0) && VER_LTE(3, 3, Z)) || // V4
             (VER_GTE(3, 2, 0) && VER_LTE(3, 2, Z)) || // V3
             (VER_GTE(3, 1, 0) && VER_LTE(3, 1, Z)) || // V2
             (VER_GTE(3, 0, 0) && VER_LTE(3, 0, Z)))   // V1
    {
        offset_uiBut__flag = 24;
        offset_uiBut__type = 32;
    }

    /**/ if ((VER_GTE(4, 0, 0) && VER_LTE(4, 1, 0)) ||
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))
    {
        // 当前需求无需区分版本

        UI_SELECT = (1 << 0);             // 十六进制：1
        UI_BTYPE_TEXT = (3 << 9);         // 十六进制：600
        UI_BTYPE_NUM = (6 << 9);          // 十六进制：C00
        UI_BTYPE_SEARCH_MENU = (41 << 9); // 十六进制：5200
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
        size_t p_runtime = GET_VALUE(size_t, SpaceText, offset_SpaceText__runtime);
        if (p_runtime)
        {
            int value = GET_VALUE(int, p_runtime, offset_SpaceText_Runtime__lheight_px);
            return value;
        }
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        size_t runtime = GEN_ADDR(SpaceText, offset_SpaceText__runtime);
        int value = GET_VALUE(int, runtime, offset_SpaceText_Runtime__lheight_px);
        return value;
    }

    return 1000;
}

extern __declspec(dllexport) int SpaceText_cwidth_px_get(void *SpaceText)
{
    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V2
    {
        size_t p_runtime = GET_VALUE(size_t, SpaceText, offset_SpaceText__runtime);
        if (p_runtime)
        {
            int value = GET_VALUE(int, p_runtime, offset_SpaceText_Runtime__cwidth_px);
            return value;
        }
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        size_t runtime = GEN_ADDR(SpaceText, offset_SpaceText__runtime);
        int value = GET_VALUE(int, runtime, offset_SpaceText_Runtime__cwidth_px);
        return value;
    }

    return 1000;
}

extern __declspec(dllexport) int SpaceText_line_number_display_digits_get(void *SpaceText)
{
    /**/ if ((VER_GTE(4, 1, 0) && VER_LTE(4, 1, 0))) //// V2
    {
        size_t p_runtime = GET_VALUE(size_t, SpaceText, offset_SpaceText__runtime);
        if (p_runtime)
        {
            int value = GET_VALUE(int, p_runtime, offset_SpaceText_Runtime__line_number_display_digits);
            return value;
        }
    }
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, 2)) || // V1
             (VER_GTE(3, 0, 0) && VER_LTE(3, 6, 9)))   // V1
    {
        size_t runtime = GEN_ADDR(SpaceText, offset_SpaceText__runtime);
        int value = GET_VALUE(int, runtime, offset_SpaceText_Runtime__line_number_display_digits);
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
    else if ((VER_GTE(4, 0, 0) && VER_LTE(4, 0, Z)) || // V1
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
    // 无需区分版本
    offset_ListBase__first = 0;
    offset_ListBase__last = 8;
    offset_Link__next = 0;
    offset_Link__prev = 8;

    blender_data_init_wmWindow();

    blender_data_init_SpaceText();
}
