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
- Sort tasks chronologically so the day reads in time order
- Filter tasks by pet name, completion status, and due date scope
- Mark tasks complete and automatically create the next daily or weekly occurrence
- Detect exact-time conflicts and surface warnings before schedule generation
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

- `sort_by_time()` orders tasks by due date, scheduled time, and then priority
- `filter_tasks()` narrows the view by pet, completion status, or due date
- `mark_task_complete()` creates the next recurring task for daily and weekly care
- `detect_conflicts()` returns warnings when two due tasks share the same exact time
- `generate_plan()` builds a schedule that fits inside the owner's available time budget

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

- Chronological sorting
- Filtering by pet and completion status
- Daily and weekly recurrence
- Conflict detection for duplicate times
- Empty-state scheduling when pets have no tasks

Confidence Level: 4/5 stars. The current suite gives strong coverage for the main scheduling behaviors and several important edge cases, but the app would be even more reliable with additional tests for overlapping durations and longer multi-day planning flows.
