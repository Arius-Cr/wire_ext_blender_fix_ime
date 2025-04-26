struct uiHandleButtonData {
    wmWindowManager *wm = nullptr;
    wmWindow *window = nullptr;
    ScrArea *area = nullptr;
    ARegion *region = nullptr;
  
    bool interactive = false;
  
    /* overall state */
    uiHandleButtonState state = {};
    int retval = 0;
    /* booleans (could be made into flags) */
    bool cancel = false;
    bool escapecancel = false;
    bool applied = false;
    bool applied_interactive = false;
    /* Button is being applied through an extra icon. */
    bool apply_through_extra_icon = false;
    bool changed_cursor = false;
    wmTimer *flashtimer = nullptr;
  
    uiTextEdit text_edit;
  
    double value = 0.0f;
    double origvalue = 0.0f;
    double startvalue = 0.0f;
    float vec[3], origvec[3];
    ColorBand *coba = nullptr;
  
    /* True when alt is held and the preference for displaying tooltips should be ignored. */
    bool tooltip_force = false;
    /**
     * Behave as if #UI_BUT_DISABLED is set (without drawing grayed out).
     * Needed so non-interactive labels can be activated for the purpose of showing tool-tips,
     * without them blocking interaction with nodes, see: #97386.
     */
    bool disable_force = false;
  
    /**
     * Semi-modal buttons: Instead of capturing all events, pass on events that aren't relevant to
     * own handling. This way a text button (e.g. a search/filter field) can stay active while the
     * remaining UI stays interactive. Only few button types support this well currently.
     */
    bool is_semi_modal = false;
  
    /* auto open */
    bool used_mouse = false;
    wmTimer *autoopentimer = nullptr;
  
    /* auto open (hold) */
    wmTimer *hold_action_timer = nullptr;
  
    /* number editing / dragging */
    /* coords are Window/uiBlock relative (depends on the button) */
    int draglastx = 0;
    int draglasty = 0;
    int dragstartx = 0;
    int dragstarty = 0;
    bool dragchange = false;
    bool draglock = false;
    int dragsel = 0;
    float dragf = 0.0f;
    float dragfstart = 0.0f;
    CBData *dragcbd = nullptr;
  
    /** Soft min/max with #UI_DRAG_MAP_SOFT_RANGE_PIXEL_MAX applied. */
    float drag_map_soft_min = 0.0f;
    float drag_map_soft_max = 0.0f;
  
  #ifdef USE_CONT_MOUSE_CORRECT
    /* when ungrabbing buttons which are #ui_but_is_cursor_warp(),
     * we may want to position them.
     * FLT_MAX signifies do-nothing, use #ui_block_to_window_fl()
     * to get this into a usable space. */
    float ungrab_mval[2];
  #endif
  
    /* Menu open, see: #UI_screen_free_active_but_highlight. */
    uiPopupBlockHandle *menu = nullptr;
  
    /* Search box see: #UI_screen_free_active_but_highlight. */
    ARegion *searchbox = nullptr;
  #ifdef USE_KEYNAV_LIMIT
    uiKeyNavLock searchbox_keynav_state;
  #endif
  
  #ifdef USE_DRAG_MULTINUM
    /* Multi-buttons will be updated in unison with the active button. */
    uiHandleButtonMulti multi_data;
  #endif
  
  #ifdef USE_ALLSELECT
    uiSelectContextStore select_others;
  #endif
  
    uiBlockInteraction_Handle *custom_interaction_handle = nullptr;
  
    /* post activate */
    uiButtonActivateType posttype = {};
    uiBut *postbut = nullptr;
};

struct uiKeyNavLock {
    /** Set when we're using keyboard-input. */
    bool is_keynav = false;
    /** Only used to check if we've moved the cursor. */
    blender::int2 event_xy = blender::int2(0);
};

struct uiHandleButtonMulti {
    enum {
      /** gesture direction unknown, wait until mouse has moved enough... */
      INIT_UNSET = 0,
      /** vertical gesture detected, flag buttons interactively (UI_BUT_DRAG_MULTI) */
      INIT_SETUP,
      /** flag buttons finished, apply horizontal motion to active and flagged */
      INIT_ENABLE,
      /** vertical gesture _not_ detected, take no further action */
      INIT_DISABLE,
    } init;
  
    bool has_mbuts = false; /* any buttons flagged UI_BUT_DRAG_MULTI */
    LinkNode *mbuts = nullptr;
    uiButStore *bs_mbuts = nullptr;
  
    bool is_proportional = false;
  
    /* In some cases we directly apply the changes to multiple buttons,
     * so we don't want to do it twice. */
    bool skip = false;
  
    /* before activating, we need to check gesture direction accumulate signed cursor movement
     * here so we can tell if this is a vertical motion or not. */
    float drag_dir[2] = {0.0f, 0.0f};
  
    /* values copied direct from event->xy
     * used to detect buttons between the current and initial mouse position */
    int drag_start[2] = {0, 0};
  
    /* store x location once INIT_SETUP is set,
     * moving outside this sets INIT_ENABLE */
    int drag_lock_x = 0;
};

struct uiSelectContextStore {
    blender::Vector<uiSelectContextElem> elems;
    bool do_free = false;
    bool is_enabled = false;
    /* When set, simply copy values (don't apply difference).
     * Rules are:
     * - dragging numbers uses delta.
     * - typing in values will assign to all. */
    bool is_copy = false;
};