#ifndef FIX_IME_INPUT_H_
#define FIX_IME_INPUT_H_

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

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  公共

extern bool data_use_fix_ime_input; // 用户是否启用【修复输入法输入】特性

extern HIMC himc_custom; // 自定的输入上下文，调用 ime_input_enable() 时会将该上下文和窗口关联

extern bool himc_enabled; // 是否已经启用【自定义输入流程】，调用 ime_input_enable() 时会将该值设为 true

extern bool himc_composition; // 是否已经处于合成流程

extern bool himc_block_shift_mouse_button; // 表示 Shift + 鼠标按键时临时停用输入法

extern void fix_ime_input_WM_BUTTONDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_MOUSEBUTTONDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_KILLFOCUS(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_DESTROY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern bool fix_ime_input_WM_INPUT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_KEYDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_KEYUP(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_IME_NOTIFY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_IME_SETCONTEXT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_IME_STARTCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_IME_COMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

extern void fix_ime_input_WM_IME_ENDCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, WindowData *window);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

typedef void CompositionCallback(void *wm_pointer, int event, wchar_t *text, int pos);
typedef void ButtonDownCallback(void *wm_pointer);
typedef void LostFocusCallback(void *wm_pointer);
typedef void WindowDestoryCallback(void *wm_pointer);

// 由脚本调用，启停【使用输入法输入文字】功能
extern __declspec(dllexport) bool use_fix_ime_input(
    bool enable,
    CompositionCallback composition_callback_,
    ButtonDownCallback button_down_callback_,
    LostFocusCallback lost_focus_callback_,
    WindowDestoryCallback windown_destory_callback_);

// 由脚本调用，在进入特定状态后主动启用输入法
extern __declspec(dllexport) bool ime_input_enable(void *wm_pointer);

// 由脚本调用，在退出特定状态后主动关闭输入法
extern __declspec(dllexport) bool ime_input_disable(void *wm_pointer);

// 由脚本调用，更新候选窗口的位置
extern __declspec(dllexport) bool candidate_window_position_update_font_edit(void *wm_pointer, float p, bool show_caret);

extern __declspec(dllexport) bool candidate_window_position_update_text_editor(void *wm_pointer, int x, int y, int h, bool show_caret);

extern __declspec(dllexport) bool candidate_window_position_update_console(void *wm_pointer, int l, int t, int r, int b, bool show_caret);

// 返回当前窗口中是否有输入框处于激活状态
extern __declspec(dllexport) bool is_input_box_active(void *wm_pointer);

#endif