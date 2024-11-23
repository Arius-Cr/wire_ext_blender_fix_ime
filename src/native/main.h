#ifndef MAIN_H_
#define MAIN_H_

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <Windows.h>
// Self
#include "utils.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern bool data_use_debug;

extern HANDLE process_handle;
extern DWORD process_id;
extern DWORD thread_id;

extern int bl_ver_main;
extern int bl_ver_minor;
extern int bl_ver_patch;
extern int bl_ver;

#define BL_VER(major, minor, patch) (major * 10000 + minor * 100 + patch)

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool use_debug(bool enable);

extern __declspec(dllexport) bool init(int bl_ver_main, int bl_ver_minor, int bl_ver_patch);

extern __declspec(dllexport) bool uninit();

#endif
