#ifndef _BLENDER_H_
#define _BLENDER_H_

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
// Windows
#include <windows.h>
// Self
#include "main.h"
#include "utils.h"
#include "ime.h"

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool wmWindow_is_but_active(void *wm_pointer);

extern __declspec(dllexport) bool wmWindow_is_pop_active(void *wm_pointer);

extern __declspec(dllexport) void *wmWindow_active_screen_get(void *wm_pointer);

extern __declspec(dllexport) void *wmWindow_active_region_get(void *wm_pointer);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) int SpaceText_lheight_px_get(void *SpaceText);

extern __declspec(dllexport) int SpaceText_cwidth_px_get(void *SpaceText);

extern __declspec(dllexport) int SpaceText_line_number_display_digits_get(void *SpaceText);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) void blender_data_init();

#endif
