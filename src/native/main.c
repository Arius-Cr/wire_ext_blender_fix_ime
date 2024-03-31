#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <Windows.h>
// Self
#include "utils.h"
#include "main.h"
#include "blender.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern bool data_use_debug = false;

extern HANDLE process_handle = NULL;
extern DWORD process_id = 0;
extern DWORD thread_id = 0;

extern int ver_m = 0, ver_s = 0, ver_r = 0;

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool use_debug(bool enable)
{
    data_use_debug = enable;

    return data_use_debug;
}

extern __declspec(dllexport) bool init(int _ver_m, int _ver_s, int _ver_r)
{
    setup_console_encoding();

    process_handle = GetCurrentProcess();
    process_id = GetProcessId(process_handle);
    thread_id = GetCurrentThreadId();

    printx(D_DLL, "process_id: %X, thread_id: %X", process_id, thread_id);

    ver_m = _ver_m, ver_s = _ver_s, ver_r = _ver_r;

    blender_data_init();

    return true;
}
