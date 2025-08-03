struct uiBut {

  /** Pointer back to the layout item holding this button. */
  uiLayout *layout = nullptr;
  int flag = 0;
  int drawflag = 0;
  char flag2 = 0;

  ButType type = ButType(0);
  ButPointerType pointype = ButPointerType::None;
  bool bit = 0;
  /* 0-31 bit index. */
  char bitnr = 0;

  /** When non-zero, this is the key used to activate a menu items (`a-z` always lower case). */
  uchar menu_key = 0;

  short retval = 0, strwidth = 0, alignnr = 0;
  short ofs = 0, pos = 0, selsta = 0, selend = 0;

  /**
   * Optional color for monochrome icon. Also used as text
   * color for labels without icons. Set with #UI_but_color_set().
   */
  uchar col[4] = {0};

  std::string str;

  std::string drawstr;

  char *placeholder = nullptr;

  /** Block relative coordinates. */
  rctf rect = {};

  char *poin = nullptr;
  float hardmin = 0, hardmax = 0, softmin = 0, softmax = 0;

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
  uiButArgNFree func_argN_free_fn;
  uiButArgNCopy func_argN_copy_fn;

  const bContextStore *context = nullptr;

  uiButCompleteFunc autocomplete_func = nullptr;
  void *autofunc_arg = nullptr;

  uiButHandleRenameFunc rename_func = nullptr;
  void *rename_arg1 = nullptr;
  void *rename_orig = nullptr;

  /**
   * When defined, and the button edits a string RNA property,
   * the new name is _not_ set at all, instead this function is called with the new name.
   */
  std::function<void(std::string &new_name)> rename_full_func = nullptr;
  std::string rename_full_new;

  /** Run an action when holding the button down. */
  uiButHandleHoldFunc hold_func = nullptr;
  void *hold_argN = nullptr;

  blender::StringRef tip;
  uiButToolTipFunc tip_func = nullptr;
  void *tip_arg = nullptr;
  uiFreeArgFunc tip_arg_free = nullptr;
  /** Function to override the label to be displayed in the tooltip. */
  std::function<std::string(const uiBut *)> tip_quick_func;

  uiButToolTipCustomFunc tip_custom_func = nullptr;

  /** info on why button is disabled, displayed in tooltip */
  const char *disabled_info = nullptr;

  /** Little indicator (e.g., counter) displayed on top of some icons. */
  IconTextOverlay icon_overlay_text = {};

  /** Copied from the #uiBlock.emboss */
  blender::ui::EmbossType emboss = blender::ui::EmbossType::Emboss;
  /** direction in a pie menu, used for collision detection. */
  RadialDirection pie_dir = UI_RADIAL_NONE;
  /** could be made into a single flag */
  bool changed = false;

  BIFIconID icon = ICON_NONE;

  /** Affects the order if this uiBut is used in menu-search. */
  float search_weight = 0.0f;

  short iconadd = 0;
  /** so buttons can support unit systems which are not RNA */
  uchar unit_type = 0;

  /** See #UI_but_menu_disable_hover_open(). */
  bool menu_no_hover_open = false;

  /** #ButType::Block data */
  uiBlockCreateFunc block_create_func = nullptr;

  /** #ButType::Pulldown / #ButType::Menu data */
  uiMenuCreateFunc menu_create_func = nullptr;

  uiMenuStepFunc menu_step_func = nullptr;

  /* RNA data */
  PointerRNA rnapoin = {};
  PropertyRNA *rnaprop = nullptr;
  int rnaindex = 0;

  BIFIconID drag_preview_icon_id;
  void *dragpoin = nullptr;
  const ImBuf *imb = nullptr;
  float imb_scale = 0;
  eWM_DragDataType dragtype = WM_DRAG_ID;
  int8_t dragflag = 0;

  /**
   * Keep an operator attached but never actually call it through the button. See
   * #UI_but_operator_set_never_call().
   */
  bool operator_never_call = false;
  /* Operator data */
  blender::wm::OpCallContext opcontext = blender::wm::OpCallContext::InvokeDefault;
  wmOperatorType *optype = nullptr;
  PointerRNA *opptr = nullptr;

  ListBase extra_op_icons = {nullptr, nullptr}; /** #uiButExtraOpIcon */

  /**
   * Active button data, set when the user is hovering or interacting with a button (#UI_HOVER and
   * #UI_SELECT state mostly).
   */
  uiHandleButtonData *active = nullptr;
  /**
   * Event handling only supports one active button at a time, but there are cases where that's not
   * enough. A common one is to keep some filter button active to receive text input, while other
   * buttons remain active for interaction.
   *
   * Buttons that have #semi_modal_state set will be temporarily activated for event handling. If
   * they don't consume the event (for example text input events) the event will be forwarded to
   * other buttons.
   *
   * Currently only text buttons support this well.
   */
  uiHandleButtonData *semi_modal_state = nullptr;

  /** Custom button data (borrowed, not owned). */
  void *custom_data = nullptr;

  char *editstr = nullptr;
  double *editval = nullptr;
  float *editvec = nullptr;

  std::function<bool(const uiBut &)> pushed_state_func;

  /* pointer back */
  uiBlock *block = nullptr;

  uiBut() = default;
  /** Performs a mostly shallow copy for now. Only contained C++ types are deep copied. */
  uiBut(const uiBut &other) = default;
  /** Mostly shallow copy, just like copy constructor above. */
  uiBut &operator=(const uiBut &other) = default;

  virtual ~uiBut() = default;
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

  /* WARNING: rest of #uiBut.flag in `UI_interface_c.hh`. */
};

enum class ButType : int8_t {
  But = 1,
  Row,
  Text,
  /** Drop-down list. */
  Menu,
  ButMenu,
  /** Number button. */
  Num,
  /** Number slider. */
  NumSlider,
  Toggle,
  ToggleN,
  IconToggle,
  IconToggleN,
  /** Same as regular toggle, but no on/off state displayed. */
  ButToggle,
  /** Similar to toggle, display a 'tick'. */
  Checkbox,
  CheckboxN,
  Color,
  Tab,
  Popover,
  Scroll,
  Block,
  Label,
  KeyEvent,
  HsvCube,
  /** Menu (often used in headers), `*_MENU` with different draw-type. */
  Pulldown,
  Roundbox,
  ColorBand,
  /** Sphere widget (used to input a unit-vector, aka normal). */
  Unitvec,
  Curve,
  /** Profile editing widget. */
  CurveProfile,
  ListBox,
  ListRow,
  HsvCircle,
  TrackPreview,

  /** Buttons with value >= #ButType::SearchMenu don't get undo pushes. */
  SearchMenu,
  Extra,
  /** A preview image (#PreviewImage), with text under it. Typically bigger than normal buttons and
   * laid out in a grid, e.g. like the File Browser in thumbnail display mode. */
  PreviewTile,
  HotkeyEvent,
  /** Non-interactive image, used for splash screen. */
  Image,
  Histogram,
  Waveform,
  Vectorscope,
  Progress,
  NodeSocket,
  Sepr,
  SeprLine,
  /** Dynamically fill available space. */
  SeprSpacer,
  /** Resize handle (resize UI-list). */
  Grip,
  Decorator,
  /** An item a view (see #ui::AbstractViewItem). */
  ViewItem,
};