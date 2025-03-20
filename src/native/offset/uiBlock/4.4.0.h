struct uiBlock {
    uiBlock *next, *prev;
  
    ListBase buttons;
    Panel *panel;
    uiBlock *oldblock;
  
    /** Used for `UI_butstore_*` runtime function. */
    ListBase butstore;
  
    blender::Vector<uiButtonGroup> button_groups;
  
    ListBase layouts;
    uiLayout *curlayout;
  
    blender::Vector<std::unique_ptr<bContextStore>> contexts;
  
    /** A block can store "views" on data-sets. Currently tree-views (#AbstractTreeView) only.
     * Others are imaginable, e.g. table-views, grid-views, etc. These are stored here to support
     * state that is persistent over redraws (e.g. collapsed tree-view items). */
    ListBase views;
  
    ListBase dynamic_listeners; /* #uiBlockDynamicListener */
  
    std::string name;
  
    float winmat[4][4];
  
    rctf rect;
    float aspect;
  
    /** Unique hash used to implement popup menu memory. */
    uint puphash;
  
    uiButHandleFunc func;
    void *func_arg1;
    void *func_arg2;
  
    uiButHandleNFunc funcN;
    void *func_argN;
    uiButArgNFree func_argN_free_fn;
    uiButArgNCopy func_argN_copy_fn;
  
    uiBlockHandleFunc handle_func;
    void *handle_func_arg;
  
    /** Custom interaction data. */
    uiBlockInteraction_CallbackData custom_interaction_callbacks;
  
    /** Custom extra event handling. */
    int (*block_event_func)(const bContext *C, uiBlock *, const wmEvent *);
  
    /** Custom extra draw function for custom blocks. */
    std::function<void(const bContext *, rcti *)> drawextra;
  
    int flag;
    short alignnr;
    /** Hints about the buttons of this block. Used to avoid iterating over
     * buttons to find out if some criteria is met by any. Instead, check this
     * criteria when adding the button and set a flag here if it's met. */
    short content_hints; /* #eBlockContentHints */
  
    char direction;
    /** UI_BLOCK_THEME_STYLE_* */
    char theme_style;
    /** Copied to #uiBut.emboss */
    eUIEmbossType emboss;
    bool auto_open;
    char _pad[5];
    double auto_open_last;
  
    const char *lockstr;
  
    bool lock;
    /** To keep blocks while drawing and free them afterwards. */
    bool active;
    /** To avoid tool-tip after click. */
    bool tooltipdisabled;
    /** True when #UI_block_end has been called. */
    bool endblock;
  
    /** for doing delayed */
    eBlockBoundsCalc bounds_type;
    /** Offset to use when calculating bounds (in pixels). */
    int bounds_offset[2];
    /** for doing delayed */
    int bounds, minbounds;
  
    /** Pull-downs, to detect outside, can differ per case how it is created. */
    rctf safety;
    /** #uiSafetyRct list */
    ListBase saferct;
  
    uiPopupBlockHandle *handle;
  
    /** use so presets can find the operator,
     * across menus and from nested popups which fail for operator context. */
    wmOperator *ui_operator;
    bool ui_operator_free;
  
    /** XXX hack for dynamic operator enums */
    void *evil_C;
  
    /** unit system, used a lot for numeric buttons so include here
     * rather than fetching through the scene every time. */
    const UnitSettings *unit;
    /** \note only accessed by color picker templates. */
    ColorPickerData color_pickers;
  
    /** Block for color picker with gamma baked in. */
    bool is_color_gamma_picker;
  
    /**
     * Display device name used to display this block,
     * used by color widgets to transform colors from/to scene linear.
     */
    char display_device[64];
  
    PieMenuData pie_data;
};