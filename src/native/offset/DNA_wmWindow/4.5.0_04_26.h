typedef struct wmWindow {
    struct wmWindow *next, *prev;
  
    /** Don't want to include ghost.h stuff. */
    void *ghostwin;
    /** Don't want to include gpu stuff. */
    void *gpuctx;
  
    /** Parent window. */
    struct wmWindow *parent;
  
    /** Active scene displayed in this window. */
    struct Scene *scene;
    /** Temporary when switching. */
    struct Scene *new_scene;
    /** Active view layer displayed in this window. */
    char view_layer_name[64];
    /** The workspace may temporarily override the window's scene with scene pinning. This is the
     * "overridden" or "default" scene to restore when entering a workspace with no scene pinned. */
    struct Scene *unpinned_scene;
  
    struct WorkSpaceInstanceHook *workspace_hook;
  
    /** Global areas aren't part of the screen, but part of the window directly.
     * \note Code assumes global areas with fixed height, fixed width not supported yet */
    ScrAreaMap global_areas;
  
    struct bScreen *screen DNA_DEPRECATED;
  
    /** Window-ID also in screens, is for retrieving this window after read. */
    int winid;
    /** Window coords (in pixels). */
    short posx, posy;
    /**
     * Window size (in pixels).
     *
     * \note Loading a window typically uses the size & position saved in the blend-file,
     * there is an exception for startup files which works as follows:
     * Setting the window size to zero before `ghostwin` has been set has a special meaning,
     * it causes the window size to be initialized to `wm_init_state.size`.
     * These default to the main screen size but can be overridden by the `--window-geometry`
     * command line argument.
     */
    short sizex, sizey;
    /** Normal, maximized, full-screen, #GHOST_TWindowState. */
    char windowstate;
    /** Set to 1 if an active window, for quick rejects. */
    char active;
    /** Current mouse cursor type. */
    short cursor;
    /** Previous cursor when setting modal one. */
    short lastcursor;
    /** The current modal cursor. */
    short modalcursor;
    /** Cursor grab mode #GHOST_TGrabCursorMode (run-time only) */
    short grabcursor;
    /** Internal: tag this for extra mouse-move event,
     * makes cursors/buttons active on UI switching. */
  
    /** Internal, lock pie creation from this event until released. */
    short pie_event_type_lock;
    /**
     * Exception to the above rule for nested pies, store last pie event for operators
     * that spawn a new pie right after destruction of last pie.
     */
    short pie_event_type_last;
  
    char addmousemove;
    char tag_cursor_refresh;
  
    /* Track the state of the event queue,
     * these store the state that needs to be kept between handling events in the queue. */
    /** Enable when #KM_PRESS events are not handled (keyboard/mouse-buttons only). */
    char event_queue_check_click;
    /** Enable when #KM_PRESS events are not handled (keyboard/mouse-buttons only). */
    char event_queue_check_drag;
    /**
     * Enable when the drag was handled,
     * to avoid mouse-motion continually triggering drag events which are not handled
     * but add overhead to gizmo handling (for example), see #87511.
     */
    char event_queue_check_drag_handled;
  
    /** The last event type (that passed #WM_event_consecutive_gesture_test check). */
    char event_queue_consecutive_gesture_type;
    /** The cursor location when `event_queue_consecutive_gesture_type` was set. */
    int event_queue_consecutive_gesture_xy[2];
    /** See #WM_event_consecutive_data_get and related API. Freed when consecutive events end. */
    struct wmEvent_ConsecutiveData *event_queue_consecutive_gesture_data;
  
    /**
     * Storage for event system.
     *
     * For the most part this is storage for `wmEvent.xy` & `wmEvent.modifiers`.
     * newly added key/button events copy the cursor location and modifier state stored here.
     *
     * It's also convenient at times to be able to pass this as if it's a regular event.
     *
     * - This is not simply the current event being handled.
     *   The type and value is always set to the last press/release events
     *   otherwise cursor motion would always clear these values.
     *
     * - The value of `eventstate->modifiers` is set from the last pressed/released modifier key.
     *   This has the down side that the modifier value will be incorrect if users hold both
     *   left/right modifiers then release one. See note in #wm_event_add_ghostevent for details.
     */
    struct wmEvent *eventstate;
    /**
     * Keep the last handled event in `event_queue` here (owned and must be freed).
     *
     * \warning This must only to be used for event queue logic.
     * User interactions should use `eventstate` instead (if the event isn't passed to the function).
     */
    struct wmEvent *event_last_handled;
  
    /**
     * Input Method Editor data - complex character input (especially for Asian character input)
     * Only used when `WITH_INPUT_IME` is defined, runtime-only data.
     */
    const struct wmIMEData *ime_data;
    char ime_data_is_composing;
    char _pad1[7];
  
    /** Window+screen handlers, handled last. */
    ListBase handlers;
    /** Priority handlers, handled first. */
    ListBase modalhandlers;
  
    /** Gesture stuff. */
    ListBase gesture;
  
    /** Properties for stereoscopic displays. */
    struct Stereo3dFormat *stereo3d_format;
  
    /** Custom drawing callbacks. */
    ListBase drawcalls;
  
    /** Private runtime info to show text in the status bar. */
    void *cursor_keymap_status;
  
    /**
     * The time when the key is pressed in milliseconds (see #GHOST_GetEventTime).
     * Used to detect double-click events.
     */
    uint64_t eventstate_prev_press_time_ms;
  
    void *_pad2;
    WindowRuntimeHandle *runtime;
} wmWindow;