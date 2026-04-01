"""Core domain models for the PawPal+ logic layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


def _time_sort_key(time_text: str) -> tuple[int, int]:
    """Convert a time string into a sortable hour and minute pair."""
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            parsed_time = datetime.strptime(time_text, fmt)
            return parsed_time.hour, parsed_time.minute
        except ValueError:
            continue
    return 23, 59


@dataclass
class Task:
    """Represent a single pet care activity."""

    description: str
    scheduled_time: str
    frequency: str
    duration_minutes: int = 30
    priority: str = "medium"
    completed: bool = False
    pet_name: str | None = None

    @property
    def title(self) -> str:
        """Expose the task description as a title-like label."""
        return self.description

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def fits_within(self, available_minutes: int) -> bool:
        """Return whether the task fits inside the remaining minutes."""
        return self.duration_minutes <= available_minutes

    def describe(self) -> str:
        """Return a short human-readable summary of the task."""
        pet_label = self.pet_name or "Unassigned pet"
        status = "done" if self.completed else "pending"
        return (
            f"{self.scheduled_time} - {pet_label}: {self.description} "
            f"({self.frequency}, {self.priority} priority, {status})"
        )


@dataclass
class Pet:
    """Store pet details and the care tasks assigned to that pet."""

    name: str
    species: str
    age_years: int
    care_notes: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_description: str) -> None:
        """Remove the first task with a matching description."""
        for index, task in enumerate(self.tasks):
            if task.description.lower() == task_description.lower():
                del self.tasks[index]
                return
        raise ValueError(f"No task named '{task_description}' found for {self.name}.")

    def get_required_tasks(self) -> list[Task]:
        """Return the tasks that still need attention today."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    """Manage pets and provide access to their tasks."""

    name: str
    available_minutes_per_day: int
    preferences: dict[str, str] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        if any(existing_pet.name.lower() == pet.name.lower() for existing_pet in self.pets):
            raise ValueError(f"A pet named '{pet.name}' already exists for {self.name}.")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        for index, pet in enumerate(self.pets):
            if pet.name.lower() == pet_name.lower():
                del self.pets[index]
                return
        raise ValueError(f"No pet named '{pet_name}' found for {self.name}.")

    def update_preferences(self, preferences: dict[str, str]) -> None:
        """Merge new preference values into the owner's settings."""
        self.preferences.update(preferences)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across every pet."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            for task in pet.tasks:
                task.pet_name = pet.name
                all_tasks.append(task)
        return all_tasks


@dataclass
class Scheduler:
    """Retrieve, organize, and manage tasks across an owner's pets."""

    owner: Owner
    plan_date: date = field(default_factory=date.today)
    planned_tasks: list[Task] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)

    def collect_tasks(self) -> list[Task]:
        """Pull every task from the owner's pets."""
        return self.owner.get_all_tasks()

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by completion, time, and priority."""
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            tasks,
            key=lambda task: (
                task.completed,
                _time_sort_key(task.scheduled_time),
                priority_rank.get(task.priority.lower(), 3),
                task.description.lower(),
            ),
        )

    def generate_plan(self) -> list[Task]:
        """Build a schedule that fits inside the owner's available time."""
        remaining_minutes = self.owner.available_minutes_per_day
        self.planned_tasks = []
        self.explanations = []

        for task in self.prioritize_tasks(self.collect_tasks()):
            if task.completed:
                self.explanations.append(f"Skipped {task.description} because it is already complete.")
                continue
            if task.fits_within(remaining_minutes):
                self.planned_tasks.append(task)
                remaining_minutes -= task.duration_minutes
                self.explanations.append(
                    f"Scheduled {task.description} for {task.pet_name} at {task.scheduled_time}."
                )
            else:
                self.explanations.append(
                    f"Skipped {task.description} because only {remaining_minutes} minutes were left."
                )

        return self.planned_tasks

    def explain_plan(self) -> list[str]:
        """Return short explanations for the current plan."""
        if not self.explanations:
            self.generate_plan()
        return self.explanations


DailyPlanner = Scheduler
