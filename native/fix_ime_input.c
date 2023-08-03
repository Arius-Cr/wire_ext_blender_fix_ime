#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <Strsafe.h>
#include <windows.h>
#include <windowsx.h>
#include <imm.h>
#pragma comment(lib, "Imm32.lib")
// Self
#include "main.h"
#include "utils.h"
#include "hook.h"
#include "fix_ime.h"
#include "fix_ime_state.h"
#include "fix_ime_input.h"

/* 工作机制请参考开发指南中的说明 */

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  私有

bool himc_composition_start = false; // 是否已经处于合成流程开始阶段，用于判断是否触发 himc_input_start

CompositionCallback *composition_callback = NULL;
ButtonDownCallback *button_down_callback = NULL;
LostFocusCallback *lost_focus_callback = NULL;
WindowDestoryCallback *windown_destory_callback = NULL;

enum Composition_Event_Type
{
    CET_START = 0,
    CET_UPDATE = 1,
    CET_FINISH = 2,
    CET_CANCEL = 3,
};

#define myHIMC_INPUT_PASS 0x77697265 // 按键能否通过 WM_INPUT 的标记

wchar_t *himc_text = NULL;      // 当前的合成字串
wchar_t himc_text_empty = '\0'; // 空白字符串，用于表示没有合成文本
int himc_text_size = 0;         // 当前的合成字串字节大小
int himc_text_length = 0;       // 当前的合成字串字符数量，不含零尾
int himc_text_caret_pos = 0;    // 当前的合成字串中光标的位置

BYTE key_states[256] = {0}; // 在 WM_INPUT 中用于接收 GetKeyboardState() 的输出

void window_ime_text_update(HWND hwnd, HIMC himc, DWORD type)
{
    if (himc_text)
        free(himc_text); // 清理上次获取的字符

    himc_text_size = ImmGetCompositionStringW(himc, type, NULL, 0);
    if (himc_text_size > 0)
    {
        himc_text_length = himc_text_size / sizeof(wchar_t);
        himc_text = (wchar_t *)malloc(sizeof(wchar_t) * (himc_text_length + 1)); // 分配空间
        himc_text[himc_text_length] = '\0';                                      // 零尾
        ImmGetCompositionStringW(himc, type, himc_text, himc_text_size);
        himc_text_caret_pos = ImmGetCompositionStringW(himc, GCS_CURSORPOS, NULL, 0);
    }
    else
    {
        himc_text_length = 0;
        himc_text = NULL;
        himc_text_caret_pos = 0;
    }
}

bool is_input_box_active_core(WindowData *window)
{
    // 注意 ：从 Blender 的源码来看，数值输入框激活时不会启动 IME，
    // 但是实际运行 Blender，数值输入框激活时，也会启动IME。
    // 查找了一下，原因是绘制控件时，调用的 ui_but_ime_reposition 导致的，
    // 如果之后 Blender 修复了这个 BUG，则当前的判断方法就不可靠了。
    // 到时，针对新版本的 Blender 可能需要通过 wm_pointer 获取内部数据来判断，
    // 但是对于旧版本保持当前方法，
    // 否则需要编译 3.0.0 之后的所有版本来确定偏移量，工程量巨大。

    bool ret = false;
    HIMC himc = ImmGetContext(window->handle);
    if (himc && himc != himc_custom)
    {
        // himc 为默认 himc 时，表示 Blender 的输入框正处于输入状态
        ret = true;
    }
    if (himc)
        ImmReleaseContext(window->handle, himc);
    return ret;
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  公共

extern bool data_use_fix_ime_input = false;

extern HIMC himc_custom = NULL; // 主要用于判断 Blender 是否处于输入框激活状态

extern bool himc_enabled = false;

extern bool himc_composition = false;

extern bool himc_block_shift_mouse_button = false;

extern void fix_ime_input_WM_BUTTONDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (uMsg == WM_KEYDOWN)
    {
        USHORT key = wParam;
        if (key == VK_SHIFT || key == VK_CONTROL)
        {
            return;
        }
    }
    else if (uMsg == WM_SYSKEYDOWN)
    {
        USHORT key = wParam;
        if (key == VK_MENU)
        {
            return;
        }
    }

    if (button_down_callback)
    {
        button_down_callback(window->wm_pointer);
    }
}

extern void fix_ime_input_WM_MOUSEBUTTONDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (himc_composition)
    {
        // 取消所有未完成的合成
        printx(D_IME, "强制取消文字合成（鼠标按键）：%p", hWnd);
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            ImmNotifyIME(himc, NI_COMPOSITIONSTR, CPS_CANCEL, 0);
            ImmReleaseContext(hWnd, himc);
        }
    }
    else
    {
        /**
         * 当按下 Shift + 鼠标按键 时暂时停用输入法，
         * 当 Shift 键释放时（WM_KEYUP 只会检测到 Shift 键释放，fix_ime_input_WM_KEYUP）时，
         * 如果检测到输入法被暂时停用，
         * 则重新启用输入法。该行为主要用于修复：
         * 文字物体编辑时用 Shfit + 鼠标中键 移动视图后，输入法的输入模式(英文/中文）会改变的问题。
         */
        if ((0x8000 & GetKeyState(VK_SHIFT)) > 0)
        {
            HIMC himc = ImmGetContext(hWnd);
            if (himc != NULL)
            {
                printx(D_IME, CCFA "临时暂停输入法");
                himc_block_shift_mouse_button = true;
                ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
                ImmReleaseContext(hWnd, himc);
            }
        }
    }
}

extern void fix_ime_input_WM_KILLFOCUS(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (himc_composition)
    {
        // 取消所有未完成的合成
        printx(D_IME, "强制取消文字合成（焦点丢失）：%p", hWnd);
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            ImmNotifyIME(himc, NI_COMPOSITIONSTR, CPS_CANCEL, 0);
            ImmReleaseContext(hWnd, himc);
        }
    }
    if (lost_focus_callback)
    {
        lost_focus_callback(window->wm_pointer);
    }
}

extern void fix_ime_input_WM_DESTROY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (windown_destory_callback)
    {
        windown_destory_callback(window->wm_pointer);
    }
}

extern bool fix_ime_input_WM_INPUT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    RAWINPUT raw;
    UINT raw_size = sizeof(RAWINPUT);
    GetRawInputData((HRAWINPUT)lParam, RID_INPUT, &raw, &raw_size, sizeof(RAWINPUTHEADER));
    if (raw.header.dwType != RIM_TYPEKEYBOARD)
        return false; // 仅处理键盘消息

    USHORT key = raw.data.keyboard.VKey;
    // BYTE state[256] = {0};
    // GetKeyboardState((PBYTE)state);
    memset(key_states, 0, 256 * sizeof(BYTE));
    GetKeyboardState((PBYTE)key_states);
    bool ctrl = key_states[VK_CONTROL] & 0x80;
    bool shift = key_states[VK_SHIFT] & 0x80;
    bool alt = key_states[VK_MENU] & 0x80;
    unsigned int msg = raw.data.keyboard.Message;
    bool key_down = !(raw.data.keyboard.Flags & RI_KEY_BREAK) && msg != WM_KEYUP && msg != WM_SYSKEYUP;

    wchar_t key_name[256] = L"??";
    if (D_IME)
    {
        bool extended = raw.data.keyboard.Flags & (RI_KEY_E0 | RI_KEY_E1);
        GetKeyNameTextW(MAKELPARAM(0, (extended ? KF_EXTENDED : 0) | (raw.data.keyboard.MakeCode & 0xff)),
                        (LPWSTR)&key_name, 256);
    }

    bool block = true;
    if (!himc_composition)
    {
        /**
         * 普通状态（非合成状态）：
         * 1、如果是回放的按键则直接通过
         * 2、否则，控制按键才允许通过（输入法应该不会拦截任何控制按键）。
         */
        if (raw.data.keyboard.ExtraInformation == myHIMC_INPUT_PASS)
        {
            printx(D_IME, CCFA "WM_INPUT 放行（%s-来自回放）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
            block = false;
        }
        else if (!((key >= '0' && key <= '9') ||
                   (key >= 'A' && key <= 'Z') ||
                   (key == VK_SPACE) ||
                   (key >= VK_OEM_1 && key <= VK_OEM_3) ||
                   (key >= VK_OEM_4 && key <= VK_OEM_7) ||
                   (key >= VK_NUMPAD0 && key <= VK_DIVIDE && key != VK_SEPARATOR)))
        {
            printx(D_IME, CCFA "WM_INPUT 放行（%s-非字符键）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
            block = false;
            /**
             * #define VK_NUMPAD0        0x60
             * #define VK_NUMPAD1        0x61
             * #define VK_NUMPAD2        0x62
             * #define VK_NUMPAD3        0x63
             * #define VK_NUMPAD4        0x64
             * #define VK_NUMPAD5        0x65
             * #define VK_NUMPAD6        0x66
             * #define VK_NUMPAD7        0x67
             * #define VK_NUMPAD8        0x68
             * #define VK_NUMPAD9        0x69
             * #define VK_MULTIPLY       0x6A   // *
             * #define VK_ADD            0x6B   // +
             * #define VK_SEPARATOR      0x6C   // ENTER
             * #define VK_SUBTRACT       0x6D   // -
             * #define VK_DECIMAL        0x6E   // .
             * #define VK_DIVIDE         0x6F   // /
             *
             * #define VK_OEM_1          0xBA   // ';:' for US
             * #define VK_OEM_PLUS       0xBB   // '+' any country
             * #define VK_OEM_COMMA      0xBC   // ',' any country
             * #define VK_OEM_MINUS      0xBD   // '-' any country
             * #define VK_OEM_PERIOD     0xBE   // '.' any country
             * #define VK_OEM_2          0xBF   // '/?' for US
             * #define VK_OEM_3          0xC0   // '`~' for US
             *
             * #define VK_OEM_4          0xDB  //  '[{' for US
             * #define VK_OEM_5          0xDC  //  '\|' for US
             * #define VK_OEM_6          0xDD  //  ']}' for US
             * #define VK_OEM_7          0xDE  //  ''"' for US
             * #define VK_OEM_8          0xDF
             */
        }
    }
    else
    {
        // 在合成阶段，会拦截所有按键
    }
    if (block)
    {
        printx(D_IME, CCFA "WM_INPUT 屏蔽（%s-插件接管）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
        return true;
    }
    return false;
}

extern void fix_ime_input_WM_KEYDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    /**
     * 如果当前开启了输入法，并且处于普通状态（非合成状态），且输入法不处理该按键，
     * 并且该按键属于字符按键，则重放一次该按键，
     * 这次重放将开放 WM_INPUT 的通道。
     * 此时，输入法会再次处理该事件，但没有关系，
     * 因为该键不是IME需要处理的，因此IME不会理会该按键，
     * 但会重新触发KEY_DOWN，因此需要通过标记避免再次重发。
     * 只会重发字符按键，控制按键重发会导致问题。
     */
    if (!himc_composition && wParam != VK_PROCESSKEY)
    {
        USHORT key = wParam;
        if ((key >= '0' && key <= '9') ||
            (key >= 'A' && key <= 'Z') ||
            (key == VK_SPACE) ||
            (key >= VK_OEM_1 && key <= VK_OEM_3) ||
            (key >= VK_OEM_4 && key <= VK_OEM_7) ||
            (key >= VK_NUMPAD0 && key <= VK_DIVIDE && key != VK_SEPARATOR))
        {
            LPARAM extra_info = GetMessageExtraInfo();
            if (extra_info != myHIMC_INPUT_PASS)
            {
                if (D_IME)
                {
                    wchar_t key_name[256] = L"??";
                    GetKeyNameTextW(lParam, (LPWSTR)&key_name, 256);
                    printx(D_IME, "WM_KEYDOWN 回放：\"%ls\" (%x)", key_name, key);
                }
                keybd_event(wParam, MapVirtualKey(key, MAPVK_VK_TO_VSC), 0, myHIMC_INPUT_PASS);
            }
            else
            {
                printx(D_IME, "WM_KEYDOWN 回放...完成");
            }
        }
    }
}

extern void fix_ime_input_WM_KEYUP(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    USHORT key = wParam;
    if (!himc_composition && wParam != VK_PROCESSKEY)
    {
        if (wParam != VK_PROCESSKEY)
        {
            if ((key >= '0' && key <= '9') ||
                (key >= 'A' && key <= 'Z') ||
                (key == VK_SPACE) ||
                (key >= VK_OEM_1 && key <= VK_OEM_3) ||
                (key >= VK_OEM_4 && key <= VK_OEM_7) ||
                (key >= VK_NUMPAD0 && key <= VK_DIVIDE && key != VK_SEPARATOR))
            {
                LPARAM extra_info = GetMessageExtraInfo();
                if (extra_info != myHIMC_INPUT_PASS)
                {
                    if (D_IME)
                    {
                        wchar_t key_name[256] = L"??";
                        GetKeyNameTextW(lParam, (LPWSTR)&key_name, 256);
                        printx(D_IME, "WM_KEYUP 回放：\"%ls\" (%x)", key_name, key);
                    }
                    // 和 KEY_DOWN 的唯一不同在于第三个参数为 KEYEVENTF_KEYUP
                    keybd_event(wParam, MapVirtualKey(key, MAPVK_VK_TO_VSC), KEYEVENTF_KEYUP, myHIMC_INPUT_PASS);
                }
                else
                {
                    printx(D_IME, "WM_KEYUP 回放...完成");
                }
            }
        }

        if (himc_block_shift_mouse_button && key == VK_SHIFT)
        {
            printx(D_IME, CCFA "恢复输入法");
            himc_block_shift_mouse_button = false;
            ImmAssociateContextEx(hWnd, NULL, IACE_DEFAULT);
        }
    }
}

extern void fix_ime_input_WM_IME_NOTIFY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
}

extern void fix_ime_input_WM_IME_SETCONTEXT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
}

extern void fix_ime_input_WM_IME_STARTCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    printx(D_IME, "WM_IME_STARTCOMPOSITION");

    himc_composition = true;

    himc_composition_start = true;
}

extern void fix_ime_input_WM_IME_COMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    WORD chDBCS = (WORD)wParam;
    BOOL fFlags = (BOOL)lParam;
    printx(D_IME, "WM_IME_COMPOSITION, fFlags: %x", fFlags);
    if (fFlags & GCS_COMPSTR)
    {
        if (himc_composition_start)
        {
            HIMC himc = ImmGetContext(hWnd);
            window_ime_text_update(hWnd, himc, GCS_COMPSTR);
            ImmReleaseContext(hWnd, himc);
            if (himc_text_size)
            {
                himc_composition_start = false;
                if (composition_callback)
                {
                    // printx(D_IME, "myHIMC_INPUT_START");
                    composition_callback(window->wm_pointer, CET_START, himc_text, himc_text_caret_pos);
                }
            }
        }
        else
        {
            HIMC himc = ImmGetContext(hWnd);
            window_ime_text_update(hWnd, himc, GCS_COMPSTR);
            ImmReleaseContext(hWnd, himc);
            if (himc_text_size)
            {
                himc_composition_start = false;
                if (composition_callback)
                {
                    // printx(D_IME, "myHIMC_INPUT_UPDATE");
                    composition_callback(window->wm_pointer, CET_UPDATE, himc_text, himc_text_caret_pos);
                }
            }
        }
    }
    else if (fFlags & GCS_CURSORPOS)
    {
        // 虽然 GCS_CURSORPOS 仅表示光标位置发生了变换，但是目前先这样粗略处理

        HIMC himc = ImmGetContext(hWnd);
        window_ime_text_update(hWnd, himc, GCS_COMPSTR);
        ImmReleaseContext(hWnd, himc);
        if (himc_text_size)
        {
            himc_composition_start = false;
            if (composition_callback)
            {
                // printx(D_IME, "myHIMC_INPUT_UPDATE");
                composition_callback(window->wm_pointer, CET_UPDATE, himc_text, himc_text_caret_pos);
            }
        }
    }
}

extern void fix_ime_input_WM_IME_ENDCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    printx(D_IME, "WM_IME_ENDCOMPOSITION");

    if (himc_composition_start)
    {
        himc_composition_start = false;
        HIMC himc = ImmGetContext(hWnd);
        window_ime_text_update(hWnd, himc, GCS_RESULTSTR);
        ImmReleaseContext(hWnd, himc);
        if (himc_text_size)
        {
            /**
             * 当直接按下 Shift + 1 之类时会发生这种情况，
             * 合成过程会快速经过开始、更新、完成，不会弹出候选窗口。
             * 这里的代码就是为了应对这种情况。
             **/
            if (composition_callback)
            {
                // printx(D_IME, "myHIMC_INPUT_START");
                // printx(D_IME, "myHIMC_INPUT_FINISH");
                composition_callback(window->wm_pointer, CET_START, himc_text, himc_text_caret_pos);
                composition_callback(window->wm_pointer, CET_FINISH, himc_text, himc_text_caret_pos);
            }
        }
    }
    else
    {
        HIMC himc = ImmGetContext(hWnd);
        window_ime_text_update(hWnd, himc, GCS_RESULTSTR);
        ImmReleaseContext(hWnd, himc);
        if (himc_text_size)
        {
            if (composition_callback)
            {
                // printx(D_IME, "myHIMC_INPUT_FINISH");
                composition_callback(window->wm_pointer, CET_FINISH, himc_text, himc_text_caret_pos);
            }
        }
        else
        {
            if (composition_callback)
            {
                // printx(D_IME, "myHIMC_INPUT_CNACEL");
                composition_callback(window->wm_pointer, CET_CANCEL, &himc_text_empty, 0);
            }
        }
    }

    himc_composition = false;
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_fix_ime_input(
    bool enable,
    CompositionCallback composition_callback_,
    ButtonDownCallback button_down_callback_,
    LostFocusCallback lost_focus_callback_,
    WindowDestoryCallback windown_destory_callback_)
{
    printx(D_IME, CCFA "use_fix_ime_input: %s", enable ? "True" : "False");

    HRESULT result_h = S_OK;
    BOOL result_b = TRUE;

    if (enable)
    {
        composition_callback = composition_callback_;
        button_down_callback = button_down_callback_;
        lost_focus_callback = lost_focus_callback_;
        windown_destory_callback = windown_destory_callback_;

        if (!himc_custom)
        {
            himc_custom = ImmCreateContext();
        }
    }
    else
    {
        composition_callback = NULL;
        button_down_callback = NULL;
        lost_focus_callback = NULL;
        windown_destory_callback = NULL;

        if (himc_custom)
        {
            ImmDestroyContext(himc_custom);
            himc_custom = NULL;
        }
    }

    data_use_fix_ime_input = enable;

    return data_use_fix_ime_input;
}

extern __declspec(dllexport) bool ime_input_enable(void *wm_pointer)
{
    /**
     * 在区块中启用输入法。
     * 虽然“在区块中”，但实际上是在整个窗口中启用输入法，
     * 只是在 BPY 中当鼠标移出区块后会自动停用输入法（正处于合成状态时除外）。
     */

    if (!data_use_fix_ime_input)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (himc == NULL || himc_enabled == false)
    {
        printx(D_IME, "ime_input_enable");

        himc_enabled = true;
        himc_composition = false;
        himc_block_shift_mouse_button = false;

        DWORD conversion, sentence;
        ImmAssociateContextEx(hwnd, NULL, IACE_DEFAULT);
        HIMC himc_default = ImmGetContext(hwnd);
        ImmGetConversionStatus(himc_default, &conversion, &sentence);
        ImmSetConversionStatus(himc_custom, conversion, sentence);
        ImmSetOpenStatus(himc_custom, true); // 通知IME，否则设置的状态有时需要按几次转换模式的按键（如Shift）才会生效。
        ImmReleaseContext(hwnd, himc_default);
        
        ImmAssociateContext(hwnd, himc_custom);
    }
    if (himc != NULL)
        ImmReleaseContext(hwnd, himc);
    return himc_enabled;
}

extern __declspec(dllexport) bool ime_input_disable(void *wm_pointer)
{
    /**
     * 在区块中启用输入法。
     * 虽然“在区块中”，但实际上是在整个窗口中停用输入法。
     * 由 BPY 中的代码调用。
     * 注意：会间接修复输入法和快捷键冲突问题。
     */

    WindowData *window = get_window_by_wm(wm_pointer);
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (himc != NULL || himc_enabled == true)
    {
        printx(D_IME, "ime_input_disable");

        himc_enabled = false;

        if (himc_text != NULL)
        {
            free(himc_text);
            himc_text = NULL;
            himc_text_size = 0;
            himc_text_length = 0;
        }

        DWORD conversion, sentence;
        ImmGetConversionStatus(himc_custom, &conversion, &sentence);
        ImmAssociateContextEx(hwnd, NULL, IACE_DEFAULT);
        HIMC himc_default = ImmGetContext(hwnd);
        ImmSetConversionStatus(himc_default, conversion, sentence);
        ImmSetOpenStatus(himc_default, true); // 通知IME，否则设置的状态有时需要按几次转换模式的按键（如Shift）才会生效。
        ImmReleaseContext(hwnd, himc_default);

        // ImmAssociateContextEx(hwnd, NULL, IACE_IGNORENOCONTEXT);
        ImmAssociateContext(hwnd, NULL);
    }
    if (himc != NULL)
        ImmReleaseContext(hwnd, himc);
    return himc_enabled;
}

extern __declspec(dllexport) bool is_input_box_active(void *wm_pointer)
{
    WindowData *window = get_window_by_wm(wm_pointer);
    if (!window)
        return false;

    return is_input_box_active_core(window);
}

extern __declspec(dllexport) bool candidate_window_position_update_font_edit(void *wm_pointer, float p, bool show_caret)
{
    if (!himc_enabled)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (!window)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (!himc)
        return false;

    /**
     * 本函数用于更新候选窗口的位置。
     *
     * 注意：
     *      ImmSetCandidateWindow 对大部分输入法都 *无效*，
     *      即使对微软拼音输入法也会有时候失效。
     *      候选窗口基本上看光标的位置和大小来进行定位。
     *
     * 光标创建后无需 ShowCaret()，光标在隐藏的状态下，依然是有效的。
     *
     * 所有坐标都是相对窗口客户区左上角。
     */

    HMONITOR monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONULL);
    MONITORINFO monitor_info = {0};
    monitor_info.cbSize = sizeof(monitor_info);
    GetMonitorInfo(monitor, &monitor_info);
    POINT xy = {
        monitor_info.rcWork.left + (int)(p * monitor_info.rcWork.right - monitor_info.rcWork.left),
        monitor_info.rcWork.bottom};
    POINT lt = {
        monitor_info.rcWork.left,
        monitor_info.rcWork.top};
    POINT rb = {
        monitor_info.rcWork.right,
        monitor_info.rcWork.bottom};
    ScreenToClient(hwnd, &xy);
    ScreenToClient(hwnd, &lt);
    ScreenToClient(hwnd, &rb);

    CANDIDATEFORM candidate_form = {0};
    candidate_form.dwIndex = 0;
    candidate_form.dwStyle = CFS_CANDIDATEPOS;
    candidate_form.ptCurrentPos.x = xy.x;
    candidate_form.ptCurrentPos.y = xy.y;
    candidate_form.rcArea.left = lt.x;
    candidate_form.rcArea.top = lt.y;
    candidate_form.rcArea.right = rb.x;
    candidate_form.rcArea.bottom = rb.y;
    ImmSetCandidateWindow(himc, &candidate_form);
    ImmReleaseContext(hwnd, himc);

    DestroyCaret();
    CreateCaret(hwnd, NULL, 10, 10); // 宽高不能同时为 1，否者部分字上屏后，微软拼音的候选窗口会偏移一段位置（原因未知）
    SetCaretPos(xy.x, xy.y);
    if (show_caret)
    {
        ShowCaret(hwnd);
    }

    return true;
}

extern __declspec(dllexport) bool candidate_window_position_update_text_editor(void *wm_pointer, int x, int y, int h, bool show_caret)
{
    if (!himc_enabled)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (!window)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (!himc)
        return false;

    CANDIDATEFORM candidate_form = {0};
    candidate_form.dwIndex = 0;
    candidate_form.dwStyle = CFS_CANDIDATEPOS;
    candidate_form.ptCurrentPos.x = x;
    candidate_form.ptCurrentPos.y = y;
    ImmSetCandidateWindow(himc, &candidate_form);
    ImmReleaseContext(hwnd, himc);

    DestroyCaret();
    CreateCaret(hwnd, NULL, 10, max(2, h));
    SetCaretPos(x, y);
    if (show_caret)
    {
        ShowCaret(hwnd);
    }

    return true;
}

extern __declspec(dllexport) bool candidate_window_position_update_console(void *wm_pointer, int l, int t, int r, int b, bool show_caret)
{
    if (!himc_enabled)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (!window)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (!himc)
        return false;

    CANDIDATEFORM candidate_form = {0};
    candidate_form.dwIndex = 0;
    candidate_form.dwStyle = CFS_EXCLUDE;
    candidate_form.ptCurrentPos.x = l;
    candidate_form.ptCurrentPos.y = b;
    candidate_form.rcArea.left = l;
    candidate_form.rcArea.top = t;
    candidate_form.rcArea.right = r;
    candidate_form.rcArea.bottom = b;
    ImmSetCandidateWindow(himc, &candidate_form);
    ImmReleaseContext(hwnd, himc);

    DestroyCaret();
    CreateCaret(hwnd, NULL, 10, max(2, b - t));
    SetCaretPos(l, t);
    if (show_caret)
    {
        ShowCaret(hwnd);
    }

    return true;
}
