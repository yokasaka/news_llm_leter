from datetime import datetime, timezone

from rss_digest.models import Group, GroupSchedule, User
from rss_digest.repository import Repositories
from rss_digest.services.scheduler.service import SchedulerService


def test_scheduler_ticks_due_schedule_and_prevents_double_fire():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    group = Group(user_id=user.id, name="Daily")
    schedule = GroupSchedule(group_id=group.id, time_hhmm="08:30")
    repos.users.add(user)
    repos.groups.add(group)
    repos.schedules.add(schedule)

    service = SchedulerService(repos.schedules, repos.groups, repos.users)
    now = datetime(2024, 1, 1, 8, 30, tzinfo=timezone.utc)
    due = service.tick(now)

    assert len(due) == 1
    assert due[0].group.id == group.id

    due_again = service.tick(now)
    assert due_again == []
