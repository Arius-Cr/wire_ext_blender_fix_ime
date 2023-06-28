#ifndef UTILS_H_
#define UTILS_H_

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <locale.h>
// Windows
#include <Windows.h>

// MSVC 2017 需要开启 /experimental:preprocessor- 以去除不等参数前的逗号

#define CCZ0 "\033[0m"
#define CCZL "\033[0m\n"

#define CCFR "\033[1;31;40m" // 红字，黑底
#define CCFG "\033[1;32;40m" // 绿字，黑底
#define CCFY "\033[1;33;40m" // 黄字，黑底
#define CCFB "\033[1;34;40m" // 蓝字，黑底
#define CCFP "\033[1;35;40m" // 紫字，黑底
#define CCFA "\033[1;36;40m" // 青字，黑底

#define CCBR "\033[1;37;41m" // 白字，红底
#define CCBG "\033[1;37;42m" // 白字，绿底
#define CCBY "\033[1;37;43m" // 白字，黄底
#define CCBB "\033[1;37;44m" // 白字，蓝底
#define CCBP "\033[1;37;45m" // 白字，紫底
#define CCBA "\033[1;37;46m" // 白字，青底

// 输出普通信息
#define DEBUGI(condition, message, ...)                   \
    {                                                     \
        if (data_use_debug && condition)                  \
        {                                                 \
            printf("INFO: " message "\n", ##__VA_ARGS__); \
        }                                                 \
    }

// 输出提示信息
#define DEBUGH(condition, message, ...)                        \
    {                                                          \
        if (data_use_debug && condition)                       \
        {                                                      \
            printf(CCFA "HIT : " message CCZL, ##__VA_ARGS__); \
        }                                                      \
    }

// 输出警告信息
#define DEBUGW(condition, message, ...)                        \
    {                                                          \
        if (data_use_debug && condition)                       \
        {                                                      \
            printf(CCFY "WARN: " message CCZL, ##__VA_ARGS__); \
        }                                                      \
    }

// 输出错误信息
#define ERRORP(message, ...)                               \
    {                                                      \
        printf(CCFR "ERR : " message CCZL, ##__VA_ARGS__); \
    }

void setup_console_encoding();

#endif