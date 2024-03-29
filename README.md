# wire_fix_ime

**项目链接**：[Github](https://github.com/Arius-Cr/wire_ext_blender_fix_ime)

**文档链接**：[中文](doc/zh-Hans/Index.md)

&nbsp;

**注意：该插件仅适用于 Windows 版的 Blender。**

&nbsp;

通过插件修复 Blender 中，和 IME 相关的一些问题，目前实现的功能包括：

1. **自动管理输入法状态**

    该功能所针对的问题往往会被描述为“快捷键失灵”，或者“快捷键和输入法冲突”等。

    该问题的经典场景就是通过输入法重命名物体的名称，并且按下 Enter 键后，鼠标移动到 3D 视图，按下“G”键移动物体，并没有触发移动操作，而是弹出了输入法的候选窗口。

    本功能可以在用户激活输入控件时自动启用输入法，在用户离开输入控件时自动停用输入法。

2. **使用输入法输入文字**

    允许用户在以下状态时，直接通过输入法输入文字：

    - 3D视图文本物体的编辑模式

    - 文本编辑器

    - 控制台

&nbsp;

详细内容请参考本页顶部列出的 **文档链接**。
