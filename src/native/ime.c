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
#include "utils.h"
#include "main.h"
#include "blender.h"
#include "ime.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern bool data_use_fix_ime_debug = true;

static bool data_use_fix_ime = false;

static bool data_use_fix_ime_for_field = false;

static bool data_use_fix_ime_for_space = false;

static bool data_use_fix_direct_input_caps_lock = false;

static bool data_use_fix_direct_input_all = false;

// -----

/**
 * 用于记录窗口信息的缓存的"链表"，仅用于提升窗口类型判断的效率
 */
typedef struct tag_node_WindowData
{
    struct tag_node_WindowData *next; // 节点指针
    HWND handle;                      // 窗口句柄

    /**
     * Blender 中 GHOST_WindowWin32（gw_pointer） 和 wmWindow（wm_pointer） 实例的指针。
     * gw_pointer 用于将窗口和 wmWindow 对应。（从 wm_pointer 可以获得 gw_pointer，但反过来则不太方便）
     *
     * source\blender\windowmanager\intern\wm_window.c
     *      wm_window_ghostwindow_add()
     * intern\ghost\intern\GHOST_WindowWin32.cpp
     *      GHOST_WindowWin32::GHOST_WindowWin32()
     * 官方将自己的 GHOST_WindowWin32 对象的指针存储到窗口的用户数据中，
     * 而 Window 对象的第一个成员为 GHOST_WindowWin32 对象的指针，
     * 因此可以根据这些获取到指针和窗口的对应关系。
     */
    void *gw_pointer;
    void *wm_pointer;

    /** 当前窗口 IME 的启用者，必须通过 get_ime_invoker 函数来获取，不能直接通过该属性获取。 */
    IMEInvoker invoker;

    bool composing;
} WindowData;

typedef struct tag_head_WindowData
{
    int count;
    WindowData *first;
} WindowDataHead;

/**
 * 已被捕获的窗口
 */
static WindowData *window_datas = NULL;

static WindowDataHead window_datas_head = {.count = 0, .first = NULL};

static WindowData *window_datas_for_each(WindowData **window)
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

static WindowData *window_datas_add(WindowData *window)
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

static bool window_datas_remove(WindowData *window)
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

static bool window_datas_clean()
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

static WindowData *find_window_by_gw_ptr(void *gw_ptr)
{
    WindowData *window = NULL;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->gw_pointer == gw_ptr)
        {
            return window;
        }
    }
    return NULL;
}

static WindowData *find_window_by_wm_ptr(void *wm_ptr)
{
    WindowData *window = NULL;
    while (window_datas_for_each(&window) != NULL)
    {
        if (window->wm_pointer == wm_ptr)
        {
            return window;
        }
    }
    return NULL;
}

static inline void *get_gw_ptr(void *wm_ptr)
{
    /**
     * 参考：
     * source\blender\makesdna\DNA_windowmanager_types.h
     *      typedef struct wmWindow
     */
    return (void *)*((size_t *)wm_ptr + 2);
}

static HWND _handle = NULL;
static BOOL CALLBACK _EnumThreadWndProc(HWND hWnd, LPARAM gw_ptr)
{
    if ((void *)GetWindowLongPtrW(hWnd, GWLP_USERDATA) == (void *)gw_ptr)
    {
        _handle = hWnd;
        return FALSE; // 退出枚举
    }
    return TRUE;
}
static HWND get_handle(void *wm_ptr)
{
    void *gw_pointer = get_gw_ptr(wm_ptr);
    _handle = NULL;
    EnumThreadWindows(thread_id, _EnumThreadWndProc, (LPARAM)gw_pointer);
    return _handle;
}

// -----

static FixIMEEventCallback *event_callback = NULL;

#define IS_FILED(invoker) (invoker == INVOKER_FIELD)
#define IS_SPACE(invoker) (invoker >= INVOKER_VIEW3D_FONT_EDIT && invoker <= INVOKER_CONSOLE)
#define USE_AND_IS_FILED(win) (data_use_fix_ime_for_field && IS_FILED(win->invoker))
#define USE_AND_IS_SPACE(win) (data_use_fix_ime_for_space && IS_SPACE(win->invoker))

/** 设置到回放按键消息的 dwExtraInfo 中，表示在 WM_INPUT 时不要拦截该按键  */
#define myHIMC_INPUT_PASS 0x77697265

/**
 * 设置到回放按键消息的 dwExtraInfo 中，表示在 WM_INPUT 时必须拦截并抛弃该按键。
 * 这种按键用于中断按键的重复状态。大部分快捷键需要按键处于第一次按下时才会被识别，
 * 而 Blender 3.6.2 版修改了获取按键重复状态的逻辑，使得这里必须模拟一次按键释放，
 * 才能让 Blender 认为按键处于非重复状态。具体参考 WM_KEYDOWN 事件的处理逻辑。
 * 参考源码：GHOST_SystemWin32::processKeyEvent()
 */
#define myHIMC_INPUT_BLOCK 0x77697266

/** 窗口消息交由函数处理后，函数希望调用者执行的操作 */
typedef enum
{
    /** 调用者可以让原始窗口处理该消息。 */
    FIRT_PASS,
    /** 调用者不要让原始窗口处理该消息，应该直接调用 DefWindowProc()。 */
    FIRT_BLOCK,
    /** 调用者应该返回函数返回的返回值。 */
    FIRT_RETURN,
} FIRT; // Fix IME Return

/** 在 WM_INPUT 中用于接收 GetKeyboardState() 的输出 */
static BYTE key_states[256] = {0};

/* 回放按键数据，用于 SendInput()。最多只有两个回放按键数据。 */
/* 对于 FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE 最多可能有六个按键数据 */
static INPUT playback_key_events[6];

/* 修复 Blender 在中文输入模式下无法输入英文标点的问题 */
#define FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE 1

/**
 * 获取指定窗口中 IME 的调用者。
 * 该函数实际上会根据当前情况更新 WindowData.invoker，
 * 因此直接获取 invoker 属性是没有意义的，必须通过该函数获取。
 */
static IMEInvoker get_ime_invoker(WindowData *window)
{
    if (wmWindow_is_but_active(window->wm_pointer))
    {
        window->invoker = INVOKER_FIELD;
        return INVOKER_FIELD;
    }
    else
    {
        if (window->invoker == INVOKER_FIELD)
        {
            window->invoker = INVOKER_NONE;
        }
        return window->invoker;
    }
}

typedef enum
{
    // 拦截（均为字符按键，除退格键）
    KEY_CATALOG_BLOCK,
    // 非数字锁定时的数字键（0-9，.），此时按键实际为方向键、HOME、END、DEL等。
    KEY_CATALOG_BLOCK_NOT_NUMLOCK,
    // 不拦截（非字符按键、非数字锁定时的数字键）
    KEY_CATALOG_NOT_BLOCK,
} KEY_CATALOG;

static KEY_CATALOG get_key_catalog(USHORT key, BOOL extended)
{
    /**
     * 判断当前按键是否为字符键，包括回车键，退格键，因为这些键都是输入法可能会处理的按键。
     * 譬如正在合成文字时，按下空格键、回车键选择或确认文字。
     *
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
    if ((key >= '0' && key <= '9') ||
        (key >= 'A' && key <= 'Z') ||
        (key == VK_SPACE) || (key == VK_RETURN) || (key == VK_BACK) || (key == VK_TAB) ||
        (key >= VK_OEM_1 && key <= VK_OEM_3) ||
        (key >= VK_OEM_4 && key <= VK_OEM_7) ||
        (key >= VK_NUMPAD0 && key <= VK_DIVIDE && key != VK_SEPARATOR))
    {
        return KEY_CATALOG_BLOCK;
    }

    /**
     * 判断当前按键是否为非数字锁定时的数字键盘上的数字键或点号键
     *
     * 以 数字键4 为例，按下时：
     * - 　数字锁定时，key == VK_NUMPAD4，extended = False
     * - 非数字锁定时，key == VK_LEFT，   extended = False
     * 左方向键按下时：
     * - 　　　　　　　key == VK_LEFT，   extended = True
     *
     * Key  | Num Lock         | not Num Lock    |
     * 0    | VK_NUMPAD0(0x60) | VK_INSERT(0x2D) |
     * 1    | VK_NUMPAD1(0x61) | VK_END   (0x23) |
     * 2    | VK_NUMPAD2(0x62) | VK_DOWN  (0x28) |
     * 3    | VK_NUMPAD3(0x63) | VK_NEXT  (0x22) |
     * 4    | VK_NUMPAD4(0x64) | VK_LEFT  (0x25) |
     * 5    | VK_NUMPAD5(0x65) | VK_CLEAR (0x0C) |
     * 6    | VK_NUMPAD6(0x66) | VK_RIGHT (0x27) |
     * 7    | VK_NUMPAD7(0x67) | VK_HOME  (0x24) |
     * 8    | VK_NUMPAD8(0x68) | VK_UP    (0x26) |
     * 9    | VK_NUMPAD9(0x69) | VK_PRIOR (0x21) |
     * .    | VK_DECIMAL(0x6E) | VK_DELETE(0x2E) |
     */
    if (!extended && ((key >= VK_PRIOR && key <= VK_DOWN) ||
                      (key >= VK_INSERT && key <= VK_DELETE) ||
                      (key == VK_CLEAR)))
    {
        return KEY_CATALOG_BLOCK_NOT_NUMLOCK;
    }

    return KEY_CATALOG_NOT_BLOCK;
}

// ----------

/**
 * IME 的输入数据，包括合成字符串、结果字符串、光标位置、转换目标的位置。
 * 所有窗口共用，因为同一时间只有一个窗口处于输入状态。
 */
static IMEData ime_data = {0};

/**  */
#define IsTargetAttribute(attr) (attr == ATTR_TARGET_CONVERTED || attr == ATTR_TARGET_NOTCONVERTED)

static update_composite_string(HIMC himc)
{
    if (ime_data.composite_str)
    {
        free(ime_data.composite_str); // 清理上次获取的字符
        ime_data.composite_str = NULL;
    }

    // printx(D_IME, CCFR "offset result_str: %zu", offsetof(IMEData, result_str));
    // printx(D_IME, CCFR "offset composite_len_b: %zu", offsetof(IMEData, composite_len_b));
    // printx(D_IME, CCFR "offset composite_len_c: %zu", offsetof(IMEData, composite_len_c));
    // printx(D_IME, CCFR "offset composite_cur_i: %zu", offsetof(IMEData, composite_cur_i));
    // printx(D_IME, CCFR "offset composite_sta_i: %zu", offsetof(IMEData, composite_sta_i));
    // printx(D_IME, CCFR "offset composite_end_i: %zu", offsetof(IMEData, composite_end_i));
    // printx(D_IME, CCFR "offset result_str: %zu", offsetof(IMEData, result_str));
    // printx(D_IME, CCFR "offset result_len_b: %zu", offsetof(IMEData, result_len_b));
    // printx(D_IME, CCFR "offset result_len_c: %zu", offsetof(IMEData, result_len_c));

    bool has_result = false;
    if (himc)
    {
        ime_data.composite_len_b = ImmGetCompositionStringW(himc, GCS_COMPSTR, NULL, 0);
        if (ime_data.composite_len_b > 0)
        {
            has_result = true;
            ime_data.composite_len_c = ime_data.composite_len_b / sizeof(wchar_t);
            ime_data.composite_str = (wchar_t *)malloc(sizeof(wchar_t) * (ime_data.composite_len_c + 1)); // 分配空间
            ImmGetCompositionStringW(himc, GCS_COMPSTR, ime_data.composite_str, ime_data.composite_len_b);
            ime_data.composite_str[ime_data.composite_len_c] = '\0\0'; // 零尾

            printx(D_IME, CCFR "composite_str: %p", ime_data.composite_str);

            ime_data.composite_cur_i = ImmGetCompositionStringW(himc, GCS_CURSORPOS, NULL, 0);

            ime_data.composite_sta_i = -1;
            ime_data.composite_end_i = -1;
            int attribute_size = ImmGetCompositionStringW(himc, GCS_COMPATTR, NULL, 0);
            if (attribute_size > 0)
            {
                char *attribute_data = (char *)malloc(sizeof(char) * (attribute_size + 1));
                if (attribute_data)
                {
                    ImmGetCompositionStringW(himc, GCS_COMPATTR, attribute_data, attribute_size);
                    for (ime_data.composite_sta_i = 0; ime_data.composite_sta_i < attribute_size; ++ime_data.composite_sta_i)
                    {
                        if (IsTargetAttribute(attribute_data[ime_data.composite_sta_i]))
                            break;
                    }
                    for (ime_data.composite_end_i = ime_data.composite_sta_i; ime_data.composite_end_i < attribute_size; ++ime_data.composite_end_i)
                    {
                        if (!IsTargetAttribute(attribute_data[ime_data.composite_end_i]))
                            break;
                    }
                    if (ime_data.composite_sta_i == attribute_size)
                    {
                        // /**
                        //  * This composition clause does not contain any target clauses,
                        //  * i.e. this clauses is an input clause.
                        //  * We treat whole this clause as a target clause.
                        //  */
                        // ime_data.composite_end_i = ime_data.composite_sta_i;
                        // ime_data.composite_sta_i = 0;
                        ime_data.composite_sta_i = -1;
                        ime_data.composite_end_i = -1;
                    }
                    if (ime_data.composite_sta_i != -1 && ime_data.composite_sta_i < attribute_size &&
                        attribute_data[ime_data.composite_sta_i] == ATTR_TARGET_NOTCONVERTED)
                    {
                        ime_data.composite_cur_i = ime_data.composite_sta_i;
                    }
                    free(attribute_data);
                }
            }
        }
    }
    if (!has_result)
    {
        ime_data.composite_str = NULL;
        ime_data.composite_len_b = -1;
        ime_data.composite_len_c = -1;
        ime_data.composite_cur_i = -1;
        ime_data.composite_sta_i = -1;
        ime_data.composite_end_i = -1;
    }
}

static update_result_string(HIMC himc)
{
    if (ime_data.result_str)
    {
        free(ime_data.result_str); // 清理上次获取的字符
        ime_data.result_str = NULL;
    }

    bool has_result = false;
    if (himc)
    {
        ime_data.result_len_b = ImmGetCompositionStringW(himc, GCS_RESULTSTR, NULL, 0);
        if (ime_data.result_len_b > 0)
        {
            has_result = true;
            ime_data.result_len_c = ime_data.result_len_b / sizeof(wchar_t);
            ime_data.result_str = (wchar_t *)malloc(sizeof(wchar_t) * (ime_data.result_len_c + 1)); // 分配空间
            ImmGetCompositionStringW(himc, GCS_RESULTSTR, ime_data.result_str, ime_data.result_len_b);
            ime_data.result_str[ime_data.result_len_c] = '\0\0'; // 零尾

            printx(D_IME, CCFR "result_str: %p", ime_data.result_str);
        }
    }

    if (!has_result)
    {
        ime_data.result_str = NULL;
        ime_data.result_len_b = -1;
        ime_data.result_len_c = -1;
    }
}

static update_char_string(HIMC himc)
{
    if (ime_data.composite_str)
    {
        free(ime_data.composite_str); // 清理上次获取的字符
        ime_data.composite_str = NULL;
    }
}

// ----------

static void fix_ime_WM_DESTROY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (event_callback)
    {
        event_callback(window->wm_pointer, FIEV_WINDOW_DESTORY, NULL);
    }
}

static void fix_ime_WM_BUTTONDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (event_callback)
    {
        event_callback(window->wm_pointer, FIEV_BUTTON_DOWN, NULL);
    }
}

// ----------

static FIRT fix_ime_WM_INPUT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window, LRESULT *r_ret)
{
    RAWINPUT raw;
    UINT raw_size = sizeof(RAWINPUT);
    GetRawInputData((HRAWINPUT)lParam, RID_INPUT, &raw, &raw_size, sizeof(RAWINPUTHEADER));
    if (raw.header.dwType != RIM_TYPEKEYBOARD)
        return FIRT_PASS; // 仅处理键盘消息

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
    bool extended = raw.data.keyboard.Flags & (RI_KEY_E0 | RI_KEY_E1);

    wchar_t key_name[256] = L"??";
    if (D_IME)
    {
        GetKeyNameTextW(MAKELPARAM(0, (extended ? KF_EXTENDED : 0) | (raw.data.keyboard.MakeCode & 0xFF)),
                        (LPWSTR)&key_name, 256);
        printx(D_IME, CCFP "%s：\"%ls\" (%hx), %s",
               key_down ? "按下" : "释放", &key_name, key,
               extended ? "扩展" : "非扩展");
    }

    FIRT result = FIRT_PASS;

    HIMC hImc = ImmGetContext(hWnd);
    if (hImc)
    {
        bool block_ime_test = false;
        /**/ if (raw.data.keyboard.ExtraInformation == myHIMC_INPUT_BLOCK)
        {
            printx(D_IME, CCFP "WM_INPUT 屏蔽（%s-来自回放）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
            result = FIRT_BLOCK;
        }
        else if (raw.data.keyboard.ExtraInformation == myHIMC_INPUT_PASS)
        {
            printx(D_IME, CCFA "WM_INPUT 放行（%s-来自回放）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
            result = FIRT_PASS;

            // 以下代码用于修复 Blender 对非IME字符处理
            // 基本逻辑：对于输入法不处理的字符按键，先停用输入法，然后让Blender处理按键，再重新启用输入法。
            // 这样可以避免 Blender 在输入法启用时，对字符按键判断出现差错的问题。
            // 参考源码：processKeyEvent() 中的 IsImeKeyEvent()

            if (key_down && !ctrl && !alt)
            {
                bool use_fix_direct_input = false;

                if (USE_AND_IS_FILED(window) || USE_AND_IS_SPACE(window))
                {
                    if (data_use_fix_direct_input_all)
                    {
#if defined(FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE)
                        /**
                         * 背景：
                         *
                         *   Blender 假定了所有中文输入法都会在按下部分标点符号时进入文本合成状态。
                         *   因此在 WM_INPUT 时，遇到这些标点符号的按键时，会不处理按键。
                         *   但并不是所有标点符号按键都会触发文本合成，譬如微软拼音输入法中的 “/” 键不会触发文本合成。
                         *   同时，中文输入法有英文标点模式，可以在中文输入状态输入英文。
                         *   同时，部分输入法会根据之前输入的字符自动选择输入的标点为英文还是中文，
                         *   譬如微软拼音输入法会在输入数字后在按主键盘的 “.” 键时，产生英文标点 “.”，此外则产生中文标点 “。"。
                         *
                         *   简单来说，Blender 不支持用户在中文输入模式下输入英文标点符号。
                         *
                         *   源码可参考：HOST_ImeWin32::IsImeKeyEvent()
                         *
                         * 解决：
                         *
                         *   为了解决上面的问题，增加了一个 data_use_fix_direct_input_all 开关。
                         *   当启用时，如果 WM_INPUT 遇到回放的标点符号按键，
                         *   则先停用输入法，让 Blender 处理了按键后，再重新启用输入法。
                         *
                         *   但该方案对于微软拼音输入法存在缺陷。
                         *
                         *   微软拼音输入法会根据之前的按键决定标点符号按键产生英文标点还是中文标点。
                         *
                         *   假设前一个输入的字符为数字，则按下主键盘的 “.” 键时，按键会被屏蔽，然后回放。
                         *   回放由 Blender 处理后，产生英文标点 “.”，
                         *   但回放按键同时也会被输入法处理，此时微软拼音输入法会产生文本合成消息。
                         *   该消息同样会被 Blender 处理，因此额外产生中文标点 “。”。
                         *   即按下 “.” 后，会产生两个字符 “.。”。
                         *
                         *   解决上述问题，目前采取大写锁定的方法。
                         *   对于主键盘的 “.” 键，在发送回放按键前和后，分别发送一个大写锁定按下然后释放的按键序列。
                         *   即让回放的按键处于大写锁定模式中。
                         *   这样可以阻止微软拼音输入法对回放按键产生文本合成消息，
                         *   因为在大写锁定的时候，微软拼音输入法不会触发任何文本合成。
                         *   同时绝大部分的中文输入法都不会在大写锁定时触发任何文本合成（但微软日语输入法会，但不影响）。
                         *
                         * 注意：
                         *
                         *   原则上只需要支持 Blender 所假定的这些标点即可：
                         *     !"$'(),.:;<>?[\]^_`/
                         *   但这里将这个解决机制扩大化，让大部分回放的按键使用相同的方法处理。
                         *   可能存在潜在的问题，但逻辑上大概没有问题。
                         *   这里仅记录上述标点符号对应的虚拟按键：
                         *   - [! ]  Shift  + '1'
                         *   - ['"] [Shift] + VK_OEM_7
                         *   - [$ ]  Shift  + '4'
                         *   - [( ]  Shift  + '9'
                         *   - [) ]  Shift  + '0'
                         *   - [,<] [Shift] + VK_OEM_COMMA
                         *   - [.>] [Shift] + VK_OEM_PERIOD, VK_DECIMAL
                         *   - [;:] [Shift] + VK_OEM_1
                         *   - [/?] [Shift] + VK_OEM_2, VK_DIVIDE
                         *   - [[ ]           VK_OEM_4
                         *   - [\|] [Shift] + VK_OEM_5
                         *   - [] ]           VK_OEM_6
                         *   - [^ ]  Shift  + '6'
                         *   - [_ ]           VK_OEM_MINUS
                         *   - [` ]           VK_OEM_3
                         */
                        use_fix_direct_input = true;
#endif
                    }
                    else if (data_use_fix_direct_input_caps_lock)
                    {
                        /**
                         * 在 Blender 中同样无法在中文输入模式且大写锁定时输入字符，原因和 data_use_fix_direct_input_all 相同。
                         * 即 Blender 假定所有字符按键都会在中文输入模式中触发文本合成，故而不处理，
                         * 但实际上多数输入法在大写锁定时不触发文本合成。
                         * 
                         * 解决方法和 data_use_fix_direct_input_all 相同。
                         * 如果已经启用 data_use_fix_direct_input_all ，则无需考虑 data_use_fix_direct_input_caps_lock，
                         * 因为 data_use_fix_direct_input_all 已经包括 data_use_fix_direct_input_caps_lock。
                         */
                        if ((GetKeyState(VK_CAPITAL) & 0x0001))
                        {
                            use_fix_direct_input = true;
                        }
                    }
                }

                /**
                 * 如果 use_fix_direct_input 则先停用输入法再让 Blender 处理该按键，
                 * 避免 Blender 的额外逻辑导致按键无法输入字符。
                 * 否则，直接放行（result = FIRT_PASS），让 Blender 直接处理。
                 */

                if (use_fix_direct_input)
                {
                    if (get_key_catalog(key, extended) == KEY_CATALOG_BLOCK)
                    {
                        printx(D_IME, CCFA "处理输入法不处理的字符按键：\"%ls\"", key_name);

                        ImmAssociateContext(hWnd, NULL);

                        *r_ret = DefSubclassProc(hWnd, uMsg, wParam, lParam);

                        ImmAssociateContextEx(hWnd, NULL, IACE_DEFAULT);

                        result = FIRT_RETURN;
                    }
                }
            }
        }
        else
        {
            switch (get_key_catalog(key, extended))
            {
            case KEY_CATALOG_BLOCK:
            case KEY_CATALOG_BLOCK_NOT_NUMLOCK:
            {
                printx(D_IME, CCFA "WM_INPUT 屏蔽（%s-插件接管）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
                result = FIRT_BLOCK;
            }
            break;
            case KEY_CATALOG_NOT_BLOCK:
            default:
            {
                printx(D_IME, CCFA "WM_INPUT 放行（%s-无关按键）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
                result = FIRT_PASS;
            }
            break;
            }
        }

        ImmReleaseContext(hWnd, hImc);
    }
    else
    {
        printx(D_IME, CCFA "WM_INPUT 放行（%s-输入法停用）：\"%ls\" (%hx)", key_down ? "按下" : "释放", &key_name, key);
        result = FIRT_PASS;
    }

    return result;
}

static void fix_ime_WM_KEYDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    /**
     * 仅处理输入法启用时，没有被输入法处理的部分按键。
     *
     * 如果当前开启了输入法，并且处于普通状态（非合成状态），且输入法不处理该按键，
     * 并且该按键属于字符按键，则重放一次该按键，
     * 这次重放将开放 WM_INPUT 的通道。
     * 此时，输入法会再次处理该事件，但没有关系，
     * 因为该键不是IME需要处理的，因此IME不会理会该按键，
     * 但会重新触发KEY_DOWN，因此需要通过标记避免再次重发。
     * 只会重发字符按键，控制按键重发会导致问题。
     */

    USHORT key = LOWORD(wParam);
    WORD key_flags = HIWORD(lParam);
    BOOL extended = (key_flags & KF_EXTENDED) == KF_EXTENDED;
    LPARAM extra_info = GetMessageExtraInfo();

    KEY_CATALOG key_cat = get_key_catalog(key, extended);

    HIMC hImc = ImmGetContext(hWnd);

    if (key_cat == KEY_CATALOG_BLOCK && hImc && key != VK_PROCESSKEY)
    {
        ImmReleaseContext(hWnd, hImc);

        LPARAM extra_info = GetMessageExtraInfo();
        if (extra_info != myHIMC_INPUT_PASS && extra_info != myHIMC_INPUT_BLOCK)
        {
            if (D_IME)
            {
                wchar_t key_name[256] = L"??";
                GetKeyNameTextW(lParam, (LPWSTR)&key_name, 256);
                printx(D_IME, "WM_KEYDOWN 回放：\"%ls\" (%x)", key_name, key);
            }

            // 不含扩展标记的扫描码
            WORD wScan = LOBYTE(key_flags); // equal to MapVirtualKey(key, MAPVK_VK_TO_VSC)
            // 释放标记 | 扩展标记E0 | 扩展标记E1（?）
            DWORD dwFlags = (extended ? KEYEVENTF_EXTENDEDKEY : 0);

            printx(D_IME, CCFA "wScan 1: %x", wScan);
            printx(D_IME, CCFA "wScan 2: %x", MapVirtualKey(key, MAPVK_VK_TO_VSC));
            printx(D_IME, CCFA "dwFlags 1: %x", dwFlags | KEYEVENTF_KEYUP);
            printx(D_IME, CCFA "dwFlags 2: %x", KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP);

            // 如果当前按键是重复的按键，则需要发送两个按键消息：
            // 第一个消息为第二个消息进行铺垫，使得第二个消息产生时，按键处于没有按下的状态
            // 第二个消息为正常的按键消息
            int events_count = 0;
            // GetKeyState 返回的是按键消息产生时按键的状态，不包括按键消息自身。
            // 返回值的最高位为 1 时表示按键按下，此时值为负数；否则为释放，此时值为非负数
            if (GetKeyState(key) < 0) // 按键发生时按键已经按下，表示该按键是重复按键
            {
                playback_key_events[events_count].type = INPUT_KEYBOARD;
                playback_key_events[events_count].ki.wVk = key;
                playback_key_events[events_count].ki.wScan = wScan;
                playback_key_events[events_count].ki.dwFlags = dwFlags | KEYEVENTF_KEYUP;
                playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_BLOCK;
                events_count += 1;
                printx(D_IME, "WM_KEYDOWN 中断重复状态");
            }

#if defined(FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE)
            /**
             * 此处特地对主键盘上 “.” 键进行特殊处理，主要是为了让该键在微软拼音输入法中正常使用。
             * 具体原因请通过 FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE 搜索相关代码。
             */
            bool toggle_cap_lock = false;

            if (key == VK_OEM_PERIOD && ((GetKeyState(VK_CAPITAL) & 0x0001) == 0))
            {
                bool ctrl = (GetKeyState(VK_CONTROL) & 0x8000) == 1;
                bool shift = (GetKeyState(VK_SHIFT) & 0x8000) == 1;
                bool alt = (GetKeyState(VK_MENU) & 0x8000) == 1;

                if (!ctrl && !shift && !alt)
                {
                    toggle_cap_lock = true;

                    printx(D_IME, CCFY "WM_KEYDOWN 对 \".\" 特殊处理");
                }
            }

            if (toggle_cap_lock)
            {
                playback_key_events[events_count].type = INPUT_KEYBOARD;
                playback_key_events[events_count].ki.wVk = VK_CAPITAL;
                playback_key_events[events_count].ki.wScan = 0x003A;
                playback_key_events[events_count].ki.dwFlags = 0;
                playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_BLOCK;
                events_count += 1;
                playback_key_events[events_count].type = INPUT_KEYBOARD;
                playback_key_events[events_count].ki.wVk = VK_CAPITAL;
                playback_key_events[events_count].ki.wScan = 0x003A;
                playback_key_events[events_count].ki.dwFlags = KEYEVENTF_KEYUP;
                playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_BLOCK;
                events_count += 1;
            }
#endif /* FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE */

            playback_key_events[events_count].type = INPUT_KEYBOARD;
            playback_key_events[events_count].ki.wVk = key;
            playback_key_events[events_count].ki.wScan = wScan;
            playback_key_events[events_count].ki.dwFlags = dwFlags;
            playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_PASS;
            events_count += 1;

#if defined(FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE)
            if (toggle_cap_lock)
            {
                playback_key_events[events_count].type = INPUT_KEYBOARD;
                playback_key_events[events_count].ki.wVk = VK_CAPITAL;
                playback_key_events[events_count].ki.wScan = 0x003A;
                playback_key_events[events_count].ki.dwFlags = 0;
                playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_BLOCK;
                events_count += 1;
                playback_key_events[events_count].type = INPUT_KEYBOARD;
                playback_key_events[events_count].ki.wVk = VK_CAPITAL;
                playback_key_events[events_count].ki.wScan = 0x003A;
                playback_key_events[events_count].ki.dwFlags = KEYEVENTF_KEYUP;
                playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_BLOCK;
                events_count += 1;
            }
#endif /* FIX_ENG_PUNCTUATION_IN_CHINESE_INPUT_MODE */

            SendInput(events_count, (PINPUT)&playback_key_events, sizeof(INPUT));
        }
        else
        {
            printx(D_IME, "WM_KEYDOWN 回放...完成");
        }
    }

    if (key_cat == KEY_CATALOG_BLOCK_NOT_NUMLOCK)
    {
        LPARAM extra_info = GetMessageExtraInfo();
        if (extra_info != myHIMC_INPUT_PASS && extra_info != myHIMC_INPUT_BLOCK)
        {
            /**
             * 用于修复 Blender 在非数字锁定时，不响应数字键盘上部分按键的问题。
             *
             * 以按下 4 为例，此时按键为 VK_LEFT 但不带 KEYEVENTF_EXTENDEDKEY 标记，
             * 而左方向键为 VK_LEFT 带 KEYEVENTF_EXTENDEDKEY 标记。
             *
             * 修复逻辑：屏蔽按键，模拟该按键带 KEYEVENTF_EXTENDEDKEY 标记的版本。
             */

            WORD wScan = LOBYTE(key_flags); // equal to MapVirtualKey(key, MAPVK_VK_TO_VSC)
            DWORD dwFlags = 0;

            int events_count = 0;
            if (GetKeyState(key) < 0)
            {
                playback_key_events[events_count].type = INPUT_KEYBOARD;
                playback_key_events[events_count].ki.wVk = key;
                playback_key_events[events_count].ki.wScan = wScan;
                playback_key_events[events_count].ki.dwFlags = dwFlags | KEYEVENTF_KEYUP;
                playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_BLOCK;
                events_count += 1;
                printx(D_IME, "WM_KEYDOWN 中断重复状态");
            }

            playback_key_events[events_count].type = INPUT_KEYBOARD;
            playback_key_events[events_count].ki.wVk = key;
            playback_key_events[events_count].ki.wScan = wScan;
            playback_key_events[events_count].ki.dwFlags = dwFlags | KEYEVENTF_EXTENDEDKEY;
            playback_key_events[events_count].ki.dwExtraInfo = myHIMC_INPUT_PASS;
            events_count += 1;

            SendInput(events_count, (PINPUT)&playback_key_events, sizeof(INPUT));
        }
    }
}

static void fix_ime_WM_KEYUP(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    USHORT key = LOWORD(wParam);
    WORD key_flags = HIWORD(lParam);
    BOOL extended = (key_flags & KF_EXTENDED) == KF_EXTENDED;

    KEY_CATALOG key_cat = get_key_catalog(key, extended);

    HIMC hImc = ImmGetContext(hWnd);

    if (key_cat == KEY_CATALOG_BLOCK && hImc && key != VK_PROCESSKEY)
    {
        ImmReleaseContext(hWnd, hImc);

        LPARAM extra_info = GetMessageExtraInfo();
        if (extra_info != myHIMC_INPUT_PASS && extra_info != myHIMC_INPUT_BLOCK)
        {
            if (D_IME)
            {
                wchar_t key_name[256] = L"??";
                GetKeyNameTextW(lParam, (LPWSTR)&key_name, 256);
                printx(D_IME, "WM_KEYUP 回放：\"%ls\" (%x)", key_name, key);
            }

            WORD wScan = LOBYTE(key_flags);
            DWORD dwFlags = (extended ? KEYEVENTF_EXTENDEDKEY : 0);

            playback_key_events[0].type = INPUT_KEYBOARD;
            playback_key_events[0].ki.wVk = key;
            playback_key_events[0].ki.wScan = wScan;
            playback_key_events[0].ki.dwFlags = dwFlags | KEYEVENTF_KEYUP;
            playback_key_events[0].ki.dwExtraInfo = myHIMC_INPUT_PASS;
            SendInput(1, (PINPUT)&playback_key_events, sizeof(INPUT));
        }
        else
        {
            printx(D_IME, "WM_KEYUP 回放...完成");
        }
    }

    if (key_cat == KEY_CATALOG_BLOCK_NOT_NUMLOCK)
    {
        LPARAM extra_info = GetMessageExtraInfo();
        if (extra_info != myHIMC_INPUT_PASS && extra_info != myHIMC_INPUT_BLOCK)
        {
            WORD wScan = LOBYTE(key_flags);
            DWORD dwFlags = KEYEVENTF_EXTENDEDKEY;

            playback_key_events[0].type = INPUT_KEYBOARD;
            playback_key_events[0].ki.wVk = key;
            playback_key_events[0].ki.wScan = wScan;
            playback_key_events[0].ki.dwFlags = dwFlags | KEYEVENTF_KEYUP;
            playback_key_events[0].ki.dwExtraInfo = myHIMC_INPUT_PASS;
            SendInput(1, (PINPUT)&playback_key_events, sizeof(INPUT));
        }
    }
}

// ----------

static bool block_shift_add_mouse_button = false;

static void space_WM_MOUSEDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    if (window->composing)
    {
        // // 取消所有未完成的合成
        // printx(D_IME, "强制取消文字合成（鼠标按键）：%p", hWnd);
        // HIMC himc = ImmGetContext(hWnd);
        // if (himc != NULL)
        // {
        //     ImmNotifyIME(himc, NI_COMPOSITIONSTR, CPS_CANCEL, 0);
        //     ImmReleaseContext(hWnd, himc);
        // }
    }
    else
    {
        /**
         * 当按下 Shift + 鼠标按键 时暂时停用输入法，
         * 当 Shift 键释放时，如果检测到输入法被暂时停用，则重新启用输入法。
         * 该行为主要用于修复：
         * 文字物体编辑时用 Shfit + 鼠标中键 移动视图后，输入法的输入模式(英文/中文）会改变的问题。
         * 针对使用 Shift 键切换输入模式的输入法。
         */
        if ((0x8000 & GetKeyState(VK_SHIFT)) > 0)
        {
            HIMC himc = ImmGetContext(hWnd);
            if (himc)
            {
                printx(D_IME, CCFA "暂停输入法");
                block_shift_add_mouse_button = true;
                ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
                ImmReleaseContext(hWnd, himc);
            }
        }
    }
}

static bool space_WM_KEYUP(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    USHORT key = wParam;
    if (block_shift_add_mouse_button && key == VK_SHIFT)
    {
        printx(D_IME, CCFA "恢复输入法");
        block_shift_add_mouse_button = false;
        ImmAssociateContextEx(hWnd, NULL, IACE_DEFAULT);
    }

    return true;
}

// ----------

static void space_WM_IME_STARTCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    printx(D_IME, "WM_IME_STARTCOMPOSITION");

    window->composing = true;

    if (event_callback)
    {
        event_callback(window->wm_pointer, FIEV_COMP_START, NULL);
    }
}

static void space_WM_IME_COMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    printx(D_IME, "WM_IME_COMPOSITION");

    if (lParam & GCS_COMPATTR)
    {
        printx(D_IME, CCFA "GCS_COMPATTR");
    }
    if (lParam & GCS_COMPCLAUSE)
    {
        printx(D_IME, CCFA "GCS_COMPCLAUSE");
    }
    if (lParam & GCS_COMPREADATTR)
    {
        printx(D_IME, CCFA "GCS_COMPREADATTR");
    }
    if (lParam & GCS_COMPREADCLAUSE)
    {
        printx(D_IME, CCFA "GCS_COMPREADCLAUSE");
    }
    if (lParam & GCS_COMPREADSTR)
    {
        printx(D_IME, CCFA "GCS_COMPREADSTR");
    }
    if (lParam & GCS_COMPSTR)
    {
        printx(D_IME, CCFA "GCS_COMPSTR");
    }
    if (lParam & GCS_CURSORPOS)
    {
        printx(D_IME, CCFA "GCS_CURSORPOS");
    }
    if (lParam & GCS_DELTASTART)
    {
        printx(D_IME, CCFA "GCS_DELTASTART");
    }
    if (lParam & GCS_RESULTCLAUSE)
    {
        printx(D_IME, CCFA "GCS_RESULTCLAUSE");
    }
    if (lParam & GCS_RESULTREADSTR)
    {
        printx(D_IME, CCFA "GCS_RESULTREADSTR");
    }
    if (lParam & GCS_RESULTSTR)
    {
        printx(D_IME, CCFA "GCS_RESULTSTR");
    }

    HIMC hImc = ImmGetContext(hWnd);

    if (lParam & (GCS_COMPATTR | GCS_COMPSTR | GCS_CURSORPOS))
    {
        update_composite_string(hImc);
        update_result_string(NULL);
    }
    else if (lParam & GCS_RESULTSTR)
    {
        update_composite_string(NULL);
        update_result_string(hImc);
    }

    // update_composite_string(hImc);
    // update_result_string(hImc);

    ImmReleaseContext(hWnd, hImc);

    if (event_callback)
    {
        event_callback(window->wm_pointer, FIEV_COMP_INPUT, &ime_data);
    }
}

static void space_WM_IME_ENDCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window)
{
    printx(D_IME, "WM_IME_ENDCOMPOSITION");

    window->composing = false;

    if (event_callback)
    {
        event_callback(window->wm_pointer, FIEV_COMP_END, NULL);
    }
}

// ----------

static LRESULT Subclassproc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData)
{
    WindowData *window = (WindowData *)dwRefData;

    switch (uMsg)
    {
    case WM_DESTROY:
    {
        fix_ime_WM_DESTROY(hWnd, uMsg, wParam, lParam, window);
        unhook_window(window->wm_pointer);
    }
    break;
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
        get_ime_invoker(window);

        if (data_use_fix_ime_for_field || data_use_fix_ime_for_space)
        {
            fix_ime_WM_BUTTONDOWN(hWnd, uMsg, wParam, lParam, window);
        }

        if (USE_AND_IS_SPACE(window))
        {
            space_WM_MOUSEDOWN(hWnd, uMsg, wParam, lParam, window);
        }
    }
    break;
    case WM_INPUT:
    {
        get_ime_invoker(window);

        if (USE_AND_IS_FILED(window) || USE_AND_IS_SPACE(window))
        {
            LRESULT r_ret;
            switch (fix_ime_WM_INPUT(hWnd, uMsg, wParam, lParam, window, &r_ret))
            {
            case FIRT_BLOCK:
                return DefWindowProc(hWnd, uMsg, wParam, lParam);
                break;
            case FIRT_RETURN:
                return r_ret;
                break;
            }
        }
    }
    break;
    case WM_KEYDOWN:
    case WM_SYSKEYDOWN: // 在 F10、Alt + ... 按键时触发
    {
        get_ime_invoker(window);

        if (data_use_fix_ime_for_field || data_use_fix_ime_for_space)
        {
            fix_ime_WM_BUTTONDOWN(hWnd, uMsg, wParam, lParam, window);
        }

        if (USE_AND_IS_FILED(window) || USE_AND_IS_SPACE(window))
        {
            fix_ime_WM_KEYDOWN(hWnd, uMsg, wParam, lParam, window);
            return 0;
        }
    }
    break;
    case WM_KEYUP:
    case WM_SYSKEYUP:
    {
        get_ime_invoker(window);

        if (USE_AND_IS_FILED(window) || USE_AND_IS_SPACE(window))
        {
            fix_ime_WM_KEYUP(hWnd, uMsg, wParam, lParam, window);

            if (USE_AND_IS_SPACE(window))
            {
                space_WM_KEYUP(hWnd, uMsg, wParam, lParam, window);
            }
            return 0;
        }
    }
    break;
    // case WM_IME_NOTIFY:
    // {
    //     printx(D_IME, "WM_IME_NOTIFY：%d", wParam);
    //     HIMC hImc = ImmGetContext(hWnd);
    //     if (hImc)
    //     {
    //         DWORD conversion_mode, sentence_mode;
    //         ImmGetConversionStatus(hImc, &conversion_mode, &sentence_mode);
    //         printx(D_IME, "conversion_mode：%x,  sentence_mode: %x", conversion_mode, sentence_mode);
    //         ImmReleaseContext(hWnd, hImc);
    //     }
    //     if (wParam == IMN_SETOPENSTATUS)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_SETOPENSTATUS (%d)", IMN_SETOPENSTATUS);
    //     }
    //     else if (wParam == IMN_SETCONVERSIONMODE)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_SETCONVERSIONMODE (%d)", IMN_SETCONVERSIONMODE);
    //     }
    //     else if (wParam == IMN_SETSENTENCEMODE)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_SETSENTENCEMODE (%d)", IMN_SETSENTENCEMODE);
    //     }
    //     else if (wParam == IMN_OPENCANDIDATE)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_OPENCANDIDATE (%d)", IMN_OPENCANDIDATE);
    //     }
    //     else if (wParam == IMN_CLOSECANDIDATE)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_CLOSECANDIDATE (%d)", IMN_CLOSECANDIDATE);
    //     }
    //     else if (wParam == IMN_SETCANDIDATEPOS)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_SETCANDIDATEPOS (%d)", IMN_SETCANDIDATEPOS);
    //     }
    //     else if (wParam == IMN_CHANGECANDIDATE)
    //     {
    //         printx(D_IME, "WM_IME_NOTIFY：IMN_CHANGECANDIDATE (%d)", IMN_CHANGECANDIDATE);
    //     }
    // }
    // break;
    // case WM_IME_SETCONTEXT:
    // {
    //     BOOL fSet = (BOOL)wParam;
    //     DWORD iShow = (DWORD)lParam;
    //     printx(D_IME, "WM_IME_SETCONTEXT: %s, %x", fSet ? "True" : "False", iShow);
    // }
    // break;
    case WM_IME_STARTCOMPOSITION:
    {
        if (USE_AND_IS_SPACE(window))
        {
            space_WM_IME_STARTCOMPOSITION(hWnd, uMsg, wParam, lParam, window);
            return 0; // 屏蔽消息，避免Blender更新候选窗口位置而导致窗口跳动
        }
    }
    break;
    case WM_IME_COMPOSITION:
    {
        if (USE_AND_IS_SPACE(window))
        {
            space_WM_IME_COMPOSITION(hWnd, uMsg, wParam, lParam, window);
            return 0; // 屏蔽消息，避免Blender更新候选窗口位置而导致窗口跳动
        }
    }
    break;
    case WM_IME_ENDCOMPOSITION:
    {
        if (USE_AND_IS_SPACE(window))
        {
            space_WM_IME_ENDCOMPOSITION(hWnd, uMsg, wParam, lParam, window);
            return 0; // 屏蔽消息，避免Blender更新候选窗口位置而导致窗口跳动
        }
    }
    break;
    }

    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_fix_ime_debug(bool enable)
{
    data_use_fix_ime_debug = enable;

    return data_use_fix_ime_debug;
}

extern __declspec(dllexport) bool use_fix_ime(bool enable, FixIMEEventCallback event_callback_)
{
    if (enable)
    {
        printx(D_IME, "hook startup...");

        event_callback = event_callback_;

        data_use_fix_ime = true;

        printx(D_IME, "hook startup...finish");
    }
    else
    {
        printx(D_IME, "hook shutdown...");

        event_callback = NULL;

        if (ime_data.composite_str)
        {
            free(ime_data.composite_str);
        }
        if (ime_data.result_str)
        {
            free(ime_data.result_str);
        }
        memset(&ime_data, 0, sizeof(IMEData));

        printx(D_IME, "释放窗口...[窗口个数：%d]", window_datas_head.count);

        WindowData *window = NULL;
        while (window_datas_head.count != 0)
        {
            window = window_datas_head.first;
            unhook_window(window->wm_pointer);
        }

        window_datas_clean();

        data_use_fix_ime_for_field = false;
        data_use_fix_ime_for_space = false;

        data_use_fix_ime = false;

        printx(D_IME, "hook shutdown...finish");
    }

    return data_use_fix_ime;
}

extern __declspec(dllexport) bool use_fix_ime_for_field(bool enable)
{
    data_use_fix_ime_for_field = enable;

    return true;
}

extern __declspec(dllexport) bool use_fix_ime_for_space(bool enable)
{
    data_use_fix_ime_for_space = enable;

    return true;
}

extern __declspec(dllexport) bool use_fix_direct_input_caps_lock(bool enable)
{
    data_use_fix_direct_input_caps_lock = enable;

    return true;
}

extern __declspec(dllexport) bool use_fix_direct_input_all(bool enable)
{
    data_use_fix_direct_input_all = enable;

    return true;
}

extern __declspec(dllexport) bool hook_window(void *wm_pointer)
{
    if (wm_pointer == NULL)
    {
        return false;
    }

    void *gw_pointer = get_gw_ptr(wm_pointer);

    WindowData *window = find_window_by_wm_ptr(wm_pointer);

    if (!window)
    {
        HWND hWnd = get_handle(wm_pointer);
        if (hWnd)
        {
            WCHAR class_name[100] = {0};
            GetClassName(hWnd, (LPWSTR)&class_name, 100);
            if (lstrcmp((LPWSTR)&class_name, TEXT("GHOST_WindowClass")) == 0)
            {
                // 仅捕获 Blender 自身创建的窗口（主窗口、从窗口）

                WindowData *window = (WindowData *)malloc(sizeof(WindowData));
                memset(window, 0, sizeof(WindowData));

                if (SetWindowSubclass(hWnd, Subclassproc, (UINT_PTR)hWnd, (DWORD_PTR)window))
                {
                    window->wm_pointer = wm_pointer;
                    window->gw_pointer = gw_pointer;
                    window->handle = hWnd;

                    window_datas_add(window);

                    if (D_IME)
                    {
                        WCHAR _class_name[100] = {0};
                        GetClassName(hWnd, (LPWSTR)&_class_name, 100);
                        printx(D_IME, "捕获窗口：%p [窗口类名称：%ls]", hWnd, &_class_name);
                        GetWindowText(hWnd, (LPWSTR)&_class_name, 100);
                        printx(D_IME, "窗口名称：\"%ls\"", &_class_name);
                        printx(D_IME, "WM 指针：%p", window->wm_pointer);
                        printx(D_IME, "GW 指针：%p", window->gw_pointer);
                    }

                    return true;
                }
                else
                {
                    free(window);

                    printx(D_ERR, CCBR "捕获窗口失败[%p (wm)]：窗口子类化失败", wm_pointer);
                }
            }
            else
            {
                printx(D_ERR, CCBR "捕获窗口失败[%p (wm), %p (hWnd)]：窗口不符合条件", wm_pointer, hWnd);
            }
        }
        else
        {
            printx(D_ERR, CCBR "捕获窗口失败[%p (wm), %p (gw)]：没有找到对应窗口", wm_pointer, gw_pointer);
        }
    }
    else
    {
        printx(D_ERR, CCFR "窗口早已捕获[%p (wm), %p (gw), %p (hWnd)]", wm_pointer, gw_pointer, window->handle);
    }

    return false;
}

extern __declspec(dllexport) bool unhook_window(void *wm_pointer)
{
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (window)
    {
        if (RemoveWindowSubclass(window->handle, Subclassproc, (UINT_PTR)window->handle))
        {
            if (D_IME)
            {
                WCHAR _class_name[100] = {0};
                GetClassName(window->handle, (LPWSTR)&_class_name, 100);
                printx(D_IME, "释放窗口：%p [窗口类名称：%ls]", window->handle, &_class_name);
                GetWindowText(window->handle, (LPWSTR)&_class_name, 100);
                printx(D_IME, "窗口名称：\"%ls\"", &_class_name);
            }
        }
        else
        {
            printx(D_ERR, CCBR "释放窗口失败：%p (hw)", window->handle);
        }

        window_datas_remove(window); // 无论怎样都移除窗口数据

        return true;
    }

    return false;
}

extern __declspec(dllexport) bool window_is_active(void *wm_pointer)
{
    if (wm_pointer == NULL)
    {
        return false;
    }
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
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
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (window)
    {
        return (window->handle == GetCapture());
    }
    return false;
}

extern __declspec(dllexport) IMEInvoker ime_invoker_get(void *wm_pointer)
{
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (window == NULL)
        return INVOKER_NONE;

    return get_ime_invoker(window);
}

extern __declspec(dllexport) bool ime_is_enabled(void *wm_pointer)
{
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (window == NULL)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (himc)
    {
        ImmReleaseContext(hwnd, himc);
        return true;
    }
    return false;
}

extern __declspec(dllexport) bool ime_enable(void *wm_pointer, IMEInvoker invoker)
{
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (!window)
    {
        printx(D_IME, CCFR "找不到窗口(ime_enable)：%p", wm_pointer);
        return false;
    }

    HWND hwnd = window->handle;

    window->invoker = invoker;

    ImmAssociateContextEx(hwnd, NULL, IACE_DEFAULT);

    return true;
}

extern __declspec(dllexport) bool ime_disable(void *wm_pointer)
{
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (!window)
    {
        printx(D_IME, CCFR "找不到窗口(ime_disable)：%p", wm_pointer);
        return false;
    }

    HWND hwnd = window->handle;

    window->invoker = INVOKER_NONE;

    ImmAssociateContext(hwnd, NULL);

    return true;
}

extern __declspec(dllexport) bool ime_move_candidate_window(void *wm_pointer, int c_l, int c_t, int c_w, int c_h, int e_l, int e_t, int e_w, int e_h, bool show_caret)
{
    WindowData *window = find_window_by_wm_ptr(wm_pointer);
    if (!window)
        return false;

    HWND hwnd = window->handle;
    HIMC himc = ImmGetContext(hwnd);
    if (!himc)
        return false;

    c_w = max(0, c_w);
    c_h = max(0, c_h);
    e_w = max(0, e_w);
    e_h = max(0, e_h);

    CANDIDATEFORM candidate_form = {0};
    candidate_form.dwIndex = 0;
    candidate_form.dwStyle = CFS_EXCLUDE;
    candidate_form.ptCurrentPos.x = c_l;
    candidate_form.ptCurrentPos.y = c_t;
    candidate_form.rcArea.left = e_l;
    candidate_form.rcArea.top = e_t;
    candidate_form.rcArea.right = e_l + e_w;
    candidate_form.rcArea.bottom = e_t + e_h;
    ImmSetCandidateWindow(himc, &candidate_form);
    ImmReleaseContext(hwnd, himc);

    DestroyCaret();
    CreateCaret(hwnd, NULL, max(1, c_w), max(2, c_h));
    SetCaretPos(c_l, c_t);
    if (show_caret)
    {
        ShowCaret(hwnd);
    }

    return true;
}
