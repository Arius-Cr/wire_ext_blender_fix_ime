struct uiPopupBlockHandle {
  /* internal */
  ARegion *region = nullptr;

  /** Use only for #UI_BLOCK_MOVEMOUSE_QUIT popups. */
  float towards_xy[2];
  double towardstime = 0.0;
  bool dotowards = false;

  bool popup = false;
  void (*popup_func)(bContext *C, void *arg, int event) = nullptr;
  void (*cancel_func)(bContext *C, void *arg) = nullptr;
  void *popup_arg = nullptr;

  /** Store data for refreshing popups. */
  uiPopupBlockCreate popup_create_vars;
  /**
   * True if we can re-create the popup using #uiPopupBlockHandle.popup_create_vars.
   *
   * \note Popups that can refresh are called with #bContext::wm::region_popup set
   * to the #uiPopupBlockHandle::region both on initial creation and when refreshing.
   */
  bool can_refresh = false;
  bool refresh = false;

  wmTimer *scrolltimer = nullptr;
  float scrolloffset = 0.0f;

  uiKeyNavLock keynav_state;

  /* for operator popups */
  wmOperator *popup_op = nullptr;
  ScrArea *ctx_area = nullptr;
  ARegion *ctx_region = nullptr;

  /* return values */
  int butretval = 0;
  int menuretval = 0;
  int retvalue = 0;
  float retvec[4] = {0.0f, 0.0f, 0.0f, 0.0f};

  /** Menu direction. */
  int direction = 0;

  /* Previous values so we don't resize or reposition on refresh. */
  rctf prev_block_rect = {};
  rctf prev_butrct = {};
  short prev_dir1 = 0;
  short prev_dir2 = 0;
  int prev_bounds_offset[2] = {0, 0};

  /* Maximum estimated size to avoid having to reposition on refresh. */
  float max_size_x = 0.0f;
  float max_size_y = 0.0f;

  /* #ifdef USE_DRAG_POPUP */
  bool is_grab = false;
  int grab_xy_prev[2] = {0, 0};
  /* #endif */

  char menu_idname[64] = "";
};