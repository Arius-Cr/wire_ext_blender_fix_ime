struct uiBut {
  struct uiBut *next, *prev;

  /** Pointer back to the layout item holding this button. */
  uiLayout *layout;
  int flag, drawflag;
  eButType type;
  eButPointerType pointype;
  short bit, bitnr, retval, strwidth, alignnr;
  short ofs, pos, selsta, selend;

  char *str;
  char strdata[UI_MAX_NAME_STR];
  char drawstr[UI_MAX_DRAW_STR];

  rctf rect; /* block relative coords */

  char *poin;
  float hardmin, hardmax, softmin, softmax;

  /* both these values use depends on the button type
   * (polymorphic struct or union would be nicer for this stuff) */

  /**
   * For #uiBut.type:
   * - UI_BTYPE_LABEL:        Use `(a1 == 1.0f)` to use a2 as a blending factor (imaginative!).
   * - UI_BTYPE_SCROLL:       Use as scroll size.
   * - UI_BTYPE_SEARCH_MENU:  Use as number or rows.
   */
  float a1;

  /**
   * For #uiBut.type:
   * - UI_BTYPE_HSVCIRCLE:    Use to store the luminosity.
   * - UI_BTYPE_LABEL:        If `(a1 == 1.0f)` use a2 as a blending factor.
   * - UI_BTYPE_SEARCH_MENU:  Use as number or columns.
   */
  float a2;

  uchar col[4];

  uiButHandleFunc func;
  void *func_arg1;
  void *func_arg2;

  uiButHandleNFunc funcN;
  void *func_argN;

  struct bContextStore *context;

  uiButCompleteFunc autocomplete_func;
  void *autofunc_arg;

  uiButHandleRenameFunc rename_func;
  void *rename_arg1;
  void *rename_orig;

  /** Run an action when holding the button down. */
  uiButHandleHoldFunc hold_func;
  void *hold_argN;

  const char *tip;
  uiButToolTipFunc tip_func;
  void *tip_arg;
  uiFreeArgFunc tip_arg_free;

  /** info on why button is disabled, displayed in tooltip */
  const char *disabled_info;

  BIFIconID icon;
  /** Copied from the #uiBlock.emboss */
  eUIEmbossType emboss;
  /** direction in a pie menu, used for collision detection (RadialDirection) */
  signed char pie_dir;
  /** could be made into a single flag */
  bool changed;
  /** so buttons can support unit systems which are not RNA */
  uchar unit_type;
  short modifier_key;
  short iconadd;

  /** #UI_BTYPE_BLOCK data */
  uiBlockCreateFunc block_create_func;

  /** #UI_BTYPE_PULLDOWN / #UI_BTYPE_MENU data */
  uiMenuCreateFunc menu_create_func;

  uiMenuStepFunc menu_step_func;

  /* RNA data */
  struct PointerRNA rnapoin;
  struct PropertyRNA *rnaprop;
  int rnaindex;

  /* Operator data */
  struct wmOperatorType *optype;
  struct PointerRNA *opptr;
  short opcontext;

  /** When non-zero, this is the key used to activate a menu items (`a-z` always lower case). */
  uchar menu_key;

  ListBase extra_op_icons; /** #uiButExtraOpIcon */

  /* Drag-able data, type is WM_DRAG_... */
  char dragtype;
  short dragflag;
  void *dragpoin;
  struct ImBuf *imb;
  float imb_scale;

  /** Active button data (set when the user is hovering or interacting with a button). */
  struct uiHandleButtonData *active;

  /** Custom button data (borrowed, not owned). */
  void *custom_data;

  char *editstr;
  double *editval;
  float *editvec;

  uiButPushedStateFunc pushed_state_func;
  const void *pushed_state_arg;

  /* pointer back */
  uiBlock *block;
};

enum {
  /** Use when the button is pressed. */
  UI_SELECT = (1 << 0),
  /** Temporarily hidden (scrolled out of the view). */
  UI_SCROLLED = (1 << 1),
  UI_ACTIVE = (1 << 2),
  UI_HAS_ICON = (1 << 3),
  UI_HIDDEN = (1 << 4),
  /** Display selected, doesn't impact interaction. */
  UI_SELECT_DRAW = (1 << 5),
  /** Property search filter is active and the button does not match. */
  UI_SEARCH_FILTER_NO_MATCH = (1 << 6),
  /* WARNING: rest of #uiBut.flag in UI_interface.h */
};

typedef enum {
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
  /** menu (often used in headers), **_MENU /w different draw-type */
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
  UI_BTYPE_PROGRESS_BAR = 51 << 9,
  UI_BTYPE_NODE_SOCKET = 53 << 9,
  UI_BTYPE_SEPR = 54 << 9,
  UI_BTYPE_SEPR_LINE = 55 << 9,
  /** Dynamically fill available space. */
  UI_BTYPE_SEPR_SPACER = 56 << 9,
  /** Resize handle (resize uilist). */
  UI_BTYPE_GRIP = 57 << 9,
  UI_BTYPE_DECORATOR = 58 << 9,
  /* An item in a tree view. Parent items may be collapsible. */
  UI_BTYPE_TREEROW = 59 << 9,
} eButType;