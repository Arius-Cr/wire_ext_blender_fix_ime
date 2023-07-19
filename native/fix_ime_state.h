#ifndef FIX_IME_STATE_H_
#define FIX_IME_STATE_H_
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

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  公共

extern bool data_use_fix_ime_state;

// 处理鼠标和焦点相关的事件，在窗口处理过程中调用
extern void fix_ime_state_with_mouse_event(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

// 处理键盘相关的事件，在窗口处理过程中调用
extern void fix_ime_state_with_key_event(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_fix_ime_state(bool enable);

#endif