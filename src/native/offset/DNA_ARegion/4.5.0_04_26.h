typedef struct ARegion {
    struct ARegion *next, *prev;
  
    /** 2D-View scrolling/zoom info (most regions are 2d anyways). */
    View2D v2d;
    /** Coordinates of region. */
    rcti winrct;
    /** Size. */
    short winx, winy;
    /**
     * This is a Y offset on the panel tabs that represents pixels,
     * where zero represents no scroll - the first category always shows first at the top.
     */
    int category_scroll;
  
    /** Window, header, etc. identifier for drawing. */
    short regiontype;
    /** How it should split. */
    short alignment;
    /** Hide, .... */
    short flag;
  
    /** Current split size in unscaled pixels (if zero it uses regiontype).
     * To convert to pixels use: `UI_SCALE_FAC * region->sizex + 0.5f`.
     * However to get the current region size, you should usually use winx/winy from above, not this!
     */
    short sizex, sizey;
  
    /** Private, set for indicate drawing overlapped. */
    short overlap;
    /** Temporary copy of flag settings for clean full-screen. */
    short flagfullscreen;
  
    char _pad[2];
  
    /** Panel. */
    ListBase panels;
    /** Stack of panel categories. */
    ListBase panels_category_active;
    /** #uiList. */
    ListBase ui_lists;
    /** #uiPreview. */
    ListBase ui_previews;
    /**
     * Permanent state storage of #ui::AbstractView instances, so hiding regions with views or
     * loading files remembers the view state.
     */
    ListBase view_states; /* #uiViewStateLink */
  
    /** XXX 2.50, need spacedata equivalent? */
    void *regiondata;
  
    ARegionRuntimeHandle *runtime;
} ARegion;

struct ARegionRuntime {
    /** Callbacks for this region type. */
    struct ARegionType *type;
  
    /** Runtime for partial redraw, same or smaller than #ARegion::winrct. */
    rcti drawrct = {};
  
    /**
     * The visible part of the region, use with region overlap not to draw
     * on top of the overlapping regions.
     *
     * Lazy initialize, zeroed when unset, relative to #ARegion.winrct x/y min.
     */
    rcti visible_rect = {};
  
    /**
     * The offset needed to not overlap with window scroll-bars.
     * Only used by HUD regions for now.
     */
    int offset_x = 0;
    int offset_y = 0;
  
    /** Panel category to use between 'layout' and 'draw'. */
    const char *category = nullptr;
  
    /** Maps #uiBlock::name to uiBlock for faster lookups. */
    Map<std::string, uiBlock *> block_name_map;
    /** #uiBlock. */
    ListBase uiblocks = {};
  
    /** #wmEventHandler. */
    ListBase handlers = {};
  
    /** Use this string to draw info. */
    char *headerstr = nullptr;
  
    /** Gizmo-map of this region. */
    wmGizmoMap *gizmo_map = nullptr;
  
    /** Blend in/out. */
    wmTimer *regiontimer = nullptr;
  
    wmDrawBuffer *draw_buffer = nullptr;
  
    /** Panel categories runtime. */
    ListBase panels_category = {};
  
    /** Region is currently visible on screen. */
    short visible = 0;
  
    /** Private, cached notifier events. */
    short do_draw = 0;
  
    /** Private, cached notifier events. */
    short do_draw_paintcursor;
  
    /** Dummy panel used in popups so they can support layout panels. */
    Panel *popup_block_panel = nullptr;
};