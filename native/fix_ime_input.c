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
 *     此外，在文本物体的编辑模式、脚本编辑器、控制台中 Blender 不启用输入法。
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
 *         可以获取输入法的整个文字处理阶段和正在处理的文本，
 *         阶段分为三个：START、UPDATE、FINISH、CANCEL
 *         START：
 *             通过 keybd_event() 向窗口发送 Ctrl + F16 消息，由于均为控件按键，所有不会在 WM_INPUT 中被拦截。
 *             组合键会触发通过脚本自定义的一个操作（请参考 imm.py 中的 WIRE_OT_fix_ime_BASE 的子类），
 *             该操作启动后会持续响应 UPDATE、FINISH、CANCEL 的消息，直到合成完成。
 *             该操作主要的功能就是调用 BPY 的功能向目标插入和删除文字，通过将上次插入的文字删除，来模拟输入的效果。
 *             在每个阶段，都会将当前的合成文字存储到 himc_text 变量中，
 *             脚本需要通过调用 ime_text_get() 获取合成文字。
 *         UPDATE：
 *             插件存储当前合成文字到 himc_text 变量；
 *             通过 keybd_event() 向窗口发送 Ctrl + F17 消息；
 *             脚本中已启动的 WIRE_OT_fix_ime_BASE 子类操作监听到该消息，
 *             通过 xxx.delete（如bpy.ops.font.delete） 操作删除之前通过 xxx.insert（如bpy.ops.font.insert）插入的文字，
 *             通过调用 ime_text_get() 获取最新的合成文本，
 *             通过 xxx.insert 插入最新的合成文本。
 *         FINISH、CNACEL：
 *             和 UPDATE 类似，FINISH（Ctrl + F18）表示插入合成文本，CNACEL（Ctrl + F19）表示取消输入。
 *
 */

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  文件内功能

bool himc_composition_start = false; // 是否已经处于合成流程开始阶段，用于判断是否触发 himc_input_start

#define myHIMC_INPUT_PASS 0x77697265 // 按键能否通过 WM_INPUT 的标记

#define myHIMC_INPUT_ENABLE 0x0100     // 合成事件被启用的标记，如 (himc_input_start & myHIMC_INPUT_ENABLE) > 0 表示 START 已开启
#define myHIMC_INPUT_KEY1_DOWN 0x0001  // 合成事件按键1按下状态处理完毕的标记
#define myHIMC_INPUT_KEY1_UP 0x0002    // 合成事件按键1释放状态处理完毕的标记
#define myHIMC_INPUT_KEY2_DOWN 0x0004  // 合成事件按键2按下状态处理完毕的标记
#define myHIMC_INPUT_KEY2_UP 0x0008    // 合成事件按键2释放状态处理完毕的标记
#define myHIMC_INPUT_START_KEY VK_F16  // 合成事件 START  的按键2 虚拟键码
#define myHIMC_INPUT_UPDATE_KEY VK_F17 // 合成事件 UPDATE 的按键2 虚拟键码
#define myHIMC_INPUT_FINISH_KEY VK_F18 // 合成事件 FINISH 的按键2 虚拟键码
#define myHIMC_INPUT_CANCEL_KEY VK_F19 // 合成事件 CANCEL 的按键2 虚拟键码

short himc_input_start = 0;  // 合成事件 START   的状态，包括是否启用，各个按键是否已经处理的标记
short himc_input_update = 0; // 合成事件 UPDATE  的状态，包括是否启用，各个按键是否已经处理的标记
short himc_input_finish = 0; // 合成事件 FINISH  的状态，包括是否启用，各个按键是否已经处理的标记
short himc_input_cancel = 0; // 合成事件 CANCEL  的状态，包括是否启用，各个按键是否已经处理的标记

wchar_t *himc_text = NULL;      // 当前的合成字串
wchar_t himc_text_empty = '\0'; // 空字符
int himc_text_size = 0;         // 当前的合成字串字节大小
int himc_text_length = 0;       // 当前的合成字串字符数量，不含零尾
int himc_text_caret_pos = 0;    // 当前的合成字串中光标的位置

BYTE key_states[256] = {0}; // 在 WM_INPUT 中用于接收 GetKeyboardState() 的输出

void window_ime_text_update(HWND hwnd, HIMC himc, DWORD type)
{
    if (himc_text)
        free(himc_text); // 清理上次获取的字符

    // ImmGetCompositionWindow

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

void window_ime_message_send(USHORT key1, USHORT key2)
{
    keybd_event(key1, 0, 0, 0);
    keybd_event(key2, 0, 0, 0);
    keybd_event(key2, 0, KEYEVENTF_KEYUP, 0);
    keybd_event(key1, 0, KEYEVENTF_KEYUP, 0);
}

bool window_ime_message_check(USHORT key, bool down, short *check_list, USHORT key_1, USHORT key_2)
{
    if (key == key_1)
    {
        if (down)
        {
            *check_list |= myHIMC_INPUT_KEY1_DOWN;
        }
        else
        {
            *check_list |= myHIMC_INPUT_KEY1_UP;
        }
        return true;
    }
    else if (key == key_2)
    {
        if (down)
        {
            *check_list |= myHIMC_INPUT_KEY2_DOWN;
        }
        else
        {
            *check_list |= myHIMC_INPUT_KEY2_UP;
        }
        return true;
    }
    return false;
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序内功能

extern bool data_use_fix_ime_input = false;

extern HIMC himc_custom = NULL; // 现在没有用，似乎用默认的上下文就可以了

extern bool himc_enabled = false;

extern bool himc_composition = false;

extern bool himc_composition_core = false; // 表示合成实际上已经结束，但需要等待按键消息发送完成才真正结束

extern bool fix_ime_input_WM_INPUT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    RAWINPUT raw;
    UINT raw_size = sizeof(RAWINPUT);
    GetRawInputData((HRAWINPUT)lParam, RID_INPUT, &raw, &raw_size, sizeof(RAWINPUTHEADER));
    if (raw.header.dwType != RIM_TYPEKEYBOARD)
        return false; // 仅处理键盘消息

    USHORT key = raw.data.keyboard.VKey;
    // BYTE state[256] = {0};
    // GetKeyboardState((PBYTE)state);
    // bool ctrl = state[VK_CONTROL] & 0x80;
    // bool shift = state[VK_SHIFT] & 0x80;
    // bool alt = state[VK_MENU] & 0x80;
    memset(key_states, 0, 256 * sizeof(BYTE));
    GetKeyboardState((PBYTE)key_states);
    bool ctrl = key_states[VK_CONTROL] & 0x80;
    bool shift = key_states[VK_SHIFT] & 0x80;
    bool alt = key_states[VK_MENU] & 0x80;
    unsigned int msg = raw.data.keyboard.Message;
    bool key_down = !(raw.data.keyboard.Flags & RI_KEY_BREAK) && msg != WM_KEYUP && msg != WM_SYSKEYUP;

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
            DEBUGI(D_IME, "WM_INPUT：来自回放");
            block = false;
        }
        else if (!((key >= '0' && key <= '9') ||
                   (key >= 'A' && key <= 'Z') ||
                   (key == VK_SPACE) ||
                   (key >= VK_OEM_1 && key <= VK_OEM_3) ||
                   (key >= VK_OEM_4 && key <= VK_OEM_7) ||
                   (key >= VK_NUMPAD0 && key <= VK_DIVIDE && key != VK_SEPARATOR)))
        {
            DEBUGI(D_IME, "WM_INPUT：非字符键");
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
        // 在合成阶段，会拦截所有按键，
        // 但当任何合成事件启用后，只要按键符合事件相关的按键（如：Ctrl + F16）则不拦截，
        // 并跟踪按键状态来调整事件状态，譬如完整接收到 Ctrl + F16 的 KeyDown 和 KeyUp 后关闭该事件，
        // 如果不关闭事件，则会一直放行 Ctrl 和 F16 按键。
        if ((himc_input_start & myHIMC_INPUT_ENABLE) > 0)
        {
            if (window_ime_message_check(key, key_down, &himc_input_start, VK_CONTROL, myHIMC_INPUT_START_KEY))
            {
                block = false;
                if ((himc_input_start & 0x000F) == 0x000F)
                {
                    DEBUGI(D_HOK, CCBY "发送 “合成开始” 消息：%x" CCZ0, himc_input_start);
                    himc_input_start = 0;
                }
            }
        }
        else if ((himc_input_update & myHIMC_INPUT_ENABLE) > 0)
        {
            if (window_ime_message_check(key, key_down, &himc_input_update, VK_CONTROL, myHIMC_INPUT_UPDATE_KEY))
            {
                block = false;
                if ((himc_input_update & 0x000F) == 0x000F)
                {
                    DEBUGI(D_HOK, CCBP "发送 “合成更新” 消息：%x" CCZ0, himc_input_update);
                    himc_input_update = 0;
                }
            }
        }
        else if ((himc_input_finish & myHIMC_INPUT_ENABLE) > 0)
        {
            if (window_ime_message_check(key, key_down, &himc_input_finish, VK_CONTROL, myHIMC_INPUT_FINISH_KEY))
            {
                block = false;
                if ((himc_input_finish & 0x000F) == 0x000F)
                {
                    DEBUGI(D_HOK, CCBG "发送 “确认合成” 消息：%x" CCZ0, himc_input_finish);
                    himc_input_finish = 0;
                    himc_composition = false;
                    himc_composition_core = false;
                }
            }
        }
        else if ((himc_input_cancel & myHIMC_INPUT_ENABLE) > 0)
        {
            if (window_ime_message_check(key, key_down, &himc_input_cancel, VK_CONTROL, myHIMC_INPUT_CANCEL_KEY))
            {
                block = false;
                if ((himc_input_cancel & 0x000F) == 0x000F)
                {
                    DEBUGI(D_HOK, CCBR "发送 “取消合成” 消息：%x" CCZ0, himc_input_cancel);
                    himc_input_cancel = 0;
                    himc_composition = false;
                    himc_composition_core = false;
                }
            }
        }
    }
    if (block)
    {
        DEBUGH(D_IME, "WM_INPUT 屏蔽（%s）：%hx", key_down ? "DOWN" : "UP", key);
        return true;
    }
    else
    {
        DEBUGH(D_IME, "WM_INPUT 放行（%s）：%hx", key_down ? "DOWN" : "UP", key);
    }
    return false;
}

extern void fix_ime_input_WM_KILLFOCUS(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    // 虽然函数的名称为 WM_KILLFOCUS，但在鼠标按键按下时，依然由该函数处理，因此该函数实际上在准备或已经丢失焦点时运行

    if (himc_composition)
    {
        // 取消所有未完成的合成
        DEBUGI(D_IME, "强制取消文字合成：%p", hWnd);
        HIMC himc = ImmGetContext(hWnd);
        if (himc != NULL)
        {
            ImmNotifyIME(himc, NI_COMPOSITIONSTR, CPS_CANCEL, 0);
            ImmReleaseContext(hWnd, himc);
        }
    }
}

extern void fix_ime_input_WM_SETFOCUS(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    if (himc_composition)
    {
        if (!himc_composition_core)
        {
            DEBUGI(D_IME, "强制取消文字合成(焦点丢失时)：%p", hWnd);
            himc_input_cancel = myHIMC_INPUT_ENABLE;
            window_ime_message_send(VK_CONTROL, myHIMC_INPUT_CANCEL_KEY);
        }
    }
}

extern void fix_ime_input_WM_KEYDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
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
                DEBUGI(D_IME, "WM_KEYDOWN 回放：%x", key);
                keybd_event(wParam, MapVirtualKey(key, MAPVK_VK_TO_VSC), 0, myHIMC_INPUT_PASS);
            }
            else
            {
                DEBUGI(D_IME, "WM_KEYDOWN 回放...完成");
            }
        }
    }
}

extern void fix_ime_input_WM_KEYUP(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
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
                DEBUGI(D_IME, "WM_KEYUP 回放：%x", key);
                // 和 KEY_DOWN 的唯一不同在于第三个参数为 KEYEVENTF_KEYUP
                keybd_event(wParam, MapVirtualKey(key, MAPVK_VK_TO_VSC), KEYEVENTF_KEYUP, myHIMC_INPUT_PASS);
            }
            else
            {
                DEBUGI(D_IME, "WM_KEYUP 回放...完成");
            }
        }
    }
}

extern void fix_ime_input_WM_IME_NOTIFY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
}

extern void fix_ime_input_WM_IME_SETCONTEXT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
}

extern void fix_ime_input_WM_IME_STARTCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    DEBUGI(D_IME, "WM_IME_STARTCOMPOSITION");

    himc_composition = true;
    himc_composition_core = true;

    himc_composition_start = true;
}

extern void fix_ime_input_WM_IME_COMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
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
                // DEBUGI(D_IME, "myHIMC_INPUT_START");
                himc_input_start = myHIMC_INPUT_ENABLE;
                window_ime_message_send(VK_CONTROL, myHIMC_INPUT_START_KEY);
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
                // DEBUGI(D_IME, "myHIMC_INPUT_UPDATE");
                himc_input_update = myHIMC_INPUT_ENABLE;
                window_ime_message_send(VK_CONTROL, myHIMC_INPUT_UPDATE_KEY);
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
            // DEBUGI(D_IME, "myHIMC_INPUT_UPDATE");
            himc_input_update = myHIMC_INPUT_ENABLE;
            window_ime_message_send(VK_CONTROL, myHIMC_INPUT_UPDATE_KEY);
        }
    }
}

extern void fix_ime_input_WM_IME_ENDCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    DEBUGI(D_IME, "WM_IME_ENDCOMPOSITION");

    /**
     * 注意：因为外部原因导致窗口失去焦点时（截图的时候可能会发生这种情况），
     * 在 WM_KILLFOCUS 中会强制取消合成，但此时 window_ime_message_send 很可能无法将按键发送到目标窗口，
     * 因此 himc_composition = false 不能在 fix_ime_input_WM_INPUT 中进行设置。
     * 如果无法发送按键也有备用手段。在 BPY 的 WIRE_OT_fix_ime_input_BASE 会在鼠标移动时检查是否依然处于合成状态，
     * 如果不是，则会自动取消合成，通过这两种手段可以基本确保意外情况下，一切按原设计进行。
     */
    himc_composition_core = false;

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
            // DEBUGI(D_IME, "myHIMC_INPUT_START");
            himc_input_start = myHIMC_INPUT_ENABLE;
            window_ime_message_send(VK_CONTROL, myHIMC_INPUT_START_KEY);
            // DEBUGI(D_IME, "myHIMC_INPUT_FINISH");
            himc_input_finish = myHIMC_INPUT_ENABLE;
            window_ime_message_send(VK_CONTROL, myHIMC_INPUT_FINISH_KEY);
        }
    }
    else
    {
        HIMC himc = ImmGetContext(hWnd);
        window_ime_text_update(hWnd, himc, GCS_RESULTSTR);
        ImmReleaseContext(hWnd, himc);
        if (himc_text_size)
        {
            // DEBUGI(D_IME, "myHIMC_INPUT_FINISH");
            himc_input_finish = myHIMC_INPUT_ENABLE;
            window_ime_message_send(VK_CONTROL, myHIMC_INPUT_FINISH_KEY);
        }
        else
        {
            // DEBUGI(D_IME, "myHIMC_INPUT_CNACEL");
            himc_input_cancel = myHIMC_INPUT_ENABLE;
            window_ime_message_send(VK_CONTROL, myHIMC_INPUT_CANCEL_KEY);
        }
    }
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序外功能

extern __declspec(dllexport) bool use_fix_ime_input(bool enable)
{
    DEBUGH(D_IME, "use_fix_ime_input: %s", enable ? "True" : "False");

    HRESULT result_h = S_OK;
    BOOL result_b = TRUE;

    if (enable)
    {
        // if (himc_custom == NULL)
        // {
        //     himc_custom = ImmCreateContext();
        //     ImmSetConversionStatus(himc_custom, IME_CMODE_ALPHANUMERIC, IME_SMODE_NONE);
        // }
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

extern __declspec(dllexport) wchar_t *ime_text_get()
{
    /**
     * 获取当前的合成文本，实际上该文本在 WM_XXX 事件中保存到 himc_text 的，
     * 原则上来说需要在此处才获取的，但是本质上没有太大区别，就这样吧。
     * 该函数由 BPY 侧的代码调用。
     **/
    if (himc_text)
    {
        return himc_text;
    }
    else
    {
        return &himc_text_empty;
    }
}

extern __declspec(dllexport) int ime_text_caret_pos_get()
{
    /**
     * 获取当前的合成文本中光标的位置。
     * 该位置实际上在 WM_XXX 事件中进行获取。
     * 该函数由 BPY 侧的代码调用。
     **/
    return himc_text_caret_pos;
}

extern __declspec(dllexport) bool candidate_window_position_update_font_edit(void *wm_pointer, float p)
{
    if (!himc_enabled)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);

    POINT xy = {0};
    POINT lt = {0};
    POINT rb = {0};
    HMONITOR monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONULL);
    MONITORINFO monitor_info = {0};
    monitor_info.cbSize = sizeof(monitor_info);
    GetMonitorInfo(monitor, &monitor_info);

    xy.x = monitor_info.rcWork.left + (int)(p * monitor_info.rcWork.right - monitor_info.rcWork.left);
    xy.y = monitor_info.rcWork.bottom;
    lt.x = monitor_info.rcWork.left;
    lt.y = monitor_info.rcWork.top;
    rb.x = monitor_info.rcWork.right;
    rb.y = monitor_info.rcWork.bottom;

    // DEBUGI(D_IME, "x: %d, y: %d", xy.x, xy.y);
    // DEBUGI(D_IME, "l: %d, t: %d", lt.x, lt.y);
    // DEBUGI(D_IME, "r: %d, b: %d", rb.x, rb.y);

    ScreenToClient(hwnd, &xy);
    ScreenToClient(hwnd, &lt);
    ScreenToClient(hwnd, &rb);

    // DEBUGI(D_IME, "x: %d, y: %d", xy.x, xy.y);
    // DEBUGI(D_IME, "l: %d, t: %d", lt.x, lt.y);
    // DEBUGI(D_IME, "r: %d, b: %d", rb.x, rb.y);

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
    CreateCaret(hwnd, NULL, 10, 20);
    SetCaretPos(xy.x, xy.y);
    ShowCaret(hwnd);

    return true;
}

extern __declspec(dllexport) bool candidate_window_position_update_text_editor(void *wm_pointer, int x, int y)
{
    if (!himc_enabled)
        return false;

    WindowData *window = get_window_by_wm(wm_pointer);
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);

    // 更新候选窗口位置（所有坐标相对窗口客户区左上角）

    CANDIDATEFORM candidate_form = {0};
    candidate_form.dwIndex = 0;
    candidate_form.dwStyle = CFS_CANDIDATEPOS;
    candidate_form.ptCurrentPos.x = x;
    candidate_form.ptCurrentPos.y = y;
    ImmSetCandidateWindow(himc, &candidate_form);

    // if (D_IME)
    // {
    //     DEBUGI(D_IME, "x: %d, y: %d", x, y);

    //     ImmGetCandidateWindow(himc, 0, &candidate_form);
    //     DEBUGI(D_IME, "ptCurrentPos.x: %d", candidate_form.ptCurrentPos.x);
    //     DEBUGI(D_IME, "ptCurrentPos.y: %d", candidate_form.ptCurrentPos.y);
    // }

    ImmReleaseContext(hwnd, himc);

    /**
     * 从 Blender 源码注释中得知，似乎某些输入法不理会 ImmSetCandidateWindow() 的设置，
     * 只根据输入光标的位置来定位候选窗口。
     * 测试过微软拼音、微软日语、搜狗输入法，都能响应 ImmSetCandidateWindow()，
     * 而在没有设置 CANDIDATEFORM 时，搜狗会以光标位置定位，而微软的输入法会定位到工作区右下角。
     * 光标创建后无需 ShowCaret()，光标在隐藏的状态下，依然是有效的。
     * */
    DestroyCaret();
    CreateCaret(hwnd, NULL, 10, 20);
    SetCaretPos(x, y);
    // ShowCaret(hwnd);

    return true;
}

extern __declspec(dllexport) bool candidate_window_position_update_console(void *wm_pointer, int x, int y, int l, int t, int r, int b)
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
    candidate_form.ptCurrentPos.x = x;
    candidate_form.ptCurrentPos.y = y;
    candidate_form.rcArea.left = l;
    candidate_form.rcArea.top = t;
    candidate_form.rcArea.right = r;
    candidate_form.rcArea.bottom = b;
    ImmSetCandidateWindow(himc, &candidate_form);

    // DEBUGI(D_IME, "x: %d, y: %d", x, y);
    // DEBUGI(D_IME, "l: %d, t: %d", l, t);
    // DEBUGI(D_IME, "r: %d, b: %d", r, b);

    ImmReleaseContext(hwnd, himc);

    DestroyCaret();
    CreateCaret(hwnd, NULL, 10, 20);
    SetCaretPos(x, y);
    // ShowCaret(hwnd);

    return true;
}
