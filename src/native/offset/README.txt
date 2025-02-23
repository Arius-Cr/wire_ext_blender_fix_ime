请先参考 blender.c 中的说明。

目录结构：
    <类型>
        每个目标类型建立一个文件夹，里面记录该类型在各个版本中的声明。
        _summary.txt
            总结该类型在各个版本中的变化。
        ...
        x.x.x.h
            该类型在各个版本中的声明。

收集过程：
    1. 使用 Git 克隆 Blender 源码。
    2. 使用 Git 的工作树功能，将各个版本（标签）检出到各个工作树。
    3. 用 VSCode 打开工作树，通过 Ctrl + P 检索对应文件，然后 Ctrl + F 检索对应类型。
    4. 复制类型的声明到类型目录中对应的 "x.x.x.h" 文件。

归纳过程：
    1. 在 VSCode 的资源管理器中，选中需要比较的A文件，右键“选择以进行比较”
    2. 选中需要比较的B文件，右键“与已选项目进行比较”
    3. 根据对比结果了解该类型在各个版本中的变化。

计算过程：
    1. 对于 DNA 类型，直接按顺序计算各个成员的大小得到成员的偏移量即可。
       因为 DNA 类型是手动内存对齐的（因此会有 `char _pad[3]` 这样的成员），
       所及直接计算即可。
    2. 对于非 DNA 类型，其由编译器进行内存对齐，要么自行编译一次打印出来，
       要么手动计算后估算内存对齐的结果，然后再测试验证...

       但幸运的是，当前需要的数据要么可以简单计算出来，要么可以通过插件的调试信息获取。
       
       对于 uiHandleButtonData 和 uiPopupBlockHandle 结构的长度，
       可以在 src/native/blender.c 的 wmWindow_is_but_active()、
       wmWindow_is_pop_active() 函数输出的调试信息中获取。

       对于 uiHandleButtonData，先激活输入框，然后看调试信息即可。
       对于 uiPopupBlockHandle，先右键弹出菜单，然后看调试信息即可。

    最后，实际上如果你能够编译 Blender，只要编译最后的一个正式版，然后修改源码通过 printf 打印偏移量，
    然后根据数据结构的版本差异，反推之前的版本就可以免于繁琐的计算。

常见数据类型的长度（MSVC 64bit）：
    pointer - 8 字节
    int     - 4 字节
    float   - 4 字节
    bool    - 1 字节
    enum    - 4 字节 (默认)

2025-02-23 补充：部分数据必须通过编译和打印才能得到。

注意：必须通过 Release 配置来生成，因为 Debug 配置和 Release 配置得到的偏移量可能不同。

WM_event_add_modal_handler:
  printf("offset_ARegion__runtime: %zu\n", offsetof(ARegion, runtime));
  printf("offset_ARegionRuntime__uiblocks: %zu\n", offsetof(ARegionRuntimeHandle, uiblocks));
在3D视图按下“G”即可打印信息。

ui_do_but_textedit:
  printf("offset_wmEventHandler__type: %zu\n", offsetof(wmEventHandler, type));
  printf("offset_wmEventHandler__handle_fn: %zu\n", offsetof(wmEventHandler_UI, handle_fn));
  printf("offset_wmEventHandler__remove_fn: %zu\n", offsetof(wmEventHandler_UI, remove_fn));
  printf("offset_wmEventHandler__user_data: %zu\n", offsetof(wmEventHandler_UI, user_data));
  printf("offset_wmEventHandler__area: %zu\n", offsetof(wmEventHandler_UI::context, area));
  printf("offset_wmEventHandler__region: %zu\n", offsetof(wmEventHandler_UI::context, region));
  printf("offset_wmEventHandler__menu: %zu\n", offsetof(wmEventHandler_UI::context, region_popup));

  printf("WM_HANDLER_TYPE_UI: %d\n", WM_HANDLER_TYPE_UI);

  printf("-----\n");

  printf("sizeof_uiHandleButtonData: %zu\n", sizeof(uiHandleButtonData));

  printf("-----\n");

  printf("sizeof_uiPopupBlockHandle: %zu\n", sizeof(uiPopupBlockHandle));
  printf("offset_uiPopupBlockHandle__region: %zu\n", offsetof(uiPopupBlockHandle, region));

  printf("-----\n");

  printf("sizeof_uiPopupBlockHandle: %zu\n", sizeof(uiPopupBlockHandle));

  printf("-----\n");

  printf("offset_uiBlock__buttons: %zu\n", offsetof(uiBlock, buttons));
  block->buttons.print_stats("test");
  printf("sizeof_uiBlock__buttons__unique_ptr: %zu\n", sizeof(std::unique_ptr<uiBut>));

  printf("-----\n");

  printf("sizeof_uiBut: %zu\n", sizeof(uiBut));
  printf("offset_uiBut__flag: %zu\n", offsetof(uiBut, flag));
  printf("offset_uiBut__type: %zu\n", offsetof(uiBut, type));

  printf("-----\n");

  printf("UI_SELECT: %d\n", UI_SELECT);
  printf("UI_BTYPE_TEXT: %d\n", UI_BTYPE_TEXT);
  printf("UI_BTYPE_NUM: %d\n", UI_BTYPE_NUM);
  printf("UI_BTYPE_SEARCH_MENU: %d\n", UI_BTYPE_SEARCH_MENU);

  printf("-----\n");

  printf("block: %zu\n", (size_t)block);
  printf("block->buttons: %zu\n", (size_t)&block->buttons);
  printf("block->buttons.begin(): %zu\n", (size_t)block->buttons.begin());
  printf("block->buttons.begin()->get(): %zu\n", (size_t)block->buttons.begin()->get());
  printf("block->buttons.end(): %zu\n", (size_t)block->buttons.end());
  printf("block->buttons.end()->get(): %zu\n", (size_t)block->buttons.end()->get());
  printf("block->buttons.size(): %zu\n", block->buttons.size());
  printf("block->buttons.begin()->get()->flag: %x\n", block->buttons.begin()->get()->flag);
  printf("block->buttons.begin()->get()->type: %x\n", block->buttons.begin()->get()->type);
  printf("but: %zu\n", (size_t)but);
  printf("but.flag: %x\n", but->flag);
  printf("but.type: %x\n", but->type);

  printf("=====\n");

  printf("=====\n");
print_stats: # source\blender\blenlib\BLI_vector.hh
  printf("offset_uiBlock__buttons__begin_: %zu\n", (char *)(&this->begin_) - (char *)this);
  printf("offset_uiBlock__buttons__end_: %zu\n", (char *)(&this->end_) - (char *)this);
激活文本框即可打印信息。

-----
DNA 类型

DNA_space_types.h
SpaceText
SpaceText_Runtime

DNA_windowmanager_types.h
wmWindow

DNA_workspace_types.h
WorkSpaceInstanceHook
WorkSpaceLayout

DNA_screen_types.h
bScreen
ARegion
ARegionRuntime # Blender 4.4.0 新增

-----
非 DNA 类型

wm_event_system.h
eWM_EventHandlerType
wmEventHandler
wmEventHandler_UI

interface_handlers.c
uiHandleButtonData 【开发版不同步】

interface_intern.h
uiPopupBlockHandle
uiBlock 【开发版不同步】
uiBut 【开发版不同步】
UI_SELECT

UI_interface.h
eButType
