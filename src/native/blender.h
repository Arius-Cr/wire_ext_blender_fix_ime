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

extern __declspec(dllexport) bool wmWindow_is_txt_active(void *wm_pointer);

extern __declspec(dllexport) bool wmWindow_is_pop_active(void *wm_pointer);

extern __declspec(dllexport) void *wmWindow_active_screen_get(void *wm_pointer);

extern __declspec(dllexport) void *wmWindow_active_region_get(void *wm_pointer);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) int SpaceText_lheight_px_get(void *SpaceText);

extern __declspec(dllexport) int SpaceText_cwidth_px_get(void *SpaceText);

extern __declspec(dllexport) int SpaceText_line_number_display_digits_get(void *SpaceText);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) bool Strip_is_text_editing_active(void *TextStrip);

extern __declspec(dllexport) int Strip_text_cursor_offset_get(void *TextStrip);

extern __declspec(dllexport) void Strip_text_cursor_offset_set(void *TextStrip, int offset);

extern __declspec(dllexport) int Strip_text_selection_start_offset_get(void *TextStrip);

extern __declspec(dllexport) void Strip_text_selection_start_offset_set(void *TextStrip, int offset);

extern __declspec(dllexport) int Strip_text_selection_end_offset_get(void *TextStrip);

extern __declspec(dllexport) void Strip_text_selection_end_offset_set(void *TextStrip, int offset);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern __declspec(dllexport) int BLF_fixed_width(wchar_t *font_path, float font_size);

// ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

extern /*__declspec(dllexport)*/ void blender_data_init();

extern /*__declspec(dllexport)*/ void blender_data_uninit();

extern __declspec(dllexport) bool blender_data_set(const wchar_t *name_id, size_t value);

#endif
