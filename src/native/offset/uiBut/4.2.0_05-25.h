struct uiBut {
  uiBut *next = nullptr, *prev = nullptr;

  /** Pointer back to the layout item holding this button. */
  uiLayout *layout = nullptr;
  int flag = 0;
  int flag2 = 0;
  int drawflag = 0;
  eButType type = eButType(0);
  eButPointerType pointype = UI_BUT_POIN_NONE;
  short bit = 0, bitnr = 0, retval = 0, strwidth = 0, alignnr = 0;
  short ofs = 0, pos = 0, selsta = 0, selend = 0;

  std::string str;

  std::string drawstr;

  char *placeholder = nullptr;

  rctf rect = {}; /* block relative coords */

  char *poin = nullptr;
  float hardmin = 0, hardmax = 0, softmin = 0, softmax = 0;

  uchar col[4] = {0};

  /** See \ref UI_but_func_identity_compare_set(). */
  uiButIdentityCompareFunc identity_cmp_func = nullptr;

  uiButHandleFunc func = nullptr;
  void *func_arg1 = nullptr;
  void *func_arg2 = nullptr;
  /**
   * C++ version of #func above. Allows storing arbitrary data in a type safe way, no void
   * pointer arguments.
   */
  std::function<void(bContext &)> apply_func;

  uiButHandleNFunc funcN = nullptr;
  void *func_argN = nullptr;

  const bContextStore *context = nullptr;

  uiButCompleteFunc autocomplete_func = nullptr;
  void *autofunc_arg = nullptr;

  uiButHandleRenameFunc rename_func = nullptr;
  void *rename_arg1 = nullptr;
  void *rename_orig = nullptr;

  /** Run an action when holding the button down. */
  uiButHandleHoldFunc hold_func = nullptr;
  void *hold_argN = nullptr;

  const char *tip = nullptr;
  uiButToolTipFunc tip_func = nullptr;
  void *tip_arg = nullptr;
  uiFreeArgFunc tip_arg_free = nullptr;
  /** Function to override the label to be displayed in the tooltip. */
  std::function<std::string(const uiBut *)> tip_label_func;

  uiButToolTipCustomFunc tip_custom_func = nullptr;

  /** info on why button is disabled, displayed in tooltip */
  const char *disabled_info = nullptr;

  BIFIconID icon = ICON_NONE;
  /** Copied from the #uiBlock.emboss */
  eUIEmbossType emboss = UI_EMBOSS;
  /** direction in a pie menu, used for collision detection. */
  RadialDirection pie_dir = UI_RADIAL_NONE;
  /** could be made into a single flag */
  bool changed = false;
  /** so buttons can support unit systems which are not RNA */
  uchar unit_type = 0;
  short iconadd = 0;

  /** Affects the order if this uiBut is used in menu-search. */
  float search_weight = 0.0f;

  /** #UI_BTYPE_BLOCK data */
  uiBlockCreateFunc block_create_func = nullptr;

  /** #UI_BTYPE_PULLDOWN / #UI_BTYPE_MENU data */
  uiMenuCreateFunc menu_create_func = nullptr;

  uiMenuStepFunc menu_step_func = nullptr;

  /* RNA data */
  PointerRNA rnapoin = {};
  PropertyRNA *rnaprop = nullptr;
  int rnaindex = 0;

  /* Operator data */
  wmOperatorType *optype = nullptr;
  PointerRNA *opptr = nullptr;
  wmOperatorCallContext opcontext = WM_OP_INVOKE_DEFAULT;

  /** When non-zero, this is the key used to activate a menu items (`a-z` always lower case). */
  uchar menu_key = 0;

  ListBase extra_op_icons = {nullptr, nullptr}; /** #uiButExtraOpIcon */

  eWM_DragDataType dragtype = WM_DRAG_ID;
  short dragflag = 0;
  void *dragpoin = nullptr;
  const ImBuf *imb = nullptr;
  float imb_scale = 0;

  /**
   * Active button data, set when the user is hovering or interacting with a button (#UI_HOVER and
   * #UI_SELECT state mostly).
   */
  uiHandleButtonData *active = nullptr;

  /** Custom button data (borrowed, not owned). */
  void *custom_data = nullptr;

  char *editstr = nullptr;
  double *editval = nullptr;
  float *editvec = nullptr;

  std::function<bool(const uiBut &)> pushed_state_func;

  /** Little indicator (e.g., counter) displayed on top of some icons. */
  IconTextOverlay icon_overlay_text = {};

  /* pointer back */
  uiBlock *block = nullptr;

  uiBut() = default;
  /** Performs a mostly shallow copy for now. Only contained C++ types are deep copied. */
  uiBut(const uiBut &other) = default;
  /** Mostly shallow copy, just like copy constructor above. */
  uiBut &operator=(const uiBut &other) = default;
};

enum {
  /** Use when the button is pressed. */
  UI_SELECT = (1 << 0),
  /** Temporarily hidden (scrolled out of the view). */
  UI_SCROLLED = (1 << 1),
  /**
   * The button is hovered by the mouse and should be drawn with a hover highlight. Also set
   * sometimes to highlight buttons without actually hovering it (e.g. for arrow navigation in
   * menus). UI handling code manages this mostly and usually does this together with making the
   * button active/focused (see #uiBut::active). This means events will be forwarded to it and
   * further handlers/shortcuts can be used while hovering it.
   */
  UI_HOVER = (1 << 2),
  UI_HAS_ICON = (1 << 3),
  UI_HIDDEN = (1 << 4),
  /** Display selected, doesn't impact interaction. */
  UI_SELECT_DRAW = (1 << 5),
  /** Property search filter is active and the button does not match. */
  UI_SEARCH_FILTER_NO_MATCH = (1 << 6),

  /** Temporarily override the active button for lookups in context, regions, etc. (everything
   * using #ui_context_button_active()). For example, so that operators normally acting on the
   * active button can be polled on non-active buttons to (e.g. for disabling). */
  UI_BUT_ACTIVE_OVERRIDE = (1 << 7),

  /* WARNING: rest of #uiBut.flag in UI_interface.hh */
};

enum eButType {
  UI_BTYPE_BUT = 1 << 9,
  UI_BTYPE_ROW = 2 << 9,
  UI_BTYPE_TEXT = 3 << 9,
  /** Drop-down list. */
  UI_BTYPE_MENU = 4 << 9,
  UI_BTYPE_BUT_MENU = 5 << 9,
  /** number button */
  UI_BTYPE_NUM = 6 << 9,
  /** number slider */
  UI_BTYPE_NUM_SLIDER = 7 << 9,
  UI_BTYPE_TOGGLE = 8 << 9,
  UI_BTYPE_TOGGLE_N = 9 << 9,
  UI_BTYPE_ICON_TOGGLE = 10 << 9,
  UI_BTYPE_ICON_TOGGLE_N = 11 << 9,
  /** same as regular toggle, but no on/off state displayed */
  UI_BTYPE_BUT_TOGGLE = 12 << 9,
  /** similar to toggle, display a 'tick' */
  UI_BTYPE_CHECKBOX = 13 << 9,
  UI_BTYPE_CHECKBOX_N = 14 << 9,
  UI_BTYPE_COLOR = 15 << 9,
  UI_BTYPE_TAB = 16 << 9,
  UI_BTYPE_POPOVER = 17 << 9,
  UI_BTYPE_SCROLL = 18 << 9,
  UI_BTYPE_BLOCK = 19 << 9,
  UI_BTYPE_LABEL = 20 << 9,
  UI_BTYPE_KEY_EVENT = 24 << 9,
  UI_BTYPE_HSVCUBE = 26 << 9,
  /** Menu (often used in headers), `*_MENU` with different draw-type. */
  UI_BTYPE_PULLDOWN = 27 << 9,
  UI_BTYPE_ROUNDBOX = 28 << 9,
  UI_BTYPE_COLORBAND = 30 << 9,
  /** sphere widget (used to input a unit-vector, aka normal) */
  UI_BTYPE_UNITVEC = 31 << 9,
  UI_BTYPE_CURVE = 32 << 9,
  /** Profile editing widget */
  UI_BTYPE_CURVEPROFILE = 33 << 9,
  UI_BTYPE_LISTBOX = 36 << 9,
  UI_BTYPE_LISTROW = 37 << 9,
  UI_BTYPE_HSVCIRCLE = 38 << 9,
  UI_BTYPE_TRACK_PREVIEW = 40 << 9,

  /** Buttons with value >= #UI_BTYPE_SEARCH_MENU don't get undo pushes. */
  UI_BTYPE_SEARCH_MENU = 41 << 9,
  UI_BTYPE_EXTRA = 42 << 9,
  /** A preview image (#PreviewImage), with text under it. Typically bigger than normal buttons and
   * laid out in a grid, e.g. like the File Browser in thumbnail display mode. */
  UI_BTYPE_PREVIEW_TILE = 43 << 9,
  UI_BTYPE_HOTKEY_EVENT = 46 << 9,
  /** Non-interactive image, used for splash screen */
  UI_BTYPE_IMAGE = 47 << 9,
  UI_BTYPE_HISTOGRAM = 48 << 9,
  UI_BTYPE_WAVEFORM = 49 << 9,
  UI_BTYPE_VECTORSCOPE = 50 << 9,
  UI_BTYPE_PROGRESS = 51 << 9,
  UI_BTYPE_NODE_SOCKET = 53 << 9,
  UI_BTYPE_SEPR = 54 << 9,
  UI_BTYPE_SEPR_LINE = 55 << 9,
  /** Dynamically fill available space. */
  UI_BTYPE_SEPR_SPACER = 56 << 9,
  /** Resize handle (resize UI-list). */
  UI_BTYPE_GRIP = 57 << 9,
  UI_BTYPE_DECORATOR = 58 << 9,
  /** An item a view (see #ui::AbstractViewItem). */
  UI_BTYPE_VIEW_ITEM = 59 << 9,
};