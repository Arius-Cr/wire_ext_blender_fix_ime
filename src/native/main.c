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

extern int bl_ver_main = 0;
extern int bl_ver_minor = 0;
extern int bl_ver_patch = 0;
extern int bl_ver = 0;

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool use_debug(bool enable)
{
    data_use_debug = enable;

    return data_use_debug;
}

extern __declspec(dllexport) bool init(int bl_ver_main_, int bl_ver_minor_, int bl_ver_patch_)
{
    bl_ver_main = bl_ver_main_;
    bl_ver_minor = bl_ver_minor_;
    bl_ver_patch = bl_ver_patch_;
    bl_ver = BL_VER(bl_ver_main_, bl_ver_minor_, bl_ver_patch_);

    // 要在 Blender 的控制台输出中文，只需要确保编译时字符串使用 UTF-8 编码即可。
    // 即编译时添加 /source-charset:utf-8 /execution-charset:utf-8 选项。

    process_handle = GetCurrentProcess();
    process_id = GetProcessId(process_handle);
    thread_id = GetCurrentThreadId();

    printx(D_DLL, "process_id: %X, thread_id: %X", process_id, thread_id);

    blender_data_init();

    return true;
}

extern __declspec(dllexport) bool uninit()
{
    blender_data_uninit();

    return true;
}

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

BOOL WINAPI DllMain(
    HINSTANCE hinstDLL, // handle to DLL module
    DWORD fdwReason,    // reason for calling function
    LPVOID lpvReserved) // reserved
{
    // Perform actions based on the reason for calling.
    switch (fdwReason)
    {
    case DLL_PROCESS_ATTACH:
        // Initialize once for each new process.
        // Return FALSE to fail DLL load.
        break;

    case DLL_THREAD_ATTACH:
        // Do thread-specific initialization.
        break;

    case DLL_THREAD_DETACH:
        // Do thread-specific cleanup.
        break;

    case DLL_PROCESS_DETACH:

        if (lpvReserved != NULL)
        {
            break; // do not do cleanup if process termination scenario
        }

        // Perform any necessary cleanup.

        blender_data_uninit();

        break;
    }
    return TRUE; // Successful DLL_PROCESS_ATTACH.
}
