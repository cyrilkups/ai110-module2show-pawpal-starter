"""Core domain models for the PawPal+ logic layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


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
    due_date: date = field(default_factory=date.today)
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

    def is_due_for(self, target_date: date) -> bool:
        """Return whether the task should be considered by the target date."""
        return self.due_date <= target_date

    def next_due_date(self) -> date | None:
        """Return the next due date for a recurring task."""
        frequency_steps = {"daily": 1, "weekly": 7}
        days_until_next = frequency_steps.get(self.frequency.lower())
        if days_until_next is None:
            return None
        return self.due_date + timedelta(days=days_until_next)

    def spawn_next_occurrence(self) -> Task | None:
        """Create the next recurring copy of this task when needed."""
        next_due = self.next_due_date()
        if next_due is None:
            return None
        return Task(
            description=self.description,
            scheduled_time=self.scheduled_time,
            frequency=self.frequency,
            due_date=next_due,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
        )

    def describe(self) -> str:
        """Return a short human-readable summary of the task."""
        pet_label = self.pet_name or "Unassigned pet"
        status = "done" if self.completed else "pending"
        return (
            f"{self.due_date.isoformat()} {self.scheduled_time} - {pet_label}: "
            f"{self.description} ({self.frequency}, {self.priority} priority, {status})"
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

    def get_required_tasks(self, target_date: date | None = None) -> list[Task]:
        """Return incomplete tasks, optionally limited to a planning date."""
        if target_date is None:
            return [task for task in self.tasks if not task.completed]
        return [task for task in self.tasks if not task.completed and task.is_due_for(target_date)]


@dataclass
class Owner:
    """Manage pets and provide access to their tasks."""

    name: str
    available_minutes_per_day: int
    preferences: dict[str, str] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        if self.get_pet(pet.name) is not None:
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

    def get_pet(self, pet_name: str) -> Pet | None:
        """Return the matching pet by name if it exists."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

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
    warnings: list[str] = field(default_factory=list)

    def collect_tasks(self) -> list[Task]:
        """Pull every task from the owner's pets."""
        return self.owner.get_all_tasks()

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by due date, time, and then priority."""
        tasks_to_sort = self.collect_tasks() if tasks is None else tasks
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            tasks_to_sort,
            key=lambda task: (
                task.due_date,
                _time_sort_key(task.scheduled_time),
                priority_rank.get(task.priority.lower(), 3),
                task.description.lower(),
            ),
        )

    def filter_tasks(
        self,
        tasks: list[Task] | None = None,
        completed: bool | None = None,
        pet_name: str | None = None,
        due_on: date | None = None,
    ) -> list[Task]:
        """Filter tasks by completion status, pet name, and optional due date."""
        filtered_tasks = self.collect_tasks() if tasks is None else tasks

        if completed is not None:
            filtered_tasks = [task for task in filtered_tasks if task.completed is completed]
        if pet_name:
            filtered_tasks = [
                task
                for task in filtered_tasks
                if (task.pet_name or "").lower() == pet_name.lower()
            ]
        if due_on is not None:
            filtered_tasks = [task for task in filtered_tasks if task.is_due_for(due_on)]

        return filtered_tasks

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Prepare due and incomplete tasks in chronological order."""
        due_tasks = self.filter_tasks(tasks, completed=False, due_on=self.plan_date)
        return self.sort_by_time(due_tasks)

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return lightweight warnings for tasks that share the same exact time."""
        tasks_to_check = self.collect_tasks() if tasks is None else tasks
        due_tasks = self.filter_tasks(tasks_to_check, completed=False, due_on=self.plan_date)

        conflicts: dict[tuple[date, str], list[Task]] = {}
        for task in due_tasks:
            conflicts.setdefault((task.due_date, task.scheduled_time), []).append(task)

        warnings: list[str] = []
        for (due_date, scheduled_time), grouped_tasks in sorted(conflicts.items()):
            if len(grouped_tasks) < 2:
                continue
            task_summaries = ", ".join(
                f"{task.pet_name}: {task.description}" for task in self.sort_by_time(grouped_tasks)
            )
            warnings.append(
                f"Conflict warning for {due_date.isoformat()} at {scheduled_time}: {task_summaries}"
            )

        self.warnings = warnings
        return warnings

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task and queue its next recurring copy when applicable."""
        if task.completed:
            return None

        task.mark_complete()
        next_task = task.spawn_next_occurrence()
        if next_task is None or task.pet_name is None:
            return next_task

        pet = self.owner.get_pet(task.pet_name)
        if pet is None:
            return next_task

        if not self._has_matching_task(pet, next_task):
            pet.add_task(next_task)
        return next_task

    def generate_plan(self) -> list[Task]:
        """Build a schedule that fits inside the owner's available time."""
        remaining_minutes = self.owner.available_minutes_per_day
        self.planned_tasks = []
        self.explanations = []

        due_tasks = self.prioritize_tasks(self.collect_tasks())
        self.warnings = self.detect_conflicts(due_tasks)

        for task in due_tasks:
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

    def _has_matching_task(self, pet: Pet, candidate: Task) -> bool:
        """Return whether a pet already has an equivalent future task."""
        return any(
            existing_task.description == candidate.description
            and existing_task.scheduled_time == candidate.scheduled_time
            and existing_task.frequency == candidate.frequency
            and existing_task.due_date == candidate.due_date
            and existing_task.completed == candidate.completed
            for existing_task in pet.tasks
        )


DailyPlanner = Scheduler
