# wire_ext_blender_fix_ime

README: [中文](../README.md) | [English](doc/README_en.md)

Fix some issues related to the IME in Blender by addon:

<ol>
    <li>
    <p>The IME state (enable/disable) is incorect after input finished.</p>
        <p>Ref <a harf="https://projects.blender.org/blender/blender/issues/93421" target="_blank">T93421</a>, <a href="https://archive.blender.org/developer/D13551" target="_blank">D13551</a></p>
    </li>
</ol>

> **Note**: This addon only works on the Windows version of Blender.

# Contents

- [Installation](#Installation)
- [Getting Started](#Getting-Started)
- [Builds](#Builds)

# Installation

This addon requires Blender ≥ 3.0.

Download the addon from the [Release](https://github.com/Arius-Cr/wire_ext_blender_fix_ime/releases) page. It should be a *.zip file.

Intall the addon according to the [Blender User Manual](https://docs.blender.org/manual/en/3.5/editors/preferences/addons.html#installing-add-ons).

# Getting Started

Enable the addon according to the [Blender User Manual](https://docs.blender.org/manual/en/3.5/editors/preferences/addons.html#enabling-disabling-add-ons).

# Builds

1. git clone this repository.

2. Install [Python](https://www.python.org/) 3.x.

3. Install [Visual Studio Build Tools](https://learn.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2022).

4. Install Windows SDK（included in the Visual Studio Build Tools).

5. Copy the file **make_settings_template.py** to **make_settings.py**，and fill the settings in that file.

6. Modify the **PlatformToolset** and **WindowsTargetPlatformVersion** property in **native/main.vcxproj** according to your Visual Studio Build Tools and Windows SDK version.

7. run the command line: `make build`, and the outputs will locate in the **xdebug** directory.
