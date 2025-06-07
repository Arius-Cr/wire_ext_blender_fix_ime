typedef struct WorkSpaceLayout {
  struct WorkSpaceLayout *next, *prev;

  struct bScreen *screen;
  /* The name of this layout, we override the RNA name of the screen with this
   * (but not ID name itself) */
  char name[/*MAX_NAME*/ 64];
} WorkSpaceLayout;