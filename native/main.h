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
//  标记  公共

extern bool data_use_debug;

extern HANDLE process_handle;
extern DWORD process_id;
extern DWORD thread_id;

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
//  标记  导出

extern __declspec(dllexport) bool use_debug(bool enable);

extern __declspec(dllexport) bool init();

#endif