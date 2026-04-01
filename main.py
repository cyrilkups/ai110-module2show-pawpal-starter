"""Terminal demo for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_owner() -> Owner:
    """Create a sample owner with pets and tasks."""
    owner = Owner(
        name="Jordan",
        available_minutes_per_day=90,
        preferences={"walk_preference": "morning"},
    )

    mochi = Pet(name="Mochi", species="dog", age_years=4)
    pixel = Pet(name="Pixel", species="cat", age_years=2)

    mochi.add_task(
        Task(
            description="Morning walk",
            scheduled_time="07:00 AM",
            frequency="daily",
            duration_minutes=30,
            priority="high",
        )
    )
    mochi.add_task(
        Task(
            description="Breakfast",
            scheduled_time="08:00 AM",
            frequency="daily",
            duration_minutes=10,
            priority="high",
        )
    )
    pixel.add_task(
        Task(
            description="Evening play session",
            scheduled_time="06:00 PM",
            frequency="daily",
            duration_minutes=20,
            priority="medium",
        )
    )

    owner.add_pet(mochi)
    owner.add_pet(pixel)
    return owner


def print_schedule(schedule: list[Task]) -> None:
    """Print the schedule in a clean terminal table."""
    print("Today's Schedule")
    print("-" * 72)
    print(f"{'Time':<10}{'Pet':<12}{'Task':<24}{'Freq':<12}{'Status':<10}")
    print("-" * 72)

    for task in schedule:
        status = "Done" if task.completed else "Pending"
        print(
            f"{task.scheduled_time:<10}"
            f"{(task.pet_name or 'Unknown'):<12}"
            f"{task.description:<24}"
            f"{task.frequency:<12}"
            f"{status:<10}"
        )


def main() -> None:
    """Run the PawPal+ terminal demo."""
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_plan()
    print_schedule(schedule)


if __name__ == "__main__":
    main()
