#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <windows.h>
#include <imm.h>
#pragma comment(lib, "Imm32.lib")
// Self
#include "main.h"
#include "utils.h"
#include "fix_ime_state.h"
#include "hook.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  内部功能

HHOOK hHook_window = NULL;
HHOOK hHook_mouse = NULL;
HHOOK hHook_keyboard = NULL;

bool is_blender_window(HWND hWnd);

LRESULT CALLBACK CallWndProc(int nCode, WPARAM wParam_, LPARAM lParam_);
LRESULT CALLBACK MouseProc(int nCode, WPARAM wParam_, LPARAM lParam_);
LRESULT CALLBACK KeyboardProc(int nCode, WPARAM wParam_, LPARAM lParam_);

// 用于记录窗口信息的缓存的"链表"，仅用于提升窗口类型判断的效率
typedef struct tag_node_WindowData
{
    struct tag_node_WindowData *next; // 节点指针
    HWND handle;                      // 窗口句柄
    bool is_blender_window;           // 是否为 Blender 自身的窗口
} WindowData;
typedef struct tag_head_WindowData
{
    int count;
    WindowData *first;
} WindowDataHead;
WindowData *window_datas = NULL;
WindowDataHead window_datas_head = {.count = 0, .first = NULL};
WindowData *window_datas_for_each(WindowData **window);
WindowData *window_datas_add(WindowData *window);
bool window_datas_remove(WindowData *window);
bool window_datas_clean();

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  外部功能

extern __declspec(dllexport) bool use_hook_debug(bool enable)
{
    data_use_hook_debug = enable;

    return true; // 返回的是否执行成功
}

extern __declspec(dllexport) bool use_hook(bool enable)
{
    if (enable)
    {
        DEBUGI(D_HOK, "startup...");

        // 必须使用 WH_MOUSE 和 WH_KEYBOARD 监听鼠标和键盘消息，用 WH_CALLWNDPROC 无法获取这些消息，原因未知

        hHook_window = SetWindowsHookEx(WH_CALLWNDPROC, CallWndProc, NULL, thread_id);
        if (hHook_window == NULL)
        {
            DEBUGI(D_HOK, "SetWindowsHookEx WH_CALLWNDPROC failed");

            DEBUGI(D_HOK, "startup...failed");

            return false;
        }

        hHook_mouse = SetWindowsHookEx(WH_MOUSE, MouseProc, NULL, thread_id);
        if (hHook_mouse == NULL)
        {
            DEBUGI(D_HOK, "SetWindowsHookEx WH_MOUSE failed");

            DEBUGI(D_HOK, "startup...failed");

            return false;
        }

        hHook_keyboard = SetWindowsHookEx(WH_KEYBOARD, KeyboardProc, NULL, thread_id);
        if (hHook_keyboard == NULL)
        {
            DEBUGI(D_HOK, "SetWindowsHookEx WH_KEYBOARD failed");

            DEBUGI(D_HOK, "startup...failed");

            return false;
        }

        data_use_hook = true;

        DEBUGI(D_HOK, "startup...finish");

        return true;
    }
    else
    {
        DEBUGI(D_HOK, "shutdown...");

        if (hHook_window != NULL)
        {
            BOOL bResult = UnhookWindowsHookEx(hHook_window);
            if (bResult == FALSE)
            {
                DEBUGI(D_HOK, "UnhookWindowsHookEx hHook_window failed");

                DEBUGI(D_HOK, "shutdown...failed");
            }
        }

        if (hHook_mouse != NULL)
        {
            BOOL bResult = UnhookWindowsHookEx(hHook_mouse);
            if (bResult == FALSE)
            {
                DEBUGI(D_HOK, "UnhookWindowsHookEx hHook_mouse failed");

                DEBUGI(D_HOK, "shutdown...failed");
            }
        }

        if (hHook_keyboard != NULL)
        {
            BOOL bResult = UnhookWindowsHookEx(hHook_keyboard);
            if (bResult == FALSE)
            {
                DEBUGI(D_HOK, "UnhookWindowsHookEx hHook_keyboard failed");

                DEBUGI(D_HOK, "shutdown...failed");
            }
        }

        hHook_mouse = NULL;

        hHook_keyboard = NULL;

        data_use_hook = false;

        window_datas_clean();

        DEBUGI(D_HOK, "shutdown...finish");

        return true;
    }
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  全局和内部全局功能

extern bool data_use_hook_debug = true;

extern bool data_use_hook = false;

bool is_blender_window(HWND hWnd)
{
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
    if (!found)
    {
        window = (WindowData *)malloc(sizeof(WindowData));
        memset(window, 0, sizeof(WindowData));
        window->next = NULL;
        window->handle = hWnd;

        WCHAR class_name[100] = {0};
        GetClassName(hWnd, (LPWSTR)&class_name, 100);
        if (lstrcmp((LPWSTR)&class_name, TEXT("GHOST_WindowClass")) == 0)
        {
            window->is_blender_window = true;
        }
        else
        {
            window->is_blender_window = false;
        }

        window_datas_add(window);
    }

    DEBUGI(D_IME, "is_blender_window: %d, %p", window->is_blender_window, hWnd);

    return window->is_blender_window;
}

LRESULT CALLBACK CallWndProc(int nCode, WPARAM wParam_, LPARAM lParam_)
{
    if (nCode < 0)
    {
        return CallNextHookEx(NULL, nCode, wParam_, lParam_);
    }

    CWPSTRUCT *data = (CWPSTRUCT *)lParam_;

    HWND hWnd = data->hwnd;
    UINT uMsg = data->message;
    WPARAM wParam = data->wParam;
    LPARAM lParam = data->lParam;
    switch (uMsg)
    {
    case WM_KILLFOCUS:
    {
        DEBUGI(D_IME, "WM_KILLFOCUS: %p", hWnd);
        if (data_use_fix_ime_state && is_blender_window(hWnd))
        {
            fix_ime_state_with_mouse_event(hWnd, uMsg, (WPARAM)NULL, (LPARAM)NULL);
        }
        break;
    }
    case WM_DESTROY:
    {
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
            window_datas_remove(window);
        }
        break;
    }
    }

    return CallNextHookEx(NULL, nCode, wParam_, lParam_);
}

LRESULT CALLBACK MouseProc(int nCode, WPARAM wParam_, LPARAM lParam_)
{
    if (nCode < 0)
    {
        return CallNextHookEx(NULL, nCode, wParam_, lParam_);
    }

    MOUSEHOOKSTRUCT *data = (MOUSEHOOKSTRUCT *)lParam_;

    HWND hWnd = data->hwnd;
    UINT uMsg = wParam_;

    switch (uMsg)
    {
    case WM_LBUTTONDOWN:
    case WM_RBUTTONDOWN:
    // case WM_MBUTTONDOWN: // 中间和X键似乎不会触发输入框退出
    // case WM_XBUTTONDOWN:
    {
        DEBUGI(D_IME, "WM_#BUTTONDOWN: %p", hWnd);
        if (data_use_fix_ime_state && is_blender_window(hWnd))
        {
            fix_ime_state_with_mouse_event(hWnd, uMsg, (WPARAM)NULL, (LPARAM)NULL);
        }
        break;
    }
    }

    return CallNextHookEx(NULL, nCode, wParam_, lParam_);
}

LRESULT CALLBACK KeyboardProc(int nCode, WPARAM wParam_, LPARAM lParam_)
{
    if (nCode < 0)
    {
        return CallNextHookEx(NULL, nCode, wParam_, lParam_);
    }

    HWND hWnd = GetActiveWindow();
    if ((HIWORD(lParam_) & KF_UP) == 0) // WM_KEYDOWN
    {
        DEBUGI(D_IME, "WM_KEYDOWN: %p, %d", hWnd, (int)wParam_);
        if (data_use_fix_ime_state && is_blender_window(hWnd))
        {
            fix_ime_state_with_key_event(hWnd, WM_KEYDOWN, wParam_, lParam_);
        }
    }

    return CallNextHookEx(NULL, nCode, wParam_, lParam_);
}

WindowData *window_datas_for_each(WindowData **window)
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

WindowData *window_datas_add(WindowData *window)
{
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

bool window_datas_remove(WindowData *window)
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

bool window_datas_clean()
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
