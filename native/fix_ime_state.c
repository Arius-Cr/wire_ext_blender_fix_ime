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
//  标记  公共

extern bool data_use_fix_ime_state = false;

extern void fix_ime_state_with_mouse_event(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    HIMC himc = ImmGetContext(hWnd);
    if (himc != NULL)
    {
        printx(D_IME, CCFA "自动管理输入法状态（鼠标）: %d", uMsg);
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
            printx(D_IME, CCFA "自动管理输入法状态（键盘）: %hd", vkCode);
            ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
            ImmReleaseContext(hWnd, himc);
        }
    }
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_fix_ime_state(bool enable)
{
    printx(D_IME, CCFA "use_fix_ime_state: %s", enable ? "True" : "False");

    data_use_fix_ime_state = enable;

    return data_use_fix_ime_state;
}
