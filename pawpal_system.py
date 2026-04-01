"""Core domain models for the PawPal+ logic layer."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path


def _time_sort_key(time_text: str) -> tuple[int, int]:
    """Convert a time string into a sortable hour and minute pair."""
    for fmt in ("%H:%M", "%I:%M %p"):
        try:
            parsed_time = datetime.strptime(time_text, fmt)
            return parsed_time.hour, parsed_time.minute
        except ValueError:
            continue
    return 23, 59


def _time_to_minutes(time_text: str) -> int:
    """Convert a time string into minutes from midnight."""
    hours, minutes = _time_sort_key(time_text)
    return hours * 60 + minutes


def _minutes_to_time_text(total_minutes: int) -> str:
    """Convert minutes from midnight into a 12-hour time string."""
    total_minutes = max(0, total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    day_hours = hours % 24
    suffix = "AM" if day_hours < 12 else "PM"
    display_hour = day_hours % 12 or 12
    return f"{display_hour:02d}:{minutes:02d} {suffix}"


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

    @property
    def priority_rank(self) -> int:
        """Return a numeric priority rank for sorting."""
        rank_map = {"high": 0, "medium": 1, "low": 2}
        return rank_map.get(self.priority.lower(), 3)

    @property
    def priority_badge(self) -> str:
        """Return a compact priority label for UI display."""
        badge_map = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
        return badge_map.get(self.priority.lower(), self.priority.title())

    @property
    def task_icon(self) -> str:
        """Return an emoji that matches the task description."""
        description = self.description.lower()
        if "walk" in description:
            return "🦮"
        if "medication" in description or "meds" in description:
            return "💊"
        if "breakfast" in description or "feeding" in description or "dinner" in description:
            return "🍽"
        if "groom" in description or "bath" in description:
            return "🧼"
        if "litter" in description or "cleanup" in description:
            return "🧹"
        if "play" in description or "enrichment" in description:
            return "🎾"
        return "🐾"

    @property
    def status_badge(self) -> str:
        """Return a compact completion label for UI display."""
        return "✅ Done" if self.completed else "⏳ Pending"

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

    def to_dict(self) -> dict[str, object]:
        """Convert the task into a JSON-serializable dictionary."""
        return {
            "description": self.description,
            "scheduled_time": self.scheduled_time,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "completed": self.completed,
            "pet_name": self.pet_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Task:
        """Create a task from a dictionary."""
        return cls(
            description=str(data["description"]),
            scheduled_time=str(data["scheduled_time"]),
            frequency=str(data["frequency"]),
            due_date=date.fromisoformat(str(data.get("due_date", date.today().isoformat()))),
            duration_minutes=int(data.get("duration_minutes", 30)),
            priority=str(data.get("priority", "medium")),
            completed=bool(data.get("completed", False)),
            pet_name=str(data["pet_name"]) if data.get("pet_name") is not None else None,
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

    def to_dict(self) -> dict[str, object]:
        """Convert the pet into a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "age_years": self.age_years,
            "care_notes": list(self.care_notes),
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Pet:
        """Create a pet from a dictionary."""
        tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        return cls(
            name=str(data["name"]),
            species=str(data["species"]),
            age_years=int(data["age_years"]),
            care_notes=[str(note) for note in data.get("care_notes", [])],
            tasks=tasks,
        )


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

    def to_dict(self) -> dict[str, object]:
        """Convert the owner and all nested data into a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "available_minutes_per_day": self.available_minutes_per_day,
            "preferences": dict(self.preferences),
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Owner:
        """Create an owner from a dictionary."""
        owner = cls(
            name=str(data.get("name", "Jordan")),
            available_minutes_per_day=int(data.get("available_minutes_per_day", 90)),
            preferences={str(key): str(value) for key, value in data.get("preferences", {}).items()},
        )
        owner.pets = [Pet.from_dict(pet_data) for pet_data in data.get("pets", [])]
        return owner

    def save_to_json(self, path: str | Path) -> None:
        """Persist the owner, pets, and tasks to disk as JSON."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, path: str | Path) -> Owner:
        """Load an owner from disk, returning a default owner if the file is missing."""
        target_path = Path(path)
        if not target_path.exists():
            return cls(
                name="Jordan",
                available_minutes_per_day=90,
                preferences={"walk_preference": "morning"},
            )
        return cls.from_dict(json.loads(target_path.read_text(encoding="utf-8")))


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
        """Return tasks sorted by priority first, then date and time."""
        tasks_to_sort = self.collect_tasks() if tasks is None else tasks
        return sorted(
            tasks_to_sort,
            key=lambda task: (
                task.priority_rank,
                task.due_date,
                _time_sort_key(task.scheduled_time),
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

    def next_available_slot(
        self,
        duration_minutes: int,
        tasks: list[Task] | None = None,
        day_start: str = "06:00 AM",
        day_end: str = "10:00 PM",
    ) -> str | None:
        """Find the next open time slot that can fit the requested duration."""
        if duration_minutes <= 0:
            return None

        target_tasks = self.filter_tasks(tasks, completed=False, due_on=self.plan_date)
        busy_periods: list[tuple[int, int]] = []
        chronological_tasks = sorted(
            target_tasks,
            key=lambda task: (
                task.due_date,
                _time_sort_key(task.scheduled_time),
                task.description.lower(),
            ),
        )
        for task in chronological_tasks:
            start_minutes = _time_to_minutes(task.scheduled_time)
            end_minutes = start_minutes + task.duration_minutes
            busy_periods.append((start_minutes, end_minutes))

        current_start = _time_to_minutes(day_start)
        day_end_minutes = _time_to_minutes(day_end)

        for start_minutes, end_minutes in busy_periods:
            if current_start + duration_minutes <= start_minutes:
                return _minutes_to_time_text(current_start)
            current_start = max(current_start, end_minutes)

        if current_start + duration_minutes <= day_end_minutes:
            return _minutes_to_time_text(current_start)
        return None

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
                next_slot = self.next_available_slot(task.duration_minutes, due_tasks)
                slot_text = f" Next open slot: {next_slot}." if next_slot else ""
                self.explanations.append(
                    f"Skipped {task.description} because only {remaining_minutes} minutes were left."
                    f"{slot_text}"
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
