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
//  标记  公共

#define D_HOK data_use_hook_debug

extern bool data_use_hook_debug;

extern bool data_use_hook;

// 用于记录窗口信息的缓存的"链表"，仅用于提升窗口类型判断的效率
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

extern WindowData *get_window_by_handle(HWND handle);
extern WindowData *get_window_by_gw(void *gw_pointer);
extern WindowData *get_window_by_wm(void *wm_pointer);
extern inline void *get_gw_pointer(void *wm_pointer);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_hook_debug(bool enable);

extern __declspec(dllexport) bool use_hook(bool enable);

extern __declspec(dllexport) bool window_associate(void *wm_pointer);

extern __declspec(dllexport) bool window_is_active(void *wm_pointer);

extern __declspec(dllexport) bool window_is_mouse_capture(void *wm_pointer);

#endif