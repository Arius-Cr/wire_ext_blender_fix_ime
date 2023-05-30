#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <Windows.h>
// Self
#include "utils.h"
#include "main.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  内部功能

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  全局功能

extern bool data_is_debug = false;

extern HANDLE process_handle = NULL;
extern DWORD process_id = 0;
extern DWORD thread_id = 0;

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  对外功能

extern __declspec(dllexport) bool use_debug(bool enable)
{
    data_is_debug = enable;

    return true;
}

extern __declspec(dllexport) bool init()
{
    setup_console_encoding();

    process_handle = GetCurrentProcess();
    process_id = GetProcessId(process_handle);
    thread_id = GetCurrentThreadId();

    DEBUGI(1, "process_id: %x, thread_id: %x", process_id, thread_id);

    return true;
}