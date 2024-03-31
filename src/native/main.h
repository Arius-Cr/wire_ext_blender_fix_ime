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

// Blender 的版本号
extern int ver_m, ver_s, ver_r;

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool use_debug(bool enable);

extern __declspec(dllexport) bool init(int ver_m, int ver_s, int ver_r);

#endif
