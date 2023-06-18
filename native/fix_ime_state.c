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

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  对外功能

extern __declspec(dllexport) bool use_fix_ime_state_debug(bool enable)
{
    data_use_fix_ime_state_debug = enable;

    return true; // 返回的是否执行成功
}

extern __declspec(dllexport) bool use_fix_ime_state(bool enable)
{
    DEBUGI(D_IME, "use_fix_ime_state: %s", enable ? "True" : "False");

    data_use_fix_ime_state = enable;

    return true; // 返回的是否执行成功
}

extern __declspec(dllexport) bool change_ime_state(bool enable)
{
    DEBUGI(D_IME, "change_ime_state: %s", enable ? "True" : "False");

    // 由于无法准确获取哪个窗口，只能默认来自于活动窗口
    HWND hWnd = GetActiveWindow();

    HIMC himc = ImmGetContext(hWnd);

    if (enable)
    {
        // 这部分代码，实际上不会使用到
        if (himc == NULL)
        {
            ImmAssociateContextEx(hWnd, NULL, IACE_DEFAULT);
            ImmReleaseContext(hWnd, himc);
        }
    }
    else
    {
        if (himc != NULL)
        {
            DEBUGI(D_IME, "disable IME in change_ime_state：%p", hWnd);
            ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
            ImmReleaseContext(hWnd, himc);
        }
    }

    return true; // 返回的是否执行成功
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  全局功能

extern bool data_use_fix_ime_state_debug = true;

extern bool data_use_fix_ime_state = false;

extern void fix_ime_state_with_mouse_event(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    HIMC himc = ImmGetContext(hWnd);
    if (himc != NULL)
    {
        DEBUGI(D_IME, "auto disable IME in mouse and focus event");
        ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
        ImmReleaseContext(hWnd, himc);
    }
}

extern void fix_ime_state_with_key_event(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    WORD vkCode = LOWORD(wParam);
    if (vkCode == VK_ESCAPE || vkCode == VK_RETURN || vkCode == VK_TAB)
    {
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            DEBUGI(D_IME, "auto disable IME in key event");
            ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
            ImmReleaseContext(hWnd, himc);
        }
    }
}
