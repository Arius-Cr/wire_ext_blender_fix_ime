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
#include "main.h"
#include "utils.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序内功能

#define D_HOK data_use_hook_debug

extern bool data_use_hook_debug;

extern bool data_use_hook;

// 用于记录窗口信息的缓存的"链表"，仅用于提升窗口类型判断的效率
typedef struct tag_node_WindowData
{
    struct tag_node_WindowData *next; // 节点指针
    HWND handle;                      // 窗口句柄

    /**
     * Blender 中 GHOST_WindowWin32 和 wmWindow 实例的指针
     * 该成员主要用于确定 BPY 中的窗口对应的实际窗口的句柄。
     */
    void *gw_pointer;
    void *wm_pointer;

} WindowData;
typedef struct tag_head_WindowData
{
    int count;
    WindowData *first;
} WindowDataHead;
extern WindowData *window_datas;
extern WindowDataHead window_datas_head;
extern WindowData *window_datas_for_each(WindowData **window);
extern WindowData *window_datas_add(WindowData *window);
extern bool window_datas_remove(WindowData *window);
extern bool window_datas_clean();

extern WindowData *get_window_by_wm(void *wm_pointer);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  程序外功能

extern __declspec(dllexport) bool use_hook_debug(bool enable);

extern __declspec(dllexport) bool use_hook(bool enable);

extern __declspec(dllexport) bool window_associate_pointer(void *pointer);

extern __declspec(dllexport) bool window_is_active(void *pointer);

extern __declspec(dllexport) bool window_is_mouse_capture(void *pointer);

#endif