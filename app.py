from __future__ import annotations

from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


def get_owner() -> Owner:
    """Create the session owner once and reuse it on later reruns."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(
            name="Jordan",
            available_minutes_per_day=90,
            preferences={"walk_preference": "morning"},
        )
    return st.session_state.owner


def find_pet(owner: Owner, pet_name: str) -> Pet | None:
    """Return the pet with the matching name, if it exists."""
    return owner.get_pet(pet_name)


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


def task_rows(owner: Owner) -> list[dict[str, int | str]]:
    """Build table rows for every task across all pets."""
    return [
        {
            "Pet": task.pet_name or "Unknown",
            "Task": task.description,
            "Due Date": task.due_date.isoformat(),
            "Time": task.scheduled_time,
            "Frequency": task.frequency,
            "Duration": task.duration_minutes,
            "Priority": task.priority,
            "Completed": "Yes" if task.completed else "No",
        }
        for task in owner.get_all_tasks()
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
            "Priority": task.priority,
        }
        for task in schedule
    ]


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

owner = get_owner()

st.title("🐾 PawPal+")
st.markdown(
    """
PawPal+ helps a busy pet owner keep pet care organized.
Add pets, assign tasks, and generate a simple schedule for today.
"""
)

with st.expander("How session memory works", expanded=False):
    st.markdown(
        """
This app stores the `Owner` object in `st.session_state`, which works like a dictionary.
The app checks whether `"owner"` already exists before creating a new one, so pets and tasks
stay available across Streamlit reruns during the session.
"""
    )

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
        st.success(f"Added {cleaned_pet_name} to {owner.name}'s household.")
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
        task_time = st.time_input("Scheduled time", value=time(7, 0))
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        pet = find_pet(owner, selected_pet_name)
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
                    duration_minutes=int(duration),
                    priority=priority,
                )
            )
            st.session_state.schedule_generated = False
            st.success(f"Added {cleaned_task_description} for {pet.name}.")
else:
    st.info("Add a pet first, then you can schedule care tasks.")

if owner.get_all_tasks():
    st.write("Current tasks:")
    st.table(task_rows(owner))
else:
    st.info("No tasks yet. Add a few tasks to build today's schedule.")

st.divider()

st.subheader("Build Schedule")
st.caption("The scheduler reads all pet tasks from the owner and fits them into today's time.")

if st.button("Generate schedule"):
    st.session_state.schedule_generated = True

if st.session_state.get("schedule_generated"):
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    if schedule:
        st.write("Today's schedule:")
        st.table(schedule_rows(schedule))
    else:
        st.warning("No tasks could be scheduled with the current data.")

    explanations = scheduler.explain_plan()
    if scheduler.warnings:
        st.markdown("### Conflict warnings")
        for warning in scheduler.warnings:
            st.warning(warning)

    if explanations:
        st.markdown("### Why this plan")
        for explanation in explanations:
            st.write(f"- {explanation}")
