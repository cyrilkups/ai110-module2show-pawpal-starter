"""Terminal demo for the PawPal+ logic layer."""

from __future__ import annotations

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_owner() -> Owner:
    """Create a sample owner with pets and intentionally unsorted tasks."""
    today = date.today()
    owner = Owner(
        name="Jordan",
        available_minutes_per_day=120,
        preferences={"walk_preference": "morning"},
    )

    mochi = Pet(name="Mochi", species="dog", age_years=4)
    pixel = Pet(name="Pixel", species="cat", age_years=2)

    mochi.add_task(
        Task(
            description="Evening medication",
            scheduled_time="06:00 PM",
            frequency="daily",
            due_date=today,
            duration_minutes=10,
            priority="high",
        )
    )
    mochi.add_task(
        Task(
            description="Morning walk",
            scheduled_time="07:00 AM",
            frequency="daily",
            due_date=today,
            duration_minutes=30,
            priority="medium",
        )
    )
    mochi.add_task(
        Task(
            description="Breakfast",
            scheduled_time="08:00 AM",
            frequency="daily",
            due_date=today,
            duration_minutes=10,
            priority="high",
        )
    )

    pixel.add_task(
        Task(
            description="Morning medication",
            scheduled_time="07:00 AM",
            frequency="daily",
            due_date=today,
            duration_minutes=5,
            priority="high",
        )
    )
    pixel.add_task(
        Task(
            description="Litter box cleanup",
            scheduled_time="09:30 AM",
            frequency="daily",
            due_date=today,
            duration_minutes=10,
            priority="low",
        )
    )
    pixel.add_task(
        Task(
            description="Weekly grooming",
            scheduled_time="05:00 PM",
            frequency="weekly",
            due_date=today,
            duration_minutes=20,
            priority="medium",
        )
    )

    owner.add_pet(mochi)
    owner.add_pet(pixel)
    return owner


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a readable task table in the terminal."""
    print(title)
    print("-" * 126)
    print(
        f"{'Date':<12}{'Time':<10}{'Pet':<12}{'Task':<28}"
        f"{'Type':<12}{'Priority':<14}{'Status':<14}"
    )
    print("-" * 126)

    for task in tasks:
        task_name = f"{task.task_icon} {task.description}"
        print(
            f"{task.due_date.isoformat():<12}"
            f"{task.scheduled_time:<10}"
            f"{(task.pet_name or 'Unknown'):<12}"
            f"{task_name:<28}"
            f"{task.frequency.title():<12}"
            f"{task.priority_badge:<14}"
            f"{task.status_badge:<14}"
        )
    print()


def print_warnings(warnings: list[str]) -> None:
    """Print conflict warnings in a compact list."""
    print("Conflict Warnings")
    print("-" * 126)
    if not warnings:
        print("No conflicts detected.\n")
        return

    for warning in warnings:
        print(f"⚠️  {warning}")
    print()


def main() -> None:
    """Run the PawPal+ terminal demo."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)

    print_tasks("Tasks Entered Out of Order", owner.get_all_tasks())

    sorted_tasks = scheduler.sort_by_time()
    print_tasks("Priority-First Schedule View", sorted_tasks)

    mochi_pending = scheduler.filter_tasks(completed=False, pet_name="Mochi")
    print_tasks("Pending Tasks for Mochi", scheduler.sort_by_time(mochi_pending))

    breakfast = next(task for task in owner.get_all_tasks() if task.description == "Breakfast")
    next_breakfast = scheduler.mark_task_complete(breakfast)
    print("Recurring Task Demo")
    print("-" * 126)
    if next_breakfast is None:
        print("No new recurring task was created.\n")
    else:
        print(
            "✅ Completed Breakfast and created the next occurrence for "
            f"{next_breakfast.due_date.isoformat()} at {next_breakfast.scheduled_time}.\n"
        )

    next_slot = scheduler.next_available_slot(30)
    print("Next Available Slot")
    print("-" * 126)
    if next_slot is None:
        print("No 30-minute slot is available today.\n")
    else:
        print(f"⏰ Next open 30-minute care slot: {next_slot}\n")

    schedule = scheduler.generate_plan()
    print_tasks("Today's Schedule", schedule)
    print_warnings(scheduler.warnings)


if __name__ == "__main__":
    main()
