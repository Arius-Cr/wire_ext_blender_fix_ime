struct uiPopupBlockHandle {
  /* internal */
  struct ARegion *region;

  /** Use only for #UI_BLOCK_MOVEMOUSE_QUIT popups. */
  float towards_xy[2];
  double towardstime;
  bool dotowards;

  bool popup;
  void (*popup_func)(struct bContext *C, void *arg, int event);
  void (*cancel_func)(struct bContext *C, void *arg);
  void *popup_arg;

  /** Store data for refreshing popups. */
  struct uiPopupBlockCreate popup_create_vars;
  /** True if we can re-create the popup using #uiPopupBlockHandle.popup_create_vars. */
  bool can_refresh;
  bool refresh;

  struct wmTimer *scrolltimer;
  float scrolloffset;

  struct uiKeyNavLock keynav_state;

  /* for operator popups */
  struct wmOperator *popup_op;
  struct ScrArea *ctx_area;
  struct ARegion *ctx_region;

  /* return values */
  int butretval;
  int menuretval;
  int retvalue;
  float retvec[4];

  /** Menu direction. */
  int direction;

  /* Previous values so we don't resize or reposition on refresh. */
  rctf prev_block_rect;
  rctf prev_butrct;
  short prev_dir1, prev_dir2;
  int prev_bounds_offset[2];

  /* Maximum estimated size to avoid having to reposition on refresh. */
  float max_size_x, max_size_y;

  /* #ifdef USE_DRAG_POPUP */
  bool is_grab;
  int grab_xy_prev[2];
  /* #endif */
};