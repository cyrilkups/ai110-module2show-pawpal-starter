"""Quick checks for the PawPal+ logic layer."""

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status() -> None:
    """Ensure marking a task complete updates its status."""
    task = Task(description="Morning walk", scheduled_time="07:00 AM", frequency="daily")

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count() -> None:
    """Ensure adding a task to a pet grows the task list."""
    pet = Pet(name="Mochi", species="dog", age_years=4)
    task = Task(description="Breakfast", scheduled_time="08:00 AM", frequency="daily")

    pet.add_task(task)

    assert len(pet.tasks) == 1
