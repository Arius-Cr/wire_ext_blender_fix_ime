typedef struct Strip {
    struct Strip *next, *prev;
    void *_pad;
    /** Needed (to be like ipo), else it will raise libdata warnings, this should never be used. */
    void *lib;
    /** STRIP_NAME_MAXSTR - name, set by default and needs to be unique, for RNA paths. */
    char name[64];
  
    /** Flags bitmap (see below) and the type of sequence. */
    int flag, type;
    /** The length of the contents of this strip - before handles are applied. */
    int len;
    /**
     * Start frame of contents of strip in absolute frame coordinates.
     * For meta-strips start of first strip startdisp.
     */
    float start;
    /**
     * Frames after the first frame where display starts,
     * frames before the last frame where display ends.
     */
    float startofs, endofs;
    /**
     * Frames that use the first frame before data begins,
     * frames that use the last frame after data ends.
     */
    float startstill, endstill;
    /** Machine: the strip channel */
    int machine;
    /** Starting and ending points of the effect strip. Undefined for other strip types. */
    int startdisp, enddisp;
    float sat;
    float mul;
  
    /** Stream-index for movie or sound files with several streams. */
    short streamindex;
    short _pad1;
    /** For multi-camera source selection. */
    int multicam_source;
    /** MOVIECLIP render flags. */
    int clip_flag;
  
    StripData *data;
  
    /** Old animation system, deprecated for 2.5. */
    struct Ipo *ipo DNA_DEPRECATED;
  
    /** these ID vars should never be NULL but can be when linked libraries fail to load,
     * so check on access */
    struct Scene *scene;
    /** Override scene camera. */
    struct Object *scene_camera;
    /** For MOVIECLIP strips. */
    struct MovieClip *clip;
    /** For MASK strips. */
    struct Mask *mask;
    /** For MOVIE strips. */
    ListBase anims;
  
    float effect_fader;
    /* DEPRECATED, only used for versioning. */
    float speed_fader;
  
    /* pointers for effects: */
    struct Strip *seq1, *seq2;
  
    /* This strange padding is needed due to how `seqbasep` de-serialization is
     * done right now in #scene_blend_read_data. */
    void *_pad7;
    int _pad8[2];
  
    /** List of strips for meta-strips. */
    ListBase seqbase;
    ListBase channels; /* SeqTimelineChannel */
  
    /* List of strip connections (one-way, not bidirectional). */
    ListBase connections; /* StripConnection */
  
    /** The linked "bSound" object. */
    struct bSound *sound;
    /** Handle to #AUD_SequenceEntry. */
    void *scene_sound;
    float volume;
  
    /** Pitch (-0.1..10), pan -2..2. */
    float pitch DNA_DEPRECATED, pan;
    float strobe;
  
    float sound_offset;
    char _pad4[4];
  
    /** Struct pointer for effect settings. */
    void *effectdata;
  
    /** Only use part of animation file. */
    int anim_startofs;
    /** Is subtle different to startofs / endofs. */
    int anim_endofs;
  
    int blend_mode;
    float blend_opacity;
  
    /* Tag color showed if `SEQ_TIMELINE_SHOW_STRIP_COLOR_TAG` is set. */
    int8_t color_tag;
  
    char alpha_mode;
    char _pad2[2];
  
    int cache_flag;
  
    /* is sfra needed anymore? - it looks like its only used in one place */
    /** Starting frame according to the timeline of the scene. */
    int sfra;
  
    /* Multiview */
    char views_format;
    char _pad3[3];
    struct Stereo3dFormat *stereo3d_format;
  
    struct IDProperty *prop;
  
    /* modifiers */
    ListBase modifiers;
  
    /* Playback rate of strip content in frames per second. */
    float media_playback_rate;
    float speed_factor;
  
    struct SeqRetimingKey *retiming_keys;
    void *_pad5;
    int retiming_keys_num;
    char _pad6[4];
  
    StripRuntime runtime;
} Strip;

typedef struct TextVars {
    char text[512];
    struct VFont *text_font;
    int text_blf_id;
    float text_size;
    float color[4], shadow_color[4], box_color[4], outline_color[4];
    float loc[2];
    float wrap_width;
    float box_margin;
    float box_roundness;
    float shadow_angle;
    float shadow_offset;
    float shadow_blur;
    float outline_width;
    char flag;
    char align;
    char _pad[2];
  
    /** Offsets in characters (unicode code-points) for #TextVars::text. */
    int cursor_offset;
    int selection_start_offset;
    int selection_end_offset;
  
    char align_y DNA_DEPRECATED /* Only used for versioning. */;
    char anchor_x, anchor_y;
    char _pad1;
    TextVarsRuntime *runtime;
} TextVars;

enum {
    /* `SELECT = (1 << 0)` */
    SEQ_LEFTSEL = (1 << 1),
    SEQ_RIGHTSEL = (1 << 2),
    SEQ_OVERLAP = (1 << 3),
    SEQ_FILTERY = (1 << 4),
    SEQ_MUTE = (1 << 5),
    SEQ_FLAG_TEXT_EDITING_ACTIVE = (1 << 6),
    SEQ_REVERSE_FRAMES = (1 << 7),
    SEQ_IPO_FRAME_LOCKED = (1 << 8),
    SEQ_EFFECT_NOT_LOADED = (1 << 9),
    SEQ_FLAG_DELETE = (1 << 10),
    SEQ_FLIPX = (1 << 11),
    SEQ_FLIPY = (1 << 12),
    SEQ_MAKE_FLOAT = (1 << 13),
    SEQ_LOCK = (1 << 14),
    SEQ_USE_PROXY = (1 << 15),
    SEQ_IGNORE_CHANNEL_LOCK = (1 << 16),
    SEQ_AUTO_PLAYBACK_RATE = (1 << 17),
    SEQ_SINGLE_FRAME_CONTENT = (1 << 18),
    SEQ_SHOW_RETIMING = (1 << 19),
    SEQ_SHOW_OFFSETS = (1 << 20),
    SEQ_MULTIPLY_ALPHA = (1 << 21),
  
    SEQ_USE_EFFECT_DEFAULT_FADE = (1 << 22),
    SEQ_USE_LINEAR_MODIFIERS = (1 << 23),
  
    /* flags for whether those properties are animated or not */
    SEQ_AUDIO_VOLUME_ANIMATED = (1 << 24),
    SEQ_AUDIO_PITCH_ANIMATED = (1 << 25),
    SEQ_AUDIO_PAN_ANIMATED = (1 << 26),
    SEQ_AUDIO_DRAW_WAVEFORM = (1 << 27),
  
    /* don't include Annotations in OpenGL previews of Scene strips */
    SEQ_SCENE_NO_ANNOTATION = (1 << 28),
    SEQ_USE_VIEWS = (1 << 29),
  
    /* Access scene strips directly (like a meta-strip). */
    SEQ_SCENE_STRIPS = (1 << 30),
  
    SEQ_INVALID_EFFECT = (1u << 31),
};