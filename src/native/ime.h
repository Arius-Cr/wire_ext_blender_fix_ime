#ifndef HOOK_H_
#define HOOK_H_
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <windows.h>
#include <imm.h>
#pragma comment(lib, "Imm32.lib")
// Self
#include "utils.h"
#include "main.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

#define D_IME data_use_fix_ime_debug

extern bool data_use_fix_ime_debug;

/**
 * 表示谁启用了 IME。
 */
typedef enum
{
    /* 当前 IME 没有激活 */
    INVOKER_NONE = 0,
    /* 当前 IME 由 输入框 激活 */
    INVOKER_FIELD,
    /* 当前 IME 由 3D视图 - 文本编辑模式 激活 */
    INVOKER_VIEW3D_TEXT_EDIT,
    /* 当前 IME 由 文本编辑器 激活 */
    INVOKER_TEXT_EDITOR,
    /* 当前 IME 由 控制台 激活 */
    INVOKER_CONSOLE,
    /* 当前 IME 由 序列编辑器 激活 */
    INVOKER_SEQUENCE_EDITOR_TEXT_EDIT,
} IMEInvoker;

/**
 * 用于 FixIMEEventCallback 回调函数中的 event 参数。
 */
typedef enum tag_FIEV
{
    FIEV_NONE = 0,
    FIEV_COMP_START,
    FIEV_COMP_INPUT,
    FIEV_COMP_END,
    FIEV_BUTTON_DOWN,
    FIEV_LOST_FOCUS,
    FIEV_WINDOW_DESTORY,
} FIEV;

/**
 * 用于 FixIMEEventCallback 回调函数中的 data 参数。（仅适用于 FIEV_COMP_INPUT 事件）
 * 保存了 WM_IME_COMPOSITION 事件触发时的 IME 输入数据。
 */
typedef struct tag_IMEData
{
    wchar_t *composite_str; // 当前的合成字串
    LONG composite_len_b;   // 字串字节长度
    LONG composite_len_c;   // 字串字符数量
    LONG composite_cur_i;   // 光标位置（字符索引）
    LONG composite_sta_i;   // 转换目标起始位置（字符索引）
    LONG composite_end_i;   // 转换目标结束位置（字符索引）
    char _pad1[4];
    wchar_t *result_str; // 当前的结果字串
    LONG result_len_b;   // 字串字节长度
    LONG result_len_c;   // 字串字符数量

    wchar_t *char_str; // 额外的字符（仅适用于韩语输入法）
} IMEData;

typedef void FixIMEEventCallback(void *wm_pointer, FIEV event, void *data);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool use_fix_ime_debug(bool enable);

extern __declspec(dllexport) bool use_fix_ime(bool enable, FixIMEEventCallback event_callback);

extern __declspec(dllexport) bool use_fix_ime_for_field(bool enable);

extern __declspec(dllexport) bool use_fix_ime_for_space(bool enable);

extern __declspec(dllexport) bool use_fix_direct_input_caps_lock(bool enable);

extern __declspec(dllexport) bool use_fix_direct_input_all(bool enable);

/**
 * 捕获窗口，以便检查发送到窗口的消息。
 */
extern __declspec(dllexport) bool hook_window(void *wm_pointer);

extern __declspec(dllexport) bool unhook_window(void *wm_pointer);

extern __declspec(dllexport) bool window_is_active(void *wm_pointer);

extern __declspec(dllexport) bool window_is_mouse_capture(void *wm_pointer);

extern __declspec(dllexport) IMEInvoker ime_invoker_get(void *wm_pointer);

extern __declspec(dllexport) bool ime_is_enabled(void *wm_pointer);

extern __declspec(dllexport) bool ime_enable(void *wm_pointer, IMEInvoker invoker);

extern __declspec(dllexport) bool ime_disable(void *wm_pointer);

extern __declspec(dllexport) bool ime_move_candidate_window(void *wm_pointer, int c_l, int c_t, int c_w, int c_h, int e_l, int e_t, int e_w, int e_h, bool show_caret);

#endif
