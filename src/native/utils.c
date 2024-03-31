#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <locale.h>
// Windows
#include <Windows.h>
// Self
#include "utils.h"

void setup_console_encoding()
{
    // 要在 Blender 的控制台输出中文似乎非常困难？其行为和常规的控制台似乎不同
    // 按照以下设置，可以实现:
    //      printf 的格式化字符串必须为 UTF-8。%s -> UTF-8 字符串，%ls -> UTF-16 字符串。
    //     wprintf 的格式化字符串必须为 UTF-8。%s -> UTF-8 字符串，%ls -> UTF-8  字符串。
    // 总结就是，直接通过printf即可输出中文，支持UTF-8（源码中的字符串）和UTF-16（系统传递过来的字符串）。
    // 其行为和常规的不同，原因未知。
    UINT cp = GetConsoleCP();
    if (cp != CP_UTF8)
    {
        SetConsoleCP(CP_UTF8);
    }
    UINT cp_out = GetConsoleOutputCP();
    if (cp_out != CP_UTF8)
    {
        SetConsoleOutputCP(CP_UTF8);
    }
    setlocale(LC_ALL, ".UTF-8");

    // 示例：
    // printf("你好，%ls！", L"中文");

    // char *locale = setlocale(LC_ALL, NULL);
    // printf("locale: %s\n", locale);

    // char a[] = "好1";     // UTF-8 编码，E5A5BD
    // // 编码应该是 E5 A5 BD 31 00 （31 是 "1"）

    // wchar_t b[] = L"好2"; // 应该是 UTF-16 编码 7D59，但直接输出编码却是随机的？
    // // 编码应该是 7D 59 32 00 00 00 （32 00 是 "2"）

    // char *p_byte = 0;
    // printf("code(a):\n");
    // for (int i = 0; i < sizeof(a); i += 1)
    // {
    //     p_byte = &a;
    //     p_byte += i;
    //     printf("%02hhX ", *p_byte);
    // }
    // printf("\n");

    // p_byte = 0;
    // printf("code(b):\n");
    // for (int i = 0; i < sizeof(b); i += 1)
    // {
    //     p_byte = &b;
    //     p_byte += i;
    //     printf("%02hhX ", *p_byte);
    // }
    // printf("\n");

    // printf("printf s, 好1 a: %s", a); // 可以输出 UTF-8 中文
    // printf("\n");
    // printf("printf ls, 好1 a: %ls", a); // 乱码
    // printf("\n");

    // printf("printf s, 好2 b: %s", b); // 乱码
    // printf("\n");
    // printf("printf ls, 好2 b: %ls", b); // 可以输出 UTF-16 中文
    // printf("\n");

    // wprintf(L"wprintf s, 好1 a: %s", a); // 可以输出 UTF-8 中文
    // printf("\n");
    // wprintf(L"wprintf ls, 好1 a: %ls", a); // 可以输出 UTF-8 中文
    // printf("\n");

    // wprintf(L"wprintf s, 好2 b: %s", b); // 乱码
    // printf("\n");
    // wprintf(L"wprintf ls, 好2 b: %ls", b); // 乱码
    // printf("\n");

    // printf(L"printf 宽字符"); // 乱码
    // printf("\n");
    // wprintf("wprintf 窄字符"); // 可以输出 UTF-8 中文
    // printf("\n");
}