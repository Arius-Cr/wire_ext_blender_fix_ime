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

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序内功能

extern bool data_use_fix_ime_input; // 用户是否启用【修复输入法输入】特性

extern HIMC himc_custom; // 自定的输入上下文，调用 ime_input_enable() 时会将该上下文和窗口关联

extern bool himc_enabled; // 是否已经启用【自定义输入流程】，调用 ime_input_enable() 时会将该值设为 true

extern bool himc_composition; // 是否已经处于合成流程

extern bool fix_ime_input_WM_INPUT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_KEYDOWN(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_KEYUP(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_IME_NOTIFY(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_IME_SETCONTEXT(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_IME_STARTCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_IME_COMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

extern void fix_ime_input_WM_IME_ENDCOMPOSITION(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序外功能

// 由脚本调用，启停【使用输入法输入文字】功能
extern __declspec(dllexport) bool use_fix_ime_input(bool enable);

// 由脚本调用，在进入特定状态后主动启用输入法
extern __declspec(dllexport) bool ime_input_enable(void *wm_pointer);

// 由脚本调用，在退出特定状态后主动关闭输入法
extern __declspec(dllexport) bool ime_input_disable(void *wm_pointer);

// 由脚本调用，获取合成文本
extern __declspec(dllexport) wchar_t *ime_text_get();

// 由脚本调用，获取合成文本中光标的位置
extern __declspec(dllexport) int ime_text_caret_pos_get();

// 由脚本调用，获取当前是否处于合成状态
extern __declspec(dllexport) bool is_in_composition();

// 由脚本调用，更新候选窗口的位置
extern __declspec(dllexport) bool candidate_window_position_update_font_edit(void *wm_pointer, float p);

extern __declspec(dllexport) bool candidate_window_position_update_text_editor(void *wm_pointer, int x, int y);

extern __declspec(dllexport) bool candidate_window_position_update_console(void *wm_pointer, int x, int y, int l, int t, int r, int b);

#endif