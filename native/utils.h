#ifndef UTILS_H_
#define UTILS_H_

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <locale.h>
// Windows
#include <Windows.h>

// MSVC 2017 需要开启 /experimental:preprocessor- 以去除不等参数前的逗号

// 输出调试信息
#define DEBUGI(condition, message, ...)     \
    {                                       \
        if (data_is_debug && condition)     \
        {                                   \
            printf("INFO: ");               \
            printf(message, ##__VA_ARGS__); \
            printf("\n");                   \
        }                                   \
    }

// 输出错误信息
#define DEBUGE(condition, ret, message, ...) \
    {                                        \
        if (data_is_debug && condition)      \
        {                                    \
            printf("ERROR: ");               \
            printf(message, ##__VA_ARGS__);  \
            printf("\n");                    \
            ret;                             \
        }                                    \
    }

void setup_console_encoding();

#endif