struct uiHandleButtonData {
  wmWindowManager *wm;
  wmWindow *window;
  ScrArea *area;
  ARegion *region;

  bool interactive;

  /* overall state */
  uiHandleButtonState state;
  int retval;
  /* booleans (could be made into flags) */
  bool cancel, escapecancel;
  bool applied, applied_interactive;
  /* Button is being applied through an extra icon. */
  bool apply_through_extra_icon;
  bool changed_cursor;
  wmTimer *flashtimer;

  /* edited value */
  /* use 'ui_textedit_string_set' to assign new strings */
  char *str;
  char *origstr;
  double value, origvalue, startvalue;
  float vec[3], origvec[3];
  ColorBand *coba;

  /* True when alt is held and the preference for displaying tooltips should be ignored. */
  bool tooltip_force;
  /**
   * Behave as if #UI_BUT_DISABLED is set (without drawing grayed out).
   * Needed so non-interactive labels can be activated for the purpose of showing tool-tips,
   * without them blocking interaction with nodes, see: #97386.
   */
  bool disable_force;

  /* auto open */
  bool used_mouse;
  wmTimer *autoopentimer;

  /* auto open (hold) */
  wmTimer *hold_action_timer;

  /* text selection/editing */
  /* size of 'str' (including terminator) */
  int str_maxncpy;
  /* Button text selection:
   * extension direction, selextend, inside ui_do_but_TEX */
  int sel_pos_init;
  /* Allow reallocating str/editstr and using 'maxlen' to track alloc size (maxlen + 1) */
  bool is_str_dynamic;

  /* number editing / dragging */
  /* coords are Window/uiBlock relative (depends on the button) */
  int draglastx, draglasty;
  int dragstartx, dragstarty;
  int draglastvalue;
  int dragstartvalue;
  bool dragchange, draglock;
  int dragsel;
  float dragf, dragfstart;
  CBData *dragcbd;

  /** Soft min/max with #UI_DRAG_MAP_SOFT_RANGE_PIXEL_MAX applied. */
  float drag_map_soft_min;
  float drag_map_soft_max;

#ifdef USE_CONT_MOUSE_CORRECT
  /* when ungrabbing buttons which are #ui_but_is_cursor_warp(),
   * we may want to position them.
   * FLT_MAX signifies do-nothing, use #ui_block_to_window_fl()
   * to get this into a usable space. */
  float ungrab_mval[2];
#endif

  /* Menu open, see: #UI_screen_free_active_but_highlight. */
  uiPopupBlockHandle *menu;
  int menuretval;

  /* Search box see: #UI_screen_free_active_but_highlight. */
  ARegion *searchbox;
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

  uiBlockInteraction_Handle *custom_interaction_handle;

  /* Text field undo. */
  uiUndoStack_Text *undo_stack_text;

  /* post activate */
  uiButtonActivateType posttype;
  uiBut *postbut;
};

struct uiKeyNavLock {
  /** Set when we're using keyboard-input. */
  bool is_keynav;
  /** Only used to check if we've moved the cursor. */
  int event_xy[2];
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

  bool has_mbuts; /* any buttons flagged UI_BUT_DRAG_MULTI */
  LinkNode *mbuts;
  uiButStore *bs_mbuts;

  bool is_proportional;

  /* In some cases we directly apply the changes to multiple buttons,
   * so we don't want to do it twice. */
  bool skip;

  /* before activating, we need to check gesture direction accumulate signed cursor movement
   * here so we can tell if this is a vertical motion or not. */
  float drag_dir[2];

  /* values copied direct from event->xy
   * used to detect buttons between the current and initial mouse position */
  int drag_start[2];

  /* store x location once INIT_SETUP is set,
   * moving outside this sets INIT_ENABLE */
  int drag_lock_x;
};

struct uiSelectContextStore {
  uiSelectContextElem *elems;
  int elems_len;
  bool do_free;
  bool is_enabled;
  /* When set, simply copy values (don't apply difference).
   * Rules are:
   * - dragging numbers uses delta.
   * - typing in values will assign to all. */
  bool is_copy;
};