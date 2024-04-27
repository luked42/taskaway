# Project View
Project view enables users to view project hierarchies. The project view makes use of collapsible rows and allows users to drill down into various levels and contexts of a project. 

This is in contrast to a task list where even with filtering applied isn't as aware of the hierarchies of a given project. 

![image](./collasible_rows.excalidraw.png)

# Focus Mode
Focus mode will zoom in to a given high level project. e.g whilst having a task in `work.pull_requests` highlighted, entering focus mode will zoom in to the `work.pull_requests` project essentially enabling a filter on `project:work.pull_requests` for the current view.

## Creating a new task whilst in focus mode
When adding a new task whilst having focus mode enabled the task will by default have the project of the current focus enabled. e.g when creating a new task with the focus project being `work.pull_requests` the task will be created by default with the `project:work.pull_requests`.

## Exiting focus mode
When exiting focus more state should be stored on the stack and restored. State should be stored with with a combination of `current_filter` and `task_uuid` for both which tasks should be currently displayed, and which task is the current selected row. If the task no longer exists default to first task.