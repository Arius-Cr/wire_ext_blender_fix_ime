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

  /** See \ref UI_but_func_identity_compare_set(). */
  uiButIdentityCompareFunc identity_cmp_func;

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
  /** direction in a pie menu, used for collision detection. */
  RadialDirection pie_dir;
  /** could be made into a single flag */
  bool changed;
  /** so buttons can support unit systems which are not RNA */
  uchar unit_type;
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
  wmOperatorCallContext opcontext;

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

  /** Temporarily override the active button for lookups in context, regions, etc. (everything
   * using #ui_context_button_active()). For example, so that operators normally acting on the
   * active button can be polled on non-active buttons to (e.g. for disabling). */
  UI_BUT_ACTIVE_OVERRIDE = (1 << 7),

  /* WARNING: rest of #uiBut.flag in UI_interface.h */
};