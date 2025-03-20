typedef struct WorkSpaceInstanceHook {
    WorkSpace *active;
    struct WorkSpaceLayout *act_layout;
  
    /**
     * Needed because we can't change work-spaces/layouts in running handler loop,
     * it would break context.
     */
    WorkSpace *temp_workspace_store;
    struct WorkSpaceLayout *temp_layout_store;
} WorkSpaceInstanceHook;