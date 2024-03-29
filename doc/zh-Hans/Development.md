# 开发指南

目录：

- [生成](#生成)

- [自动管理输入法状态](#自动管理输入法状态)

- [使用输入法输入文字](#使用输入法输入文字)

- [3.6.2 版非重复型快捷键失效问题](#362-版非重复型快捷键失效问题)

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

3. 在项目目录中执行（自行替换 **{}** 中的内容）：

   ```
   > python make.py build --vsdev "{path to VsDevCmd.bat}"
   ```

   输出的文件在 **xdebug** 目录中。具体请参考 **make.py**。

# 自动管理输入法状态

## 目标

- 用户激活输入框时，程序自动启用输入法，用户可以使用输入法的全部功能进行文字输入。

- 用户退出输入框时，程序自动停用输入法。用户的所有按键都直接发送给程序，**避免按快捷键时触发输入法弹出候选窗口**。

## 现状

Blender(v3.5.0) 中输入框和输入法的工作机制：

- 用户激活输入框时，程序自动启用输入法。并且在鼠标左键单击输入框时总是保持输入法的启用。

  这个行为**符合**期望。

- 用户退出输入框时，如果用户通过输入法输入过文字，则自动停用输入法，否则不调整输入法状态。

  这个行为**不符合**期望。

  在官方的反馈渠道中，已经有提及并提交了修复该 BUG 的代码：<br />
  [#93421](https://projects.blender.org/blender/blender/issues/93421)
  、[D13551](https://archive.blender.org/developer/D13551)

## 解决

解决方法：

介入 Blender 窗口消息处理流程，并且在其流程前：

- 当检测到 鼠标左键、鼠标右键、ESC、Tab、Enter、数字键盘 Enter 按下时，停用输入法。

结合 Blender 自身的机制，最终的效果为：

- 当用户通过上述按键激活输入框，或者激活输入框后在输入框中按鼠标左键。插件先停用输入法，然后 Blender 再启用输入法，结果为**启用**。

- 当用户通过上述按键退出输入框。插件先停用输入法，然后 Blender 再停用输入法或不进行任何处理，结果为**停用**。

停用输入法通过 Win32 API 完成：

```
ImmAssociateContextEx(hWnd, NULL, IACE_IGNORENOCONTEXT);
```

关键在于将第 2 个参数设为 `NULL`，这个用法在微软的文档中并未提及。

参考：[ImmAssociateContextEx](https://docs.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immassociatecontextex)、[ImmAssociateContext](https://docs.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immassociatecontext)

# 使用输入法输入文字

## 目标

- 在 3D 视图-文本物体-编辑模式、文本编辑器、控制台 中，允许用户通过输入法输入文字。

## 现状

Blender(v3.5.0) 中对输入法消息的处理机制：

- 主要在 WM_INPUT 消息中处理按键消息。

  Windows 中使用输入法输入时，相关消息按如下顺序发送：<br/>
  `WM_INPUT`<br/>
  `WM_KEYDOWN`<br/>
  ...<br/>
  `WM_IME_STARTCOMPOSITION`<br/>
  ...

- 当启用了输入法且处于非英文输入模式时，如果按键为预定的由输入法处理的按键，则在 WM_INPUT 中不处理该按键，交由后续接收到 WM_IME_XXX 消息时再处理，否者直接处理。

  “预定的由输入法处理的按键” 在 Blender 中似乎是硬编码的，而按键是否被输入法处理是由输入法决定的，当两者不同时，就会产生问题。

  譬如数字键盘上的 “.” 键，在 Blender 和微软拼音输入法中属于输入法处理范围，但在搜狗拼音输入法中不是，于是对于 “.” 键，在 Blender 看来不属于其处理范围，而在搜狗拼音看来也不属于其处理范围，结果就是没人处理该按键，即用户无法在搜狗拼音中使用数字键盘上的 “.” 键输入字符。

  > **注意**：本插件并未修复在输入框中的该问题，而在 3D 视图-文本物体-编辑模式、文本编辑器、控制台 中，通过输入法输入文字时，本插件通过一些方法避免了该问题的产生。

- Blender 在 3D 视图-文本物体-编辑模式、文本编辑器、控制台 中，不启用输入法，即使强制启用也不响应输入法消息。

- Blender 的 **自动保存** 功能必须在没有任何模态操作正在运行的时候才能执行。

- Blender 的 **工具提示**（悬停在属性或按钮上弹出的小窗口）在显示的时候，如果有模态操作结束，工具提示会自动关闭。

- 在 Blender 中进行涉及 **鼠标捕获** 相关的操作（如在数值控件上拖拽鼠标，在 3D 视图 使用移动操作等）时，如果有模态操作结束，鼠标的位置会被重新计算，导致进行这些操作时鼠标跳跃。

## 解决

插件会在 Blender 处于 3D 视图-文本物体-编辑模式、文本编辑器、控制台 时启用输入法，但因为即使在此时启用了输入法，Blender 也不会处理输入法消息，所以插件必须自行处理输入法消息。

需要处理的输入法消息包括以下的几种：

- `WM_IME_STARTCOMPOSITION`

  当开始合成文本时，IME 会发送该消息。

  此时候选窗口已经弹出（输入单个标点时不弹出，如 Shift + 2 输入 “@” 时）。

- `WM_IME_COMPOSITION`

  当开始合成文本或合成文本变动时，IME 会发送该消息。

- `WM_IME_ENDCOMPOSITION`

  当确认或取消合成文本，IME 会发送该消息。

当插件接收到这些消息后，通过 Blender 提供的 `bpy.ops.font.text_insert`、`bpy.ops.text.insert`、`bpy.ops.console.insert` 将合成文本插入到光标所在位置即可。

以上就是解决方案的大概模样，下面将展示实际的处理流程。

关键术语：

- 消息处理器：<br />
  `fix_ime_input.c` - fix_ime_input_XXX 系列函数

- 输入管理器：<br />
  `main.py` - `class Manager`

- 状态更新器：<br />
  `main.py` - `class WIRE_FIX_IME_OT_state_updater`

- 状态更新-步进-计时器：<br />
  `main.py` - `Manager.updater_step_timer`

- 输入处理器：<br />
  `main.py` - `class WIRE_FIX_IME_OT_input_handler`

- 输入处理-启动-计时器：<br />
  `main.py` - `Manager.handler_start_timer`

- 输入处理-更新-计时器：<br />
  `main.py` - `Manager.handler_update_timer`

具体流程：

1.  在插件中启用 “使用输入法输入文字” 功能后，插件会在 Blender 的按键映射表中添加以下映射项：

    - `Screen Editing` - `MOUSEMOVE` - `WIRE_FIX_IME_OT_state_updater`

      **功能 1**：用于启动 **输入管理器**（`Manager.start()`），并且将输入管理器和当前窗口（`bpy.types.Context.window`）关联。

      每个窗口对应一个输入管理器，因为用到计时器（`bpy.types.WindowManager.event_timer_add()`）时，计时器只能针对特定的一个窗口设置。

      **输入管理器** 主要用于记录各种数据和提供各种相关方法。

      **功能 2**：捕获 `MOUSEMOVE` 消息，用于触发 **状态更新**。

    - `Screen Editing` - `TIMER` - `WIRE_FIX_IME_OT_state_updater`

      **功能 1**：捕获 **状态更新-步进-计时器** 消息，用于触发 **状态更新**。

      **功能 2**：捕获 **输入处理-启动-计时器** 消息，用于触发 **输入处理**。

2.  状态更新器的工作流程：

    1. 状态更新器的主要功能就是根据程序当前的状态，自动进入或退出 **输入法消息处理流程**，该行为称为 **状态更新**。

       **状态更新**：当鼠标位于 3D 视图（活动物体为文本物体，且物体模式为编辑模式）、文本编辑器（已关联文本对象）、控制台 时进入输入法消息处理流程，反之退出输入法消息处理流程。

       **输入法消息处理流程**：

       - 进入该流程后，插件会启用输入法，并且处理输入法消息；

       - 退出该流程后，插件会停用输入法，并且不处理输入法消息。

       > 状态更新器是整个功能中最麻烦的部分，麻烦的原因在于需要兼容 **自动保存**、**工具提示**、**鼠标捕获**。当前的流程经过多次迭代已经兼容上述的功能。

    2. 状态更新器被设计为每隔 50-100ms 更新一次，并且在用户没有操作时停止更新，避免频繁和无意义的更新。

       鼠标和键盘消息均会触发更新，但距离上次更新大于 50ms 时才会执行更新。

       此外，如果当前窗口处于非激活态或正在捕获鼠标，或者正在通过输入法输入文字，都不会执行更新。

       其工作流程基本可以概括为：

       - 捕获输入消息

       - 判断当前是否满足更新的条件，满足则更新，不满足则不更新

       由于流程中细节比较多，请自行阅读代码（以**状态更新器**为中心进行查找即可看到整个更新的链路）

3.  输入处理器的基本工作流程：

    1. 输入消息的处理必然在进入 **输入法消息处理流程** 后才会运行。

    2. **消息处理器** 中对消息的处理流程：

       1. 当 `WM_INPUT` 消息到达时：

          - 如果当前没有进行文字合成：

            - 如果该消息的 `ExtraInformation` 带有特殊标记，则放行按键（即让 Blender 处理该消息）。

            - 如果该按键为非字符键，则放行按键。

            - 否则，暂时拦截按键。

          - 如果当前正在进行文字合成，拦截按键。

       2. 当 `WM_KEYDOWN`、`WM_KEYUP` 消息到达时：

          - 如果输入法表明该按键应该由输入法处理（`wParam == VK_PROCESSKEY`），则真正拦截按键。

            之后该按键的效果将由 `WM_IME_STARTCOMPOSITION` 等反映，因此拦截也没关系。

          - 否则，以模拟按键的方式将该按键重放一次，重放前设置 `ExtraInformation` 为特殊标记。

            之后 `WM_INPUT` 会再次收到该按键，而这次会放行该按键，重新交由 Blender 处理。

       3. 当 `WM_IME_STARTCOMPOSITION` 等消息到达时：

          - 通过回调函数通知脚本端进行处理。

    3. 当 **消息处理器** 接收到输入法消息后，会通过回调函数通知插件。插件会将输入法消息转换后添加到对应的 **输入管理器** 的消息队列中。然后设置 **输入处理-启动-计时器**。

    4. **输入处理-启动-计时器** 到达 **状态更新器** 后（注：没有笔误！），状态更新器会调用 **输入处理器**。

    5. **输入处理器** 每次只处理输入法消息队列中的一组消息。一组消息指 START 到 FINISH 或 CANCEL 之间的消息。如果存在下一组输入法消息，则 **输入处理器** 会设置 **输入处理-启动-计时器**，让下一个 **输入处理器** 来处理。分组处理是为了能够在用户撤销时能够逐组文字进行撤销。

    6. 每组中的每个输入法消息都按照以下流程进行处理：

       - 如果之前处理过组内的输入法消息，则删除之前消息插入过的文本。

       - 将合成文本插入到光标的位置，并且正确设置合成文本中光标的位置。

# 3.6.2 版非重复型快捷键失效问题

该问题源于以下修改（commit hash: 8191b152ecf）

    Fix #109525: Improved Win32 Repeat Key Filtering

    Allows Win32 key repeat filtering to support multiple simultaneously
    repeating keys, as can happen with modifiers. Removes
    m_keycode_last_repeat_key and instead checks current down status.

    Pull Request: https://projects.blender.org/blender/blender/pulls/109991

Blender 在 3.6.2 版中修改了按键重复的判断机制，从自己建立机制来判断改为使用系统的机制来判断。

这个修改导致了启用了本插件后，某些没有启用**重复**的按键映射项不会被触发（譬如复制：Ctrl + C），但启用了重复的按键映射项依然能够被触发（譬如粘贴：Ctlr + V）。

## 解决

通过在回放按键时多加一条按键消息来取消按键的按下状态，即可使得回放的按键处于非重复状态。

而重复产生的按键消息，无需多加一条按键消息，保持默认即可。
