from datetime import timedelta
from tasklib import Task
from datetime import datetime, timezone
from typing import Optional

from taskaway.constants import (
    COL_ACTIVE,
    COL_ACTIVE_HIDDEN,
    COL_AGE,
    COL_ANNOTATIONS,
    COL_DESCRIPTION,
    COL_DESCRIPTION_HIDDEN,
    COL_DUE,
    COL_FULL_PROJECT,
    COL_FULL_PROJECT_HIDDEN,
    COL_SHORT_PROJECT,
    COL_TAGS,
    COL_URGENCY,
    COL_UUID,
    COL_UUID_HIDDEN,
    TASK_ANNOTATIONS,
    TASK_DESCRIPTION,
    TASK_DUE,
    TASK_ENTRY,
    TASK_PROJECT,
    TASK_STARTED,
    TASK_TAGS,
    TASK_URGENCY,
    TASK_UUID,
)


def get_time_representation(delta: timedelta) -> str:
    """Represents the timedelta in a rounded human readable string"""
    total_seconds = int(delta.total_seconds())
    total_seconds_abs = abs(total_seconds)
    sign: str = "-" if total_seconds > 0 else ""

    if total_seconds_abs < 60:
        return f"{sign}{total_seconds_abs}s"

    total_minutes = int(total_seconds_abs / 60)
    if total_minutes < 60:
        return f"{sign}{total_minutes}m"

    total_hours = int(total_minutes / 60)
    if total_hours < 24:
        return f"{sign}{total_hours}h"

    total_days = int(total_hours / 24)
    if total_days < 365:
        return f"{sign}{total_days}d"

    return f"{sign}{int(total_days/365)}y"


def get_parent_project(project: str) -> str:
    """Returns the parent project of a given project
    example:
        'foo.bar' -> 'foo'
        'foo' -> ''
    """
    if not project:
        return ""
    return ".".join(project.split(".")[:-1])


def get_all_projects_from_tasks(tasks: list[Task]) -> set[str]:
    """Given a set of tasks will return the set of full length name projects as well as the full name of all
    parent projects of the tasks
    """
    projects: set[str] = set()
    for task in tasks:
        task_project: str = task["project"]
        project = str(task_project) if task_project else ""

        while project:
            projects.add(project)

            last_dot: int = project.rfind(".")
            if last_dot == -1:
                break

            project = project[0:last_dot]
    return projects


def get_column_value_for_task(task: Task, column_name: str) -> str:
    if column_name == COL_AGE:
        return get_time_representation(task[TASK_ENTRY] - datetime.now(tz=timezone.utc))
    elif column_name == COL_DESCRIPTION or column_name == COL_DESCRIPTION_HIDDEN:
        return task[TASK_DESCRIPTION]
    elif column_name == COL_FULL_PROJECT or column_name == COL_FULL_PROJECT_HIDDEN:
        return task[TASK_PROJECT]
    elif column_name == COL_SHORT_PROJECT:
        return None
    elif column_name == COL_TAGS:
        return ",".join(task[TASK_TAGS])
    elif column_name == COL_URGENCY:
        return task[TASK_URGENCY]
    elif column_name == COL_DUE:
        due: Optional[datetime] = task[TASK_DUE]
        return get_time_representation(datetime.now(tz=timezone.utc) - due) if due else None
    elif column_name == COL_UUID or column_name == COL_UUID_HIDDEN:
        return task[TASK_UUID]
    elif column_name == COL_ANNOTATIONS:
        return "\n".join(f"{x['entry'].strftime('%Y-%m-%d')}: {x['description']}" for x in task[TASK_ANNOTATIONS])
    elif column_name == COL_ACTIVE:
        started: Optional[datetime] = task[TASK_STARTED]
        return get_time_representation(started - datetime.now(tz=timezone.utc)) if started else None
    elif column_name == COL_ACTIVE_HIDDEN:
        started: Optional[datetime] = task[TASK_STARTED]
        return int((datetime.now(tz=timezone.utc) - started).total_seconds()) if started else 999999999
    raise RuntimeError(f"unsupported column name {column_name}")
