enum eWM_EventHandlerType {
    WM_HANDLER_TYPE_GIZMO = 1,
    WM_HANDLER_TYPE_UI,
    WM_HANDLER_TYPE_OP,
    WM_HANDLER_TYPE_DROPBOX,
    WM_HANDLER_TYPE_KEYMAP,
};

struct wmEventHandler {
    wmEventHandler *next, *prev;
  
    eWM_EventHandlerType type;
    eWM_EventHandlerFlag flag;
  
    EventHandlerPoll poll;
};

struct wmEventHandler_UI {
    wmEventHandler head;
  
    /** Callback receiving events. */
    wmUIHandlerFunc handle_fn;
    /** Callback when handler is removed. */
    wmUIHandlerRemoveFunc remove_fn;
    /** User data pointer. */
    void *user_data;
  
    /** Store context for this handler for derived/modal handlers. */
    struct {
      ScrArea *area;
      ARegion *region;
      /**
       * Temporary, floating regions stored in #Screen::regionbase.
       * Used for menus, popovers & dialogs.
       */
      ARegion *region_popup;
    } context;
};