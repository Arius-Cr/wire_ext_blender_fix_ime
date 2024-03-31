typedef enum eWM_EventHandlerType {
  WM_HANDLER_TYPE_GIZMO = 1,
  WM_HANDLER_TYPE_UI,
  WM_HANDLER_TYPE_OP,
  WM_HANDLER_TYPE_DROPBOX,
  WM_HANDLER_TYPE_KEYMAP,
} eWM_EventHandlerType;

typedef struct wmEventHandler {
  struct wmEventHandler *next, *prev;

  eWM_EventHandlerType type;
  eWM_EventHandlerFlag flag;

  EventHandlerPoll poll;
} wmEventHandler;

typedef struct wmEventHandler_UI {
  wmEventHandler head;

  wmUIHandlerFunc handle_fn;       /* callback receiving events */
  wmUIHandlerRemoveFunc remove_fn; /* callback when handler is removed */
  void *user_data;                 /* user data pointer */

  /** Store context for this handler for derived/modal handlers. */
  struct {
    struct ScrArea *area;
    struct ARegion *region;
    struct ARegion *menu;
  } context;
} wmEventHandler_UI;