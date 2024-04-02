typedef struct ARegion {
  struct ARegion *next, *prev;

  /** 2D-View scrolling/zoom info (most regions are 2d anyways). */
  View2D v2d;
  /** Coordinates of region. */
  rcti winrct;
  /** Runtime for partial redraw, same or smaller than winrct. */
  rcti drawrct;
  /** Size. */
  short winx, winy;

  /** Region is currently visible on screen. */
  short visible;
  /** Window, header, etc. identifier for drawing. */
  short regiontype;
  /** How it should split. */
  short alignment;
  /** Hide, .... */
  short flag;

  /** Current split size in unscaled pixels (if zero it uses regiontype).
   * To convert to pixels use: `UI_DPI_FAC * region->sizex + 0.5f`.
   * However to get the current region size, you should usually use winx/winy from above, not this!
   */
  short sizex, sizey;

  /** Private, cached notifier events. */
  short do_draw;
  /** Private, cached notifier events. */
  short do_draw_paintcursor;
  /** Private, set for indicate drawing overlapped. */
  short overlap;
  /** Temporary copy of flag settings for clean fullscreen. */
  short flagfullscreen;

  /** Callbacks for this region type. */
  struct ARegionType *type;

  /** #uiBlock. */
  ListBase uiblocks;
  /** Panel. */
  ListBase panels;
  /** Stack of panel categories. */
  ListBase panels_category_active;
  /** #uiList. */
  ListBase ui_lists;
  /** #uiPreview. */
  ListBase ui_previews;
  /** #wmEventHandler. */
  ListBase handlers;
  /** Panel categories runtime. */
  ListBase panels_category;

  /** Gizmo-map of this region. */
  struct wmGizmoMap *gizmo_map;
  /** Blend in/out. */
  struct wmTimer *regiontimer;
  struct wmDrawBuffer *draw_buffer;

  /** Use this string to draw info. */
  char *headerstr;
  /** XXX 2.50, need spacedata equivalent? */
  void *regiondata;

  ARegion_Runtime runtime;
} ARegion;