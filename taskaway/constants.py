# Element ID's
TASK_TABLE_ID = "task_table"
HELP_TABLE_ID = "help_table"

# Table column ID's
COL_SHORT_PROJECT: str = "project"
COL_DESCRIPTION: str = "description"
COL_URGENCY: str = "urg"
COL_AGE: str = "age"
COL_TAGS: str = "tags"
COL_FULL_PROJECT: str = "full_project"
COL_UUID: str = "uuid"
COL_FULL_PROJECT_HIDDEN: str = "full_project_hidden"
COL_UUID_HIDDEN: str = "uuid_hidden"
COL_DUE: str = "due"
COL_ANNOTATIONS: str = "annotations"
COL_ACTIVE: str = "active"
COL_ACTIVE_HIDDEN: str = "active_hidden"
COL_DESCRIPTION_HIDDEN: str = "description_hidden"

DEFAULT_VISIBLE_COLUMNS = [
    COL_DESCRIPTION,
    COL_AGE,
    COL_DUE,
    COL_TAGS,
]

ALL_VISIBLE_COLUMNS = [
    COL_DESCRIPTION,
    COL_URGENCY,
    COL_AGE,
    COL_TAGS,
    COL_FULL_PROJECT,
    COL_UUID,
    COL_DUE,
    COL_ANNOTATIONS,
    COL_ACTIVE,
]

# Task field ID's
TASK_DESCRIPTION = "description"
TASK_ENTRY = "entry"
TASK_PROJECT = "project"
TASK_TAGS = "tags"
TASK_URGENCY = "urgency"
TASK_UUID = "uuid"
TASK_DUE = "due"
TASK_CONTEXT = "context"
TASK_ANNOTATIONS = "annotations"
TASK_STARTED = "start"
