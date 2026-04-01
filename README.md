# PawPal+ (Module 2 Project)

PawPal+ is a Streamlit app that helps a busy pet owner organize pet care for one or more pets. The app combines a simple interface with a lightweight scheduling engine that can sort tasks, flag conflicts, and manage recurring care.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks such as walks, feeding, meds, enrichment, and grooming
- Consider constraints like time available, task priority, and owner preferences
- Produce a daily plan and explain why it chose that plan

## Features

- Add and manage multiple pets from one owner profile
- Add care tasks with a due date, scheduled time, frequency, duration, and priority
- Sort tasks by priority first and then by due date and time
- Filter tasks by pet name, completion status, and due date scope
- Mark tasks complete and automatically create the next daily or weekly occurrence
- Detect exact-time conflicts and surface warnings before schedule generation
- Suggest the next available care slot when a task does not fit
- Show emoji-based priority and status badges in the Streamlit UI and terminal demo
- Save and restore pet/task data from `data.json`
- Build a daily plan that respects the owner's available minutes
- Explain why tasks were scheduled or skipped

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run app.py
```

### Run the Terminal Demo

```bash
python main.py
```

## 📸 Demo

<a href="/course_images/ai110/pawpal_app_demo.png" target="_blank"><img src='/course_images/ai110/pawpal_app_demo.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

Demo preview of the final Streamlit interface.

## Smarter Scheduling

The scheduler includes a few focused algorithmic features:

- `sort_by_time()` orders tasks by priority, due date, and then scheduled time
- `filter_tasks()` narrows the view by pet, completion status, or due date
- `mark_task_complete()` creates the next recurring task for daily and weekly care
- `detect_conflicts()` returns warnings when two due tasks share the same exact time
- `next_available_slot()` suggests the first open care window that can fit a task
- `generate_plan()` builds a schedule that fits inside the owner's available time budget
- `save_to_json()` and `load_from_json()` keep pets and tasks between app runs

## Agent Mode Notes

The persistence refactor followed a focused Agent Mode workflow: plan the data conversion first, implement custom dictionary serialization for `Task`, `Pet`, and `Owner`, then wire the Streamlit state to load from disk on startup and save after user actions. That kept the JSON handling easy to trace and reduced the risk of mixing UI logic with storage logic.

I also used Agent Mode as a bounded implementation pass for persistence while keeping the higher-level scheduling and UI decisions under manual review. That made it easier to let AI handle repetitive JSON plumbing without giving up architectural control of the app.

## Architecture

The final class design is captured in `uml_final.png` in the project root. The system centers on four classes:

- `Task` stores care details plus recurrence behavior
- `Pet` owns task lists for one animal
- `Owner` manages pets and provides system-wide task access
- `Scheduler` sorts, filters, warns, and builds the daily plan

## Testing PawPal+

Run the automated test suite with:

```bash
python -m pytest
```

The tests cover:

- Priority-first sorting
- Filtering by pet and completion status
- Daily and weekly recurrence
- Conflict detection for duplicate times
- Next available slot suggestions
- JSON persistence round-trips
- Empty-state scheduling when pets have no tasks

Confidence Level: 4/5 stars. The current suite gives strong coverage for the main scheduling behaviors and several important edge cases, but the app would be even more reliable with additional tests for overlapping durations and longer multi-day planning flows.
