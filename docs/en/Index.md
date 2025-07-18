# IME Helper

Make Blender better support IME (Input Method Editor).

# Features

1. IME can be used in more places

    Previously, you could only use IME in Text Field.

    Now, you can use IME to input text in Text Field、Text object Edit mode、Text Editor、Console、Text strip Edit mode.

2. Automatically enable/disable IME

    Previously, after you leaving the Text Field without input any text, IME will keep enable. If you press some shortcut key (like "G" to move object) at this time, IME will intercept your keystrokes. It make you impossible to use some shortcut keys, untill you switch IME to English input mode. Unfortunately, if you accidentally press the shortcut key ("Shift" for most Chinese IMEs) to switch input modes, the input mode will revert back to non English mode. Then IME will intercept your next keystroke, and you need to switch back to English mode. Repeat like this all the time.

    Now, this addon can automatically enable/disable IME when entering/leaving the Text Field、Text object Edit mode、Text Editor、Console、Text strip Edit mode. ("Text strip Edit mode" supported only in Blender 4.4 and above.)

# CAUTIOUS

You can **ONLY** use this addon in officially released Blender and cannot use it in daily builds and third-party Blenders.

This addon will directly access memory (read only, not write) through pointers based on the memeber offset of struct. The offset may vary in different Blender versions. I can only ensure that the offset is correct in the officially released Blenders. If the offset used by the addon is different from the Blender you are using. It may **cause your Blender to crash**.

You can view all supported versions in the addon Preference. Although it will list daily builds version, but it is still not recommended that you use this addon in the daily build version, unless you voluntarily take on the risk.

The buttons in addon Preference named "Update memory offset data"/"Auto update"(memory offset data), can update the offset data from remote, make the addon support new Blender version. This is useful for users who use the daily build version, but it is not useful for other users and can be ignored.
