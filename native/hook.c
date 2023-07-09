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
//  标记  文件内功能

bool window_wrap(HWND hWnd);
bool window_unwrap(HWND hWnd);
BOOL CALLBACK EnumWindowsProc_first(HWND hWnd, LPARAM lParam);
BOOL CALLBACK EnumWindowsProc_new(HWND hWnd, LPARAM lParam);
LRESULT Subclassproc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData);

bool window_wrap(HWND hWnd)
{
    // 安装子类化窗口过程（仅针对 Blender 窗口）

    WCHAR class_name[100] = {0};
    GetClassName(hWnd, (LPWSTR)&class_name, 100);
    if (lstrcmp((LPWSTR)&class_name, TEXT("GHOST_WindowClass")) == 0)
    {
        WindowData *window = NULL;
        window = (WindowData *)malloc(sizeof(WindowData));
        memset(window, 0, sizeof(WindowData));

        window->handle = hWnd;

        if (D_HOK)
        {
            WCHAR _class_name[100] = {0};
            GetClassName(hWnd, (LPWSTR)&_class_name, 100);
            DEBUGH(D_HOK, "捕获窗口：%p [窗口类名称：%ls]", hWnd, &_class_name);
            GetWindowText(hWnd, (LPWSTR)&_class_name, 100);
            DEBUGI(D_HOK, "窗口名称：\"%ls\"", &_class_name);
        }

        /**
         * source\blender\windowmanager\intern\wm_window.c
         *      wm_window_ghostwindow_add()
         * intern\ghost\intern\GHOST_WindowWin32.cpp
         *      GHOST_WindowWin32::GHOST_WindowWin32()
         * 官方将自己的 GHOST_WindowWin32 对象的指针存储到窗口的用户数据中，
         * 而 Window 对象的第一个成员为 GHOST_WindowWin32 对象的指针，
         * 因此可以根据这些获取到指针和窗口的对应关系。
         * 注意：刚创建的窗口无法获取该数据，需要在 WM_SHOWWINDOW 时获取
         **/
        window->gw_pointer = (void *)GetWindowLongPtr(hWnd, GWLP_USERDATA);
        DEBUGH(D_HOK, "GW 指针：%p", window->gw_pointer);

        BOOL result_b = SetWindowSubclass(hWnd, Subclassproc, (UINT_PTR)hWnd, (DWORD_PTR)window);
        if (!result_b)
        {
            ERRORP("捕获窗口失败：SetWindowSubclass");
            free(window);
        }
        else
        {
            window_datas_add(window);
            return true;
        }
    }
    return false;
}

bool window_unwrap(HWND hWnd)
{
    // 卸载子类化窗口过程

    WindowData *window = NULL;
    bool found = false;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->handle == hWnd)
        {
            found = true;
            break;
        }
    }
    if (found)
    {
        if (D_HOK)
        {
            WCHAR _class_name[100] = {0};
            GetClassName(hWnd, (LPWSTR)&_class_name, 100);
            DEBUGH(D_HOK, "释放窗口：%p [窗口类名称：%ls]", hWnd, &_class_name);
            GetWindowText(hWnd, (LPWSTR)&_class_name, 100);
            DEBUGI(D_HOK, "窗口名称：\"%ls\"", &_class_name);
        }

        BOOL result_b = RemoveWindowSubclass(hWnd, Subclassproc, (UINT_PTR)hWnd);
        if (!result_b)
        {
            ERRORP("释放窗口失败：RemoveWindowSubclass");
        }

        window_datas_remove(window); // 无论怎样都移除窗口数据
        return true;
    }
    return false;
}

BOOL CALLBACK EnumWindowsProc_first(HWND hWnd, LPARAM lParam)
{
    DWORD window_processid = 0;
    GetWindowThreadProcessId(hWnd, &window_processid);
    if (window_processid == process_id)
    {
        window_wrap(hWnd);
    }
    return TRUE;
}

BOOL CALLBACK EnumWindowsProc_new(HWND hWnd, LPARAM lParam)
{
    DWORD window_processid = 0;
    GetWindowThreadProcessId(hWnd, &window_processid);
    if (window_processid == process_id)
    {
        void *gw_pointer = (void *)lParam;
        void *user_data = (void *)GetWindowLongPtr(hWnd, GWLP_USERDATA);
        if (user_data == gw_pointer)
        {
            if (window_wrap(hWnd))
            {
                return false; // 已找到窗口，停止枚举
            }
        }
    }
    return true;
}

LRESULT Subclassproc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData)
{
    WindowData *window = (WindowData *)dwRefData;

    switch (uMsg)
    {
    case WM_SHOWWINDOW:
    {
        if (window->gw_pointer == NULL)
        {
            window->gw_pointer = (void *)GetWindowLongPtr(hWnd, GWLP_USERDATA);
            DEBUGH(D_HOK, "GW 指针：%p [hwnd: %p]", window->gw_pointer, hWnd);
        }
        break;
    }
    case WM_DESTROY:
    {
        window_unwrap(hWnd);
        break;
    }
    // ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
    //  标记  输入法相关
    case WM_LBUTTONDOWN:
    case WM_RBUTTONDOWN:
    case WM_MBUTTONDOWN:
    case WM_XBUTTONDOWN:
    case WM_KILLFOCUS:
    {
        // if (D_IME)
        // {
        //     if (uMsg == WM_KILLFOCUS)
        //     {
        //         DEBUGI(D_IME, "WM_KILLFOCUS：%p", hWnd);
        //     }
        //     else
        //     {
        //         DEBUGI(D_IME, "WM_#BUTTONDOWN：%p", hWnd);
        //     }
        // }
        if (data_use_fix_ime_input) // 已经启用【修复输入法输入】特性
        {
            if (himc_enabled) // 已经启用自定义输入流程
            {
                fix_ime_input_WM_KILLFOCUS(hWnd, uMsg, wParam, lParam, window);
            }
            else if (data_use_fix_ime_state)
            {
                fix_ime_state_with_mouse_event(hWnd, uMsg, wParam, lParam);
            }
        }
        else if (data_use_fix_ime_state)
        {
            fix_ime_state_with_mouse_event(hWnd, uMsg, wParam, lParam);
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
        // DEBUGI(D_IME, "WM_IME_NOTIFY：%x", command);
        break;
    }
    case WM_IME_SETCONTEXT:
    {
        // 目前没用
        // BOOL fSet = (BOOL)wParam;
        // DWORD iShow = (DWORD)lParam;
        // DEBUGI(D_IME, "WM_IME_SETCONTEXT: %s, %x", fSet ? "True" : "False", iShow);
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
//  标记  程序内功能

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

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序外功能

extern __declspec(dllexport) bool use_hook_debug(bool enable)
{
    data_use_hook_debug = enable;

    return true; // 返回的是否执行成功
}

extern __declspec(dllexport) bool use_hook(bool enable)
{
    if (enable)
    {
        DEBUGI(D_HOK, "hook startup...");

        HRESULT result_b;

        // 初始化窗口数据
        DEBUGI(D_HOK, "初始化数据...");
        result_b = EnumWindows(EnumWindowsProc_first, (LPARAM)NULL);
        if (!result_b)
        {
            DEBUGI(D_HOK, "初始化数据...失败：EnumWindows");

            DEBUGI(D_HOK, "hook startup...failed");

            return false;
        }
        DEBUGI(D_HOK, "初始化数据...完成");

        data_use_hook = true;

        DEBUGI(D_HOK, "hook startup...finish");

        return true;
    }
    else
    {
        bool failed = false;

        DEBUGI(D_HOK, "hook shutdown...");

        DEBUGI(D_HOK, "清理数据...[窗口个数：%d]", window_datas_head.count);

        WindowData *window = NULL;
        while (window_datas_head.count != 0)
        {
            // window_unwrap() 会删除窗口数据，所以不能用遍历
            window = window_datas_head.first;
            window_unwrap(window->handle);
        }

        window_datas_clean();

        DEBUGI(D_HOK, "清理数据...完成");

        data_use_hook = false;

        DEBUGI(D_HOK, "hook shutdown...finish");

        return true;
    }
}

extern __declspec(dllexport) bool window_associate_pointer(void *wm_pointer)
{
    static bool invoke_after_enum = false;

    if (wm_pointer == NULL)
    {
        return false;
    }

    /**
     * 参考：
     * source\blender\makesdna\DNA_windowmanager_types.h
     *      typedef struct wmWindow
     */
    void *gw_pointer = (void *)*((size_t *)wm_pointer + 2);

    WindowData *window = NULL;
    bool found = false;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->gw_pointer == gw_pointer)
        {
            found = true;
            break;
        }
    }

    if (found)
    {
        DEBUGI(D_HOK, CCBA "窗口关联 [%p]: %p (gw), %p (wm)" CCZ0, window->handle, gw_pointer, wm_pointer);
        window->wm_pointer = wm_pointer;
    }
    else
    {
        EnumWindows(EnumWindowsProc_new, (LPARAM)gw_pointer);
        invoke_after_enum = true;
        window_associate_pointer(wm_pointer);
        invoke_after_enum = false;
    }

    return true;
}

extern __declspec(dllexport) bool window_is_active(void *wm_pointer)
{
    if (wm_pointer == NULL)
    {
        return false;
    }

    WindowData *window = NULL;
    bool found = false;
    while (window_datas_for_each(&window) != NULL)
    {
        // 这里直接使用 wm_pointer，因为必然在 window_associate_pointer 中关联过
        if (window->wm_pointer == wm_pointer)
        {
            found = true;
            break;
        }
    }

    if (found)
    {
        return (GetActiveWindow() == window->handle);
    }

    return false;
}
