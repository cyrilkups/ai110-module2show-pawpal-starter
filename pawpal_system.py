"""Core domain models for the PawPal+ logic layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    """A single piece of pet care work that can be scheduled."""

    title: str
    category: str
    duration_minutes: int
    priority: str
    preferred_time_of_day: str = "anytime"
    required: bool = True
    completed: bool = False

    def mark_complete(self) -> None:
        """Update the task after it has been finished."""
        pass

    def fits_within(self, available_minutes: int) -> bool:
        """Check whether the task can fit in the remaining schedule."""
        pass

    def describe(self) -> str:
        """Return a short, user-friendly summary of the task."""
        pass


@dataclass
class Pet:
    """A pet profile and the care tasks assigned to that pet."""

    name: str
    species: str
    age_years: int
    care_notes: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        pass

    def remove_task(self, task_title: str) -> None:
        """Remove a task from this pet by title."""
        pass

    def get_required_tasks(self) -> list[Task]:
        """Return tasks that must be completed today."""
        pass


@dataclass
class Owner:
    """The person managing pets and the time available for care."""

    name: str
    available_minutes_per_day: int
    preferences: dict[str, str] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care list."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        pass

    def update_preferences(self, preferences: dict[str, str]) -> None:
        """Store or update owner preferences used by the planner."""
        pass


@dataclass
class DailyPlanner:
    """Scheduling engine that turns pet care tasks into a daily plan."""

    owner: Owner
    plan_date: date = field(default_factory=date.today)
    planned_tasks: list[Task] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)

    def collect_tasks(self) -> list[Task]:
        """Gather tasks from the owner's pets."""
        pass

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks according to priority and constraints."""
        pass

    def generate_plan(self) -> list[Task]:
        """Build the final schedule for the day."""
        pass

    def explain_plan(self) -> list[str]:
        """Explain why tasks were selected and ordered."""
        pass
