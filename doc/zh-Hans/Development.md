# 开发指南

目录：

- [生成](#生成)

- [开发背景](#开发背景)

# 生成

1. 安装 [Python](https://www.python.org/) 3.x

2. 安装 [Visual Studio 2022 Build Tools](https://learn.microsoft.com/zh-cn/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2022)

    - 安装 **使用 C++ 的桌面开发** 工作负荷

    - 安装 **Windows SDK**（上述的工作负荷已包含）

    现用版本：

    - Visual Studio 2022 Build Tools 17.6.1

    - MSVC 14.36.32532

    - Windows SDK 10.0.20348.0

    > 如果使用不同的版本，请适当修改 **native/main.vcxproj** 中的 `PlatformToolset` 和 `WindowsTargetPlatformVersion` 属性。

3. 在项目目录中执行（自行替换 **{...}** 中的内容）：

    ```
    > python make.py build -v "{path to VsDevCmd.bat}"
    ```

    输出的文件在 **xdebug** 目录中。具体请参考 **make.py**。

# 开发背景

用户需要的输入法状态应该是：

- 当**需要**输入文字的时候，输入法处于**启用**状态。<br />
    此时按键会先经过输入法处理后再传递到窗口，多数时候按下字母键会触发文字合成，输入法会弹出文字候选框。

- 当**不需要**输入文字的时候，输入法处于**停用**状态。<br />此时按键会直接传递到窗口。

> **注意**：<br />这里的启用和停用输入法指的是“仅在某个窗口中启用或停用输入法”，并不是全局性（对所有窗口）启用或停用输入法。另外切换为英文输入模式并非停用输入法。

而目前 Blender(v3.5.0) 对输入法状态管理的机制为：

- 当激活文字输入框（Text Field）时（譬如修改物体的名称），启用输入法，并且在整个输入过程中保持输入法处于启用状态。

- 当离开文字输入框时：

  - 如果之前进行过任何的文字合成（无论最终确认还是取消），则停用输入法。

  - 如果之前没有进行过任何的文字合成，譬如激活文字输入框后，直接退出，则不处理输入法状态（结果就是保持启用状态）。

Blender 中这个不合理的输入法状态管理实际上是一个 BUG，原则上对源码中的以下位置的逻辑进行修正就可以修复（我还没有完全理清源码的来龙去脉，所以只是“原则上”，并不确定，譬如对 Linux 或 MacOS 是否有影响之类）：

- blender\source\blender\editors\interface\interface_handlers.cc
  - ui_textedit_end()<br />
  ```
  if (win->ime_data) {
      ui_textedit_ime_end(win, but);
  }
  ```

但是从以下页面的信息来看，这个问题好像已经修复了：

https://projects.blender.org/blender/blender/issues/93421

https://archive.blender.org/developer/D13551

只是该补丁（2021-12-12）到现在（2023-05-29）似乎依然处于“需要审查”（Needs Review）的阶段，也就是还没有合并到 Blender 的源码中，所以现在该问题依然存在。

基于上述的情况，我编写了一个插件来临时解决一下问题，直到官方正式修复该问题。

该插件的工作原理如下：

通过消息钩子监听本进程（Blender）所有窗口的鼠标、键盘和焦点消息，并且在监听到譬如鼠标左键单击、按下 Enter 键等和离开文本输入框相关的消息时，通过调用：

```
ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
```

在当前窗口停用输入法。但这些消息并不能真的表示用户正在离开文本输入框，因此单从代码逻辑上来看，该代码的作用几乎就是一直在停用输入法。

但是 Blender 本身**在激活文本输入框时，总是保持输入法处于启用状态**，也就是说：

- 在激活文本输入框时，消息钩子中的代码会停用输入法，但是接下来交给 Blender 后，Blender 会重新启用输入法，结果就是输入法处于启用状态。

- 在离开文本输入框时，消息钩子中的代码会停用输入法，之后由于 Blender 不会对输入法状态进行任何处理，因此结果就是输入法处于停用状态。

最终，输入法的状态符合我们的预期，即该启用时会自动启用，该停用时会自动停用。

---

最后关于 **ImmAssociateContextEx** 函数，请参考：

- [ImmAssociateContextEx](https://docs.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immassociatecontextex)

- [ImmAssociateContext](https://docs.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immassociatecontext)

其中通过将第 2 个参数设为 NULL 可以为指定窗口停用输入法。这个功能在微软的文档中似乎是没有讲的，但是确实可以使用。并且已经存在很多年了。

参考：

- 2008 年的一篇文章：<br />
  https://blog.csdn.net/kesalin/article/details/2603975

- 2014 年的一篇文章：<br />
  https://blog.csdn.net/xie1xiao1jun/article/details/17913967
