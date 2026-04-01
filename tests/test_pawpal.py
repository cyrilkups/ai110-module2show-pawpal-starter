"""Quick checks for the PawPal+ logic layer."""

from __future__ import annotations

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def build_owner_with_pets() -> Owner:
    """Create an owner with two pets for scheduler tests."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog", age_years=4))
    owner.add_pet(Pet(name="Pixel", species="cat", age_years=2))
    return owner


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


def test_sort_by_time_orders_same_priority_tasks_chronologically() -> None:
    """Ensure tasks with the same priority are sorted by time."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None

    mochi.add_task(
        Task(description="Evening walk", scheduled_time="06:00 PM", frequency="daily", due_date=today)
    )
    mochi.add_task(
        Task(description="Breakfast", scheduled_time="08:00 AM", frequency="daily", due_date=today)
    )
    mochi.add_task(
        Task(description="Morning walk", scheduled_time="07:00 AM", frequency="daily", due_date=today)
    )

    scheduler = Scheduler(owner)
    sorted_descriptions = [task.description for task in scheduler.sort_by_time()]

    assert sorted_descriptions == ["Morning walk", "Breakfast", "Evening walk"]


def test_sort_by_time_prioritizes_priority_before_clock_time() -> None:
    """Ensure higher-priority tasks come before lower-priority ones."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None

    mochi.add_task(
        Task(
            description="Low priority cleanup",
            scheduled_time="07:00 AM",
            frequency="daily",
            due_date=today,
            priority="low",
        )
    )
    mochi.add_task(
        Task(
            description="High priority meds",
            scheduled_time="08:30 AM",
            frequency="daily",
            due_date=today,
            priority="high",
        )
    )

    scheduler = Scheduler(owner)
    sorted_descriptions = [task.description for task in scheduler.sort_by_time()]

    assert sorted_descriptions == ["High priority meds", "Low priority cleanup"]


def test_filter_tasks_can_limit_by_pet_and_status() -> None:
    """Ensure filtering can target one pet's pending tasks."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    pixel = owner.get_pet("Pixel")
    assert mochi is not None
    assert pixel is not None

    done_task = Task(description="Breakfast", scheduled_time="08:00 AM", frequency="daily", due_date=today)
    done_task.mark_complete()
    mochi.add_task(done_task)
    mochi.add_task(Task(description="Morning walk", scheduled_time="07:00 AM", frequency="daily", due_date=today))
    pixel.add_task(Task(description="Litter box cleanup", scheduled_time="09:00 AM", frequency="daily", due_date=today))

    scheduler = Scheduler(owner)
    filtered_tasks = scheduler.filter_tasks(completed=False, pet_name="Mochi")

    assert [task.description for task in filtered_tasks] == ["Morning walk"]


def test_mark_task_complete_creates_next_daily_occurrence() -> None:
    """Ensure daily tasks create a new occurrence on the next day."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None

    task = Task(description="Breakfast", scheduled_time="08:00 AM", frequency="daily", due_date=today)
    mochi.add_task(task)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_task_complete(task)

    assert task.completed is True
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert len(mochi.tasks) == 2


def test_mark_task_complete_creates_next_weekly_occurrence() -> None:
    """Ensure weekly tasks create a new occurrence seven days later."""
    today = date.today()
    owner = build_owner_with_pets()
    pixel = owner.get_pet("Pixel")
    assert pixel is not None

    task = Task(description="Weekly grooming", scheduled_time="05:00 PM", frequency="weekly", due_date=today)
    pixel.add_task(task)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=7)


def test_detect_conflicts_returns_warning_for_exact_time_match() -> None:
    """Ensure exact time matches produce a conflict warning."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    pixel = owner.get_pet("Pixel")
    assert mochi is not None
    assert pixel is not None

    mochi.add_task(Task(description="Morning walk", scheduled_time="07:00 AM", frequency="daily", due_date=today))
    pixel.add_task(Task(description="Morning medication", scheduled_time="07:00 AM", frequency="daily", due_date=today))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "07:00 AM" in warnings[0]


def test_next_available_slot_returns_open_gap_after_busy_tasks() -> None:
    """Ensure the scheduler can suggest the next open care slot."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None

    mochi.add_task(
        Task(
            description="Breakfast",
            scheduled_time="07:00 AM",
            frequency="daily",
            due_date=today,
            duration_minutes=30,
            priority="high",
        )
    )
    mochi.add_task(
        Task(
            description="Morning walk",
            scheduled_time="08:00 AM",
            frequency="daily",
            due_date=today,
            duration_minutes=30,
            priority="medium",
        )
    )

    scheduler = Scheduler(owner)

    assert scheduler.next_available_slot(30) == "06:00 AM"
    assert scheduler.next_available_slot(45, day_start="07:00 AM") == "08:30 AM"


def test_owner_can_save_and_load_json(tmp_path) -> None:
    """Ensure owners, pets, and tasks persist through JSON storage."""
    today = date.today()
    owner = build_owner_with_pets()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(
        Task(description="Breakfast", scheduled_time="08:00 AM", frequency="daily", due_date=today)
    )

    path = tmp_path / "pawpal-data.json"
    owner.save_to_json(path)
    loaded_owner = Owner.load_from_json(path)

    assert loaded_owner.name == owner.name
    assert loaded_owner.available_minutes_per_day == owner.available_minutes_per_day
    assert loaded_owner.get_pet("Mochi") is not None
    loaded_tasks = loaded_owner.get_all_tasks()
    assert len(loaded_tasks) == 1
    assert loaded_tasks[0].description == "Breakfast"


def test_generate_plan_returns_empty_list_when_no_tasks_exist() -> None:
    """Ensure the scheduler handles pets with no tasks gracefully."""
    owner = build_owner_with_pets()

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()

    assert schedule == []
    assert scheduler.warnings == []
