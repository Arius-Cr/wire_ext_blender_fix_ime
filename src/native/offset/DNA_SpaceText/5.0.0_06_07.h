struct SpaceText_Runtime {

  /** Actual line height, scaled by DPI. */
  int lheight_px = 0;

  /** Runtime computed, character width. */
  int cwidth_px = 0;

  /** The handle of the scroll-bar which can be clicked and dragged. */
  rcti scroll_region_handle{0, 0, 0, 0};
  /** The region for selected text to show in the scrolling area. */
  rcti scroll_region_select{0, 0, 0, 0};

  /** Number of digits to show in the line numbers column (when enabled). */
  int line_number_display_digits = 0;

  /** Number of lines this window can display (even when they aren't used). */
  int viewlines = 0;

  /** Use for drawing scroll-bar & calculating scroll operator motion scaling. */
  float scroll_px_per_line = 0.0f;

  /**
   * Run-time for scroll increments smaller than a line (smooth scroll).
   * Values must be between zero and the line, column width: (cwidth, TXT_LINE_HEIGHT(st)).
   */
  int scroll_ofs_px[2]{0, 0};

  /** Cache for faster drawing. */
  void *drawcache = nullptr;
};

/** Text Editor. */
typedef struct SpaceText {
  SpaceLink *next, *prev;
  /** Storage of regions for inactive spaces. */
  ListBase regionbase;
  char spacetype;
  char link_flag;
  char _pad0[6];
  /* End 'SpaceLink' header. */

  struct Text *text;

  /** Determines at what line the top of the text is displayed. */
  int top;

  /** Determines the horizontal scroll (in columns). */
  int left;
  char _pad1[4];

  short flags;

  /** User preference, is font_size! */
  short lheight;

  int tabnumber;

  /* Booleans */
  char wordwrap;
  char doplugins;
  char showlinenrs;
  char showsyntax;
  char line_hlight;
  char overwrite;
  /** Run python while editing, evil. */
  char live_edit;
  char _pad2[1];

  char findstr[/*ST_MAX_FIND_STR*/ 256];
  char replacestr[/*ST_MAX_FIND_STR*/ 256];

  /** Column number to show right margin at. */
  short margin_column;
  char _pad3[2];

  /** Keep last. */
  SpaceText_Runtime *runtime;
} SpaceText;