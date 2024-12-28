struct uiPopupBlockHandle {
  /* internal */
  ARegion *region;

  /** Use only for #UI_BLOCK_MOVEMOUSE_QUIT popups. */
  float towards_xy[2];
  double towardstime;
  bool dotowards;

  bool popup;
  void (*popup_func)(bContext *C, void *arg, int event);
  void (*cancel_func)(bContext *C, void *arg);
  void *popup_arg;

  /** Store data for refreshing popups. */
  uiPopupBlockCreate popup_create_vars;
  /**
   * True if we can re-create the popup using #uiPopupBlockHandle.popup_create_vars.
   *
   * \note Popups that can refresh are called with #bContext::wm::region_popup set
   * to the #uiPopupBlockHandle::region both on initial creation and when refreshing.
   */
  bool can_refresh;
  bool refresh;

  wmTimer *scrolltimer;
  float scrolloffset;

  uiKeyNavLock keynav_state;

  /* for operator popups */
  wmOperator *popup_op;
  ScrArea *ctx_area;
  ARegion *ctx_region;

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

  char menu_idname[64];
};