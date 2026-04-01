from __future__ import annotations

from datetime import date, time
from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


DATA_FILE = Path(__file__).with_name("data.json")


def default_owner() -> Owner:
    """Create the starter owner used when no saved data exists yet."""
    return Owner(
        name="Jordan",
        available_minutes_per_day=90,
        preferences={"walk_preference": "morning"},
    )


def load_owner() -> Owner:
    """Load the saved owner from disk or fall back to a starter profile."""
    if not DATA_FILE.exists():
        return default_owner()

    try:
        return Owner.load_from_json(DATA_FILE)
    except Exception as error:  # pragma: no cover - defensive UI fallback
        st.warning(f"Could not load saved data from {DATA_FILE.name}: {error}")
        return default_owner()


def save_owner(owner: Owner) -> None:
    """Persist the current owner state to disk."""
    try:
        owner.save_to_json(DATA_FILE)
    except Exception as error:  # pragma: no cover - defensive UI fallback
        st.error(f"Could not save data to {DATA_FILE.name}: {error}")


def get_owner() -> Owner:
    """Create the session owner once and reuse it on later reruns."""
    if "owner" not in st.session_state:
        st.session_state.owner = load_owner()
    return st.session_state.owner


def get_scheduler(owner: Owner) -> Scheduler:
    """Build a scheduler for the current owner and planning day."""
    return Scheduler(owner=owner, plan_date=date.today())


def pet_rows(owner: Owner) -> list[dict[str, int | str]]:
    """Build table rows for the current pets."""
    return [
        {
            "Name": pet.name,
            "Species": pet.species,
            "Age": pet.age_years,
            "Tasks": len(pet.tasks),
        }
        for pet in owner.pets
    ]


def task_rows(tasks: list[Task]) -> list[dict[str, int | str]]:
    """Build table rows for a list of tasks."""
    return [
        {
            "Pet": task.pet_name or "Unknown",
            "Task": task.description,
            "Due Date": task.due_date.isoformat(),
            "Time": task.scheduled_time,
            "Type": task.frequency.title(),
            "Duration": task.duration_minutes,
            "Priority": task.priority_badge,
            "Status": task.status_badge,
        }
        for task in tasks
    ]


def schedule_rows(schedule: list[Task]) -> list[dict[str, int | str]]:
    """Build table rows for the generated plan."""
    return [
        {
            "Due Date": task.due_date.isoformat(),
            "Time": task.scheduled_time,
            "Pet": task.pet_name or "Unknown",
            "Task": task.description,
            "Duration": task.duration_minutes,
            "Priority": task.priority_badge,
        }
        for task in schedule
    ]


def task_label(task: Task) -> str:
    """Return a readable label for task selection widgets."""
    return f"{task.pet_name} | {task.description} | {task.due_date.isoformat()} {task.scheduled_time}"


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

owner = get_owner()
scheduler = get_scheduler(owner)

st.title("🐾 PawPal+")
st.markdown(
    """
PawPal+ helps a busy pet owner keep pet care organized.
Add pets, assign tasks, review conflicts, and build a cleaner schedule for today.
"""
)

if "flash_success" in st.session_state:
    st.success(st.session_state.pop("flash_success"))
if "flash_info" in st.session_state:
    st.info(st.session_state.pop("flash_info"))

with st.expander("How session memory works", expanded=False):
    st.markdown(
        """
This app stores the `Owner` object in `st.session_state`, which works like a dictionary.
The app checks whether `"owner"` already exists before creating a new one, so pets and tasks
stay available across Streamlit reruns during the session.
"""
    )

all_tasks = scheduler.sort_by_time()
today_tasks = scheduler.filter_tasks(all_tasks, due_on=scheduler.plan_date)
today_pending_tasks = scheduler.filter_tasks(today_tasks, completed=False)
conflict_warnings = scheduler.detect_conflicts(today_tasks)

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Pets", len(owner.pets))
metric_col2.metric("Tasks Due Today", len(today_pending_tasks))
metric_col3.metric("Conflicts", len(conflict_warnings))

st.subheader("Owner Settings")
owner_name = st.text_input("Owner name", value=owner.name)
available_minutes = st.number_input(
    "Available minutes for today",
    min_value=15,
    max_value=600,
    value=owner.available_minutes_per_day,
    step=15,
)

owner.name = owner_name
owner.available_minutes_per_day = int(available_minutes)
save_owner(owner)

st.divider()

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age_years = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
    care_notes_text = st.text_area("Care notes", placeholder="Optional notes, one per line")
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    try:
        cleaned_pet_name = pet_name.strip()
        if not cleaned_pet_name:
            raise ValueError("Please enter a pet name before adding a pet.")
        notes = [line.strip() for line in care_notes_text.splitlines() if line.strip()]
        owner.add_pet(
            Pet(
                name=cleaned_pet_name,
                species=species,
                age_years=int(age_years),
                care_notes=notes,
            )
        )
        st.session_state.schedule_generated = False
        st.session_state.flash_success = f"Added {cleaned_pet_name} to {owner.name}'s household."
        st.rerun()
    except ValueError as error:
        st.error(str(error))

if owner.pets:
    st.write("Current pets:")
    st.table(pet_rows(owner))
else:
    st.info("No pets yet. Add one to start building the care plan.")

st.divider()

st.subheader("Add a Task")
if owner.pets:
    with st.form("add_task_form", clear_on_submit=True):
        selected_pet_name = st.selectbox("Assign to pet", [pet.name for pet in owner.pets])
        task_description = st.text_input("Task description", value="Morning walk")
        due_date = st.date_input("Due date", value=date.today())
        task_time = st.time_input("Scheduled time", value=time(7, 0))
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        pet = owner.get_pet(selected_pet_name)
        cleaned_task_description = task_description.strip()
        if not cleaned_task_description:
            st.error("Please enter a task description before adding a task.")
        elif pet is None:
            st.error("That pet could not be found. Please try again.")
        else:
            pet.add_task(
                Task(
                    description=cleaned_task_description,
                    scheduled_time=task_time.strftime("%I:%M %p"),
                    frequency=frequency,
                    due_date=due_date,
                    duration_minutes=int(duration),
                    priority=priority,
                )
            )
            st.session_state.schedule_generated = False
            st.session_state.flash_success = f"Added {cleaned_task_description} for {pet.name}."
            st.rerun()
else:
    st.info("Add a pet first, then you can schedule care tasks.")

st.divider()

st.subheader("Task Review")
if all_tasks:
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        pet_filter = st.selectbox("Filter by pet", ["All pets", *[pet.name for pet in owner.pets]])
    with filter_col2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    with filter_col3:
        scope_filter = st.selectbox("Filter by due date", ["All upcoming", "Due today"])

    filtered_tasks = scheduler.sort_by_time(all_tasks)

    if pet_filter != "All pets":
        filtered_tasks = scheduler.filter_tasks(filtered_tasks, pet_name=pet_filter)
    if status_filter != "All":
        filtered_tasks = scheduler.filter_tasks(
            filtered_tasks,
            completed=status_filter == "Completed",
        )
    if scope_filter == "Due today":
        filtered_tasks = scheduler.filter_tasks(filtered_tasks, due_on=scheduler.plan_date)

    st.success(f"Showing {len(filtered_tasks)} task(s) using the scheduler's sorting and filters.")
    st.table(task_rows(filtered_tasks))
else:
    st.info("No tasks yet. Add a few tasks to review them here.")

st.subheader("Complete a Task")
if today_pending_tasks:
    selected_task_label = st.selectbox(
        "Mark a task as done",
        [task_label(task) for task in today_pending_tasks],
    )
    if st.button("Mark selected task complete"):
        selected_task = next(
            task for task in today_pending_tasks if task_label(task) == selected_task_label
        )
        next_task = scheduler.mark_task_complete(selected_task)
        st.session_state.flash_success = (
            f"Marked '{selected_task.description}' complete for {selected_task.pet_name}."
        )
        if next_task is not None:
            st.session_state.flash_info = (
                "Recurring task created for "
                f"{next_task.due_date.isoformat()} at {next_task.scheduled_time}."
            )
        st.rerun()
else:
    st.info("No pending tasks are due today.")

st.divider()

st.subheader("Build Schedule")
st.caption("The scheduler sorts tasks by time, filters incomplete work, and flags exact-time conflicts.")

if conflict_warnings:
    st.markdown("### Conflict warnings")
    st.warning(
        "Some tasks share the same time slot. A pet owner should reschedule one of them or "
        "mark one complete before relying on the final plan."
    )
    for warning in conflict_warnings:
        st.warning(warning)

if st.button("Generate schedule"):
    st.session_state.schedule_generated = True

if st.session_state.get("schedule_generated"):
    schedule = scheduler.generate_plan()

    if schedule:
        st.success("Today's schedule is ready.")
        st.table(schedule_rows(schedule))
    else:
        st.warning("No tasks could be scheduled with the current data.")

    explanations = scheduler.explain_plan()
    if explanations:
        st.markdown("### Why this plan")
        for explanation in explanations:
            st.write(f"- {explanation}")
