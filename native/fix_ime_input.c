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

/**作用机制：
 * 正常的输入法处理流程：
 *     事件发生顺序：WM_INPUT -> WM_KEYDOWN -> WM_IME_STARTCOMPOSITION -> WM_IME_COMPOSITION -> WM_IME_ENDCOMPOSITION
 *     当启用输入法时，WM_KEYDOWN 和 WM_KEYUP 的 wParam 如果为 VK_PROCESSKEY，表示按按键由输入法处理，程序应该无视该按键，
 *     转而关注 WM_IME_XXX 等消息来获取用户的文字输入，否则程序按自己逻辑处理 KEY_DOWN 即可。
 *     输入法在 WM_INPUT 之后 WM_KEYDOWN 之前介入按键处理，因此在 WM_INPUT 时程序无法得知该按键是否会被输入法处理。
 * 现况：
 *     Blender 通过 WM_INPUT 来处理按键和输入，
 *     但输入法的输入消息在该事件之后发生，因此 Blender 无法得知该按键是输入法处理还是自己需要处理，
 *     而 Blender 采用的解决方法是硬编码，即如果输入法处于非英文输入状态，则认为某些按键必定被输入法处理，
 *     但按键是否被输入法处理是输入法自身逻辑决定的，
 *     因此硬编码的内容和具体的某款输入法的处理逻辑不同的话，就会导致问题。
 *     此外，在文本物体的编辑模式、文本编辑器、控制台中 Blender 不启用输入法。
 * 策略：
 *     通过脚本检查当前鼠标是否在 【文本物体的编辑模式】、【脚本编辑器】、【控制台】 三种状态的任一状态中，
 *     如果是，则脚本主动启用 【自定义输入流程】（ime_input_enable），否则停用该流程（ime_input_disable）。
 *     启用该流程后，插件会完全接管窗口对按键的处理。
 *     定义：
 *         默认处于【普通状态】（himc_composition 为 false）
 *         当 WM_IME_STARTCOMPOSITION 发生时，进入【合成状态】；
 *         当 WM_IME_ENDCOMPOSITION 结束后，回到普通状态。
 *     在普通状态中：
 *         在 WM_INPUT 中，以下情况会调用 Blender 原来的窗口处理过程（放行），否则直接调用 DefWndProc（拦截）：
 *             1、ExtraInformation 为 myHIMC_INPUT_PASS。
 *                myHIMC_INPUT_PASS 为自设的标记，用来标记该按键是否应该被拦截，只有重放的按键具有该标记。
 *             2、控制按键。反过来的意思就是拦截所有文字按键。
 *         即在普通状态中，WM_INPUT 只能处理被重放的按键或控制按键。
 *         在 WM_KEYDOWN 和 WM_KEYUP 中，如果 wParam != VK_PROCESSKEY，则通过 keybd_event() 重放按键，
 *         此时，按键的 ExtraInformation 被设为 myHIMC_INPUT_PASS，
 *         则该按键在 WM_INPUT 中不会被拦截，同时在 WM_KEYDOWN 也不会再重放一次（否则会无限重放）。
 *         这是在普通状态，也就是输入法启用但是输入法不处理这些按键（例如英文输入模式）的时候的处理流程。
 *         如果 WM_KEYDOWN 和 WM_KEYUP 中，wParam == VK_PROCESSKEY，则不重放按键，
 *         接下来必然进入合成状态，由合成状态的流程处理文字输入。
 *     在合成状态中：
 *         在 WM_IME_STARTCOMPOSITION、WM_IME_COMPOSITION、WM_IME_ENDCOMPOSITION 中，
 *         可以获取输入法的整个文字处理阶段和正在处理的文本及文本中光标的位置，
 *         阶段分为四个：START、UPDATE、FINISH、CANCEL。
 *         当进入某个阶段，获取合成文本和合成文本中光标位置后，
 *         将数据通过 use_fix_ime_input() 时传入的回调函数发送给脚本侧的代码，
 *         由脚本侧的代码通过 bpy.ops.insert 之类的操作将合成文本显示到界面中。
 */

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  文件内功能

bool himc_composition_start = false; // 是否已经处于合成流程开始阶段，用于判断是否触发 himc_input_start

CompositionCallback *composition_callback = NULL;
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

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序内功能

extern bool data_use_fix_ime_input = false;

extern HIMC himc_custom = NULL; // 现在没有用，似乎用默认的上下文就可以了

extern bool himc_enabled = false;

extern bool himc_composition = false;

extern bool himc_block_shift_mouse_button = false;

extern void fix_ime_input_WM_xBUTTONDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (himc_composition)
    {
        // 取消所有未完成的合成
        DEBUGI(D_IME, "强制取消文字合成（鼠标按键）：%p", hWnd);
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
                DEBUGH(D_IME, "临时暂停输入法");
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
        DEBUGI(D_IME, "强制取消文字合成（焦点丢失）：%p", hWnd);
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
            DEBUGH(D_IME, "WM_INPUT 放行（%s-来自回放）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
            block = false;
        }
        else if (!((key >= '0' && key <= '9') ||
                   (key >= 'A' && key <= 'Z') ||
                   (key == VK_SPACE) ||
                   (key >= VK_OEM_1 && key <= VK_OEM_3) ||
                   (key >= VK_OEM_4 && key <= VK_OEM_7) ||
                   (key >= VK_NUMPAD0 && key <= VK_DIVIDE && key != VK_SEPARATOR)))
        {
            DEBUGH(D_IME, "WM_INPUT 放行（%s-非字符键）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
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
        DEBUGH(D_IME, "WM_INPUT 屏蔽（%s-插件接管）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
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
                    DEBUGI(D_IME, "WM_KEYDOWN 回放：\"%ls\" (%x)", key_name, key);
                }
                keybd_event(wParam, MapVirtualKey(key, MAPVK_VK_TO_VSC), 0, myHIMC_INPUT_PASS);
            }
            else
            {
                DEBUGI(D_IME, "WM_KEYDOWN 回放...完成");
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
                        DEBUGI(D_IME, "WM_KEYUP 回放：\"%ls\" (%x)", key_name, key);
                    }
                    // 和 KEY_DOWN 的唯一不同在于第三个参数为 KEYEVENTF_KEYUP
                    keybd_event(wParam, MapVirtualKey(key, MAPVK_VK_TO_VSC), KEYEVENTF_KEYUP, myHIMC_INPUT_PASS);
                }
                else
                {
                    DEBUGI(D_IME, "WM_KEYUP 回放...完成");
                }
            }
        }

        if (himc_block_shift_mouse_button && key == VK_SHIFT)
        {
            DEBUGH(D_IME, "恢复输入法");
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
    DEBUGI(D_IME, "WM_IME_STARTCOMPOSITION");

    himc_composition = true;

    himc_composition_start = true;
}

extern void fix_ime_input_WM_IME_COMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    WORD chDBCS = (WORD)wParam;
    BOOL fFlags = (BOOL)lParam;
    DEBUGI(D_IME, "WM_IME_COMPOSITION, fFlags: %x", fFlags);
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
                    // DEBUGI(D_IME, "myHIMC_INPUT_START");
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
                    // DEBUGI(D_IME, "myHIMC_INPUT_UPDATE");
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
                // DEBUGI(D_IME, "myHIMC_INPUT_UPDATE");
                composition_callback(window->wm_pointer, CET_UPDATE, himc_text, himc_text_caret_pos);
            }
        }
    }
}

extern void fix_ime_input_WM_IME_ENDCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    DEBUGI(D_IME, "WM_IME_ENDCOMPOSITION");

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
                // DEBUGI(D_IME, "myHIMC_INPUT_START");
                // DEBUGI(D_IME, "myHIMC_INPUT_FINISH");
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
                // DEBUGI(D_IME, "myHIMC_INPUT_FINISH");
                composition_callback(window->wm_pointer, CET_FINISH, himc_text, himc_text_caret_pos);
            }
        }
        else
        {
            if (composition_callback)
            {
                // DEBUGI(D_IME, "myHIMC_INPUT_CNACEL");
                composition_callback(window->wm_pointer, CET_CANCEL, &himc_text_empty, 0);
            }
        }
    }

    himc_composition = false;
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序外功能

extern __declspec(dllexport) bool use_fix_ime_input(
    bool enable,
    CompositionCallback composition_callback_,
    LostFocusCallback lost_focus_callback_,
    WindowDestoryCallback windown_destory_callback_)
{
    DEBUGH(D_IME, "use_fix_ime_input: %s", enable ? "True" : "False");

    HRESULT result_h = S_OK;
    BOOL result_b = TRUE;

    if (enable)
    {
        composition_callback = composition_callback_;
        lost_focus_callback = lost_focus_callback_;
        windown_destory_callback = windown_destory_callback_;

        // if (himc_custom == NULL)
        // {
        //     himc_custom = ImmCreateContext();
        //     ImmSetConversionStatus(himc_custom, IME_CMODE_ALPHANUMERIC, IME_SMODE_NONE);
        // }
    }
    else
    {
        composition_callback = NULL;
        lost_focus_callback = NULL;
        windown_destory_callback = NULL;
    }

    data_use_fix_ime_input = enable;

    return true;
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
        DEBUGI(D_IME, "ime_input_enable");

        himc_enabled = true;
        himc_composition = false;
        himc_block_shift_mouse_button = false;

        ImmAssociateContextEx(hwnd, NULL, IACE_DEFAULT);
        // ImmAssociateContext(hwnd, himc_custom);
    }
    if (himc != NULL)
        ImmReleaseContext(hwnd, himc);
    return true;
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
        DEBUGI(D_IME, "ime_input_disable");

        himc_enabled = false;

        if (himc_text != NULL)
        {
            free(himc_text);
            himc_text = NULL;
            himc_text_size = 0;
            himc_text_length = 0;
        }

        ImmAssociateContextEx(hwnd, NULL, IACE_IGNORENOCONTEXT);
    }
    if (himc != NULL)
        ImmReleaseContext(hwnd, himc);
    return true;
}

extern __declspec(dllexport) bool candidate_window_position_update_font_edit(void *wm_pointer, float p, bool show_caret)
{
    if (!himc_enabled)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;

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

    HIMC himc = ImmGetContext(hwnd);
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
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;

    HIMC himc = ImmGetContext(hwnd);
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
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;

    HIMC himc = ImmGetContext(hwnd);
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
