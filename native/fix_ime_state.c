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
#include "fix_ime.h"
#include "fix_ime_state.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序内功能

extern bool data_use_fix_ime_state = false;

extern void fix_ime_state_with_mouse_event(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    HIMC himc = ImmGetContext(hWnd);
    if (himc != NULL)
    {
        DEBUGH(D_IME, "自动停用输入法");
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
            DEBUGH(D_IME, "自动启用输入法");
            ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
            ImmReleaseContext(hWnd, himc);
        }
    }
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序外功能

extern __declspec(dllexport) bool use_fix_ime_state(bool enable)
{
    DEBUGH(D_IME, "use_fix_ime_state: %s", enable ? "True" : "False");

    data_use_fix_ime_state = enable;

    return true; // 返回的是否执行成功
}
