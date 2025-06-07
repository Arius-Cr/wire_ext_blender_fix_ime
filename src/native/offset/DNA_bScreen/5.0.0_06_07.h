typedef struct bScreen {
#ifdef __cplusplus
  /** See #ID_Type comment for why this is here. */
  static constexpr ID_Type id_type = ID_SCR;
#endif

  ID id;

  /* TODO: Should become ScrAreaMap now.
   * NOTE: KEEP ORDER IN SYNC WITH #ScrAreaMap! (see AREAMAP_FROM_SCREEN macro above). */
  /** Screens have vertices/edges to define areas. */
  ListBase vertbase;
  ListBase edgebase;
  ListBase areabase;
  /* End variables that must be in sync with #ScrAreaMap. */

  /** Screen level regions (menus), runtime only. */
  ListBase regionbase;

  struct Scene *scene DNA_DEPRECATED;

  /** General flags. */
  short flag;
  /** Window-ID from WM, starts with 1. */
  short winid;
  /** User-setting for which editors get redrawn during animation playback. */
  short redraws_flag;

  /** Temp screen in a temp window, don't save (like user-preferences). */
  char temp;
  /** Temp screen for image render display or file-select. */
  char state;
  /** Notifier for drawing edges. */
  char do_draw;
  /** Notifier for scale screen, changed screen, etc. */
  char do_refresh;
  /** Notifier for gesture draw. */
  char do_draw_gesture;
  /** Notifier for paint cursor draw. */
  char do_draw_paintcursor;
  /** Notifier for dragging draw. */
  char do_draw_drag;
  /** Set to delay screen handling after switching back from maximized area. */
  char skip_handling;
  /** Set when scrubbing to avoid some costly updates. */
  char scrubbing;
  char _pad[1];

  /** Active region that has mouse focus. */
  struct ARegion *active_region;

  /** If set, screen has timer handler added in window. */
  struct wmTimer *animtimer;
  /** Context callback. */
  void /*bContextDataCallback*/ *context;

  /** Runtime. */
  struct wmTooltipState *tool_tip;

  PreviewImage *preview;
} bScreen;