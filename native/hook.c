#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <setjmp.h>
// Windows
#include <windows.h>
#include <imm.h>
#pragma comment(lib, "Imm32.lib")
#include <strsafe.h>
#include <commctrl.h>
#pragma comment(lib, "Comctl32.lib")
// Self
#include "main.h"
#include "utils.h"
#include "fix_ime.h"
#include "fix_ime_state.h"
#include "fix_ime_input.h"
#include "hook.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  私有

bool window_wrap_check(HWND hWnd);
bool window_wrap(HWND hWnd);
bool window_unwrap(HWND hWnd);
BOOL CALLBACK EnumThreadWndProc_init(HWND hWnd, LPARAM lParam);
BOOL CALLBACK EnumThreadWndProc_associate(HWND hWnd, LPARAM lParam);
LRESULT Subclassproc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData);

bool window_wrap_check(HWND hWnd)
{
    // 检查目标窗口是否可以捕获

    WindowData *window = get_window_by_handle(hWnd);
    if (window)
    {
        // 已捕获，无需再捕获
        return false;
    }

    WCHAR class_name[100] = {0};
    GetClassName(hWnd, (LPWSTR)&class_name, 100);
    if (lstrcmp((LPWSTR)&class_name, TEXT("GHOST_WindowClass")) != 0)
    {
        // 仅捕获 Blender 自身创建的窗口（主窗口、从窗口）
        return false;
    }

    return true;
}

bool window_wrap(HWND hWnd)
{
    /**
     * 捕获窗口（使用窗口子类化机制）。
     */

    //  注意 ：调用前，必须先调用 window_wrap_check 检查窗口是否可以捕获

    WindowData *window = (WindowData *)malloc(sizeof(WindowData));
    memset(window, 0, sizeof(WindowData));

    if (SetWindowSubclass(hWnd, Subclassproc, (UINT_PTR)hWnd, (DWORD_PTR)window))
    {
        if (D_HOK)
        {
            WCHAR _class_name[100] = {0};
            GetClassName(hWnd, (LPWSTR)&_class_name, 100);
            printx(D_HOK, "捕获窗口：%p [窗口类名称：%ls]", hWnd, &_class_name);
            GetWindowText(hWnd, (LPWSTR)&_class_name, 100);
            printx(D_HOK, "窗口名称：\"%ls\"", &_class_name);
            printx(D_HOK, "GW 指针：%p", window->gw_pointer);
        }

        window->handle = hWnd;

        window->gw_pointer = (void *)GetWindowLongPtr(hWnd, GWLP_USERDATA);

        window_datas_add(window);

        return true;
    }
    else
    {
        printx(D_ERR, CCBR "捕获窗口失败：%p (hw)", hWnd);

        free(window);

        return false;
    }
    return false;
}

bool window_unwrap(HWND hWnd)
{
    // 释放窗口

    WindowData *window = get_window_by_handle(hWnd);
    if (window)
    {
        if (RemoveWindowSubclass(hWnd, Subclassproc, (UINT_PTR)hWnd))
        {
            if (D_HOK)
            {
                WCHAR _class_name[100] = {0};
                GetClassName(hWnd, (LPWSTR)&_class_name, 100);
                printx(D_HOK, "释放窗口：%p [窗口类名称：%ls]", hWnd, &_class_name);
                GetWindowText(hWnd, (LPWSTR)&_class_name, 100);
                printx(D_HOK, "窗口名称：\"%ls\"", &_class_name);
            }
        }
        else
        {
            printx(D_ERR, CCBR "释放窗口失败：%p (hw)", hWnd);
        }

        window_datas_remove(window); // 无论怎样都移除窗口数据

        return true;
    }

    return false;
}

BOOL CALLBACK EnumThreadWndProc_init(HWND hWnd, LPARAM lParam)
{
    if (window_wrap_check(hWnd))
    {
        printx(D_HOK, "从 EnumThreadWndProc_init 捕获窗口");
        window_wrap(hWnd);
    }
    return TRUE;
}

BOOL CALLBACK EnumThreadWndProc_associate(HWND hWnd, LPARAM lParam)
{
    if ((void *)GetWindowLongPtrW(hWnd, GWLP_USERDATA) == (void *)lParam)
    {
        if (window_wrap_check(hWnd))
        {
            printx(D_HOK, "从 EnumThreadWndProc_associate 捕获窗口");
            window_wrap(hWnd);
        }
        return FALSE; // 已找到窗口，停止枚举，捕获是否成功不重要
    }
    return TRUE;
}

LRESULT Subclassproc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData)
{
    WindowData *window = (WindowData *)dwRefData;

    switch (uMsg)
    {
    case WM_DESTROY:
    {
        fix_ime_input_WM_DESTROY(hWnd, uMsg, wParam, lParam, window);
        window_unwrap(hWnd);
        break;
    }
    // ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    //  标记  输入法相关
    case WM_LBUTTONDOWN:
    case WM_RBUTTONDOWN:
    case WM_MBUTTONDOWN:
    case WM_XBUTTONDOWN:
    case WM_NCLBUTTONDOWN:
    case WM_NCRBUTTONDOWN:
    case WM_NCMBUTTONDOWN:
    case WM_NCXBUTTONDOWN:
    {
        if (data_use_fix_ime_input) // 已经启用【使用输入法输入文字】特性
        {
            if (himc_enabled) // 已经在区块中启用输入法
            {
                fix_ime_input_WM_xBUTTONDOWN(hWnd, uMsg, wParam, lParam, window);
            }
            else if (data_use_fix_ime_state && (uMsg == WM_LBUTTONDOWN || uMsg == WM_RBUTTONDOWN))
            {
                fix_ime_state_with_mouse_event(hWnd, uMsg, wParam, lParam);
            }
        }
        else if (data_use_fix_ime_state && (uMsg == WM_LBUTTONDOWN || uMsg == WM_RBUTTONDOWN))
        {
            fix_ime_state_with_mouse_event(hWnd, uMsg, wParam, lParam);
        }
        break;
    }
    case WM_KILLFOCUS:
    {
        if (data_use_fix_ime_input)
        {
            if (himc_enabled)
            {
                fix_ime_input_WM_KILLFOCUS(hWnd, uMsg, wParam, lParam, window);
            }
        }
        break;
    }
    case WM_INPUT:
    {
        if (data_use_fix_ime_input)
        {
            if (himc_enabled)
            {
                if (fix_ime_input_WM_INPUT(hWnd, uMsg, wParam, lParam, window))
                {
                    // 注意 ：自行处理消息，并且对 Blender 屏蔽该消息。
                    return DefWindowProc(hWnd, uMsg, wParam, lParam);
                }
            }
        }
        break;
    }
    case WM_KEYDOWN:
    {
        if (data_use_fix_ime_input)
        {
            if (himc_enabled)
            {
                fix_ime_input_WM_KEYDOWN(hWnd, uMsg, wParam, lParam, window);
            }
            else if (data_use_fix_ime_state)
            {
                fix_ime_state_with_key_event(hWnd, uMsg, wParam, lParam);
            }
        }
        else if (data_use_fix_ime_state)
        {
            fix_ime_state_with_key_event(hWnd, uMsg, wParam, lParam);
        }
        break;
    }
    case WM_KEYUP:
    {
        if (data_use_fix_ime_input)
        {
            if (himc_enabled)
            {
                fix_ime_input_WM_KEYUP(hWnd, uMsg, wParam, lParam, window);
            }
        }
        break;
    }
    case WM_IME_NOTIFY:
    {
        // 目前没用
        // DWORD command = (DWORD)wParam;
        // printx(D_IME, "WM_IME_NOTIFY：%x", command);
        break;
    }
    case WM_IME_SETCONTEXT:
    {
        // 目前没用
        // BOOL fSet = (BOOL)wParam;
        // DWORD iShow = (DWORD)lParam;
        // printx(D_IME, "WM_IME_SETCONTEXT: %s, %x", fSet ? "True" : "False", iShow);
        break;
    }
    case WM_IME_STARTCOMPOSITION:
    {
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            if (himc_enabled)
            {
                fix_ime_input_WM_IME_STARTCOMPOSITION(hWnd, uMsg, wParam, lParam, window);

                ImmReleaseContext(hWnd, himc);
                /**
                 * 屏蔽消息，否则传到 Blender 后，Blender 会更新候选窗口位置，
                 * 导致输入过程中候选窗口跳来跳去。
                 */
                return 0; // 屏蔽消息
            }
            ImmReleaseContext(hWnd, himc);
        }
        break;
    }
    case WM_IME_COMPOSITION:
    {
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            if (himc_enabled)
            {
                fix_ime_input_WM_IME_COMPOSITION(hWnd, uMsg, wParam, lParam, window);

                ImmReleaseContext(hWnd, himc);
                return 0; // 屏蔽消息
            }
            ImmReleaseContext(hWnd, himc);
        }
        break;
    }
    case WM_IME_ENDCOMPOSITION:
    {
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            if (himc_enabled)
            {
                fix_ime_input_WM_IME_ENDCOMPOSITION(hWnd, uMsg, wParam, lParam, window);

                ImmReleaseContext(hWnd, himc);
                return 0; // 屏蔽消息
            }
            ImmReleaseContext(hWnd, himc);
        }
        break;
    }
    }

    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  公共

extern bool data_use_hook_debug = true;

extern bool data_use_hook = false;

extern WindowData *window_datas = NULL;
extern WindowDataHead window_datas_head = {.count = 0, .first = NULL};

extern WindowData *window_datas_for_each(WindowData **window)
{
    if ((*window) == NULL)
    {
        return (*window) = window_datas_head.first;
    }
    else
    {
        if ((*window)->next == NULL)
        {
            return NULL;
        }
        else
        {
            return (*window) = (*window)->next;
        }
    }
}

extern WindowData *window_datas_add(WindowData *window)
{
    window->next = NULL;
    if (window_datas_head.first == NULL)
    {
        window_datas_head.first = window;
    }
    else
    {
        WindowData *last = window_datas_head.first;
        while (last->next != NULL)
        {
            last = last->next;
        }
        last->next = window;
    }
    window_datas_head.count += 1;
    return window;
}

extern bool window_datas_remove(WindowData *window)
{
    WindowData *prev = NULL;
    WindowData *curr = window_datas_head.first;
    while (curr != NULL)
    {
        if (curr == window)
        {
            if (prev == NULL)
            {
                window_datas_head.first = curr->next;
            }
            else
            {
                prev->next = curr->next;
            }
            window_datas_head.count -= 1;
            free(curr);
            return true;
        }
        else
        {
            prev = curr;
            curr = curr->next;
        }
    }
    return false;
}

extern bool window_datas_clean()
{
    WindowData *curr = window_datas_head.first;
    WindowData *next = NULL;
    while (curr != NULL)
    {
        next = curr->next;
        free(curr);
        curr = next;
    }
    window_datas_head.count = 0;
    window_datas_head.first = NULL;
    return true;
}

extern WindowData *get_window_by_handle(HWND handle)
{
    WindowData *window = NULL;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->handle == handle)
        {
            return window;
        }
    }
    return NULL;
}

extern WindowData *get_window_by_gw(void *gw_pointer)
{
    WindowData *window = NULL;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->gw_pointer == gw_pointer)
        {
            return window;
        }
    }
    return NULL;
}

extern WindowData *get_window_by_wm(void *wm_pointer)
{
    WindowData *window = NULL;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->wm_pointer == wm_pointer)
        {
            return window;
        }
    }
    return NULL;
}

extern inline void *get_gw_pointer(void *wm_pointer)
{
    /**
     * 参考：
     * source\blender\makesdna\DNA_windowmanager_types.h
     *      typedef struct wmWindow
     */
    return (void *)*((size_t *)wm_pointer + 2);
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_hook_debug(bool enable)
{
    data_use_hook_debug = enable;

    return data_use_hook_debug;
}

extern __declspec(dllexport) bool use_hook(bool enable)
{
    if (enable)
    {
        printx(D_HOK, "hook startup...");

        HRESULT result_b;

        // 捕获已经存在的窗口
        printx(D_ERR, "捕获窗口...");
        EnumThreadWindows(thread_id, EnumThreadWndProc_init, (LPARAM)NULL);

        data_use_hook = true;

        printx(D_HOK, "hook startup...finish");
    }
    else
    {
        bool failed = false;

        printx(D_HOK, "hook shutdown...");

        printx(D_HOK, "释放窗口...[窗口个数：%d]", window_datas_head.count);

        WindowData *window = NULL;
        while (window_datas_head.count != 0)
        {
            // window_unwrap() 会删除窗口数据，所以不能用遍历
            window = window_datas_head.first;
            window_unwrap(window->handle);
        }

        window_datas_clean();

        data_use_hook = false;

        printx(D_HOK, "hook shutdown...finish");
    }

    return data_use_hook;
}

extern __declspec(dllexport) bool window_associate(void *wm_pointer)
{
    static bool invoke_after_enum = false;

    if (wm_pointer == NULL)
    {
        return false;
    }

    // 必须使用 gw_pointer，因为窗口捕获时只能获取 gw_pointer，其 wm_pointer 必然为 NULL
    void *gw_pointer = get_gw_pointer(wm_pointer);

    WindowData *window = get_window_by_gw(gw_pointer);

    if (window)
    {
        window->wm_pointer = wm_pointer;
        printx(D_HOK, CCBA "窗口关联 [%p (HWND)]: %p (wm), %p (gw)", window->handle, wm_pointer, gw_pointer);
        return true;
    }
    else if (!invoke_after_enum)
    {
        EnumThreadWindows(thread_id, EnumThreadWndProc_associate, (LPARAM)gw_pointer);
        invoke_after_enum = true;
        bool success = window_associate(wm_pointer);
        invoke_after_enum = false;
        if (!success)
        {
            printx(D_HOK, CCBR "窗口关联失败: %p (wm), %p (gw)", wm_pointer, gw_pointer);
        }
        return success;
    }

    return false;
}

extern __declspec(dllexport) bool window_is_active(void *wm_pointer)
{
    if (wm_pointer == NULL)
    {
        return false;
    }
    WindowData *window = get_window_by_wm(wm_pointer);
    if (window)
    {
        return (window->handle == GetActiveWindow());
    }
    return false;
}

extern __declspec(dllexport) bool window_is_mouse_capture(void *wm_pointer)
{
    if (wm_pointer == NULL)
    {
        return false;
    }
    WindowData *window = get_window_by_wm(wm_pointer);
    if (window)
    {
        return (window->handle == GetCapture());
    }
    return false;
}
