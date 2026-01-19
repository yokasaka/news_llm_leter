from pathlib import Path

from rss_digest.models import FeedItem, FeedSource, Group, GroupDestination, User
from rss_digest.repository import Repositories


def test_sqlite_persists_groups_and_destinations(tmp_path: Path):
    db_path = tmp_path / "rss.db"
    repos = Repositories.build_sqlite(db_path)
    user = User(email="user@example.com", timezone="UTC")
    group = Group(user_id=user.id, name="Daily")
    destination = GroupDestination(group_id=group.id, destination="user@example.com")
    repos.users.add(user)
    repos.groups.add(group)
    repos.destinations.add(destination)

    repos = Repositories.build_sqlite(db_path)
    assert len(repos.users.list_all()) == 1
    assert len(repos.groups.list_all()) == 1
    assert len(repos.destinations.list_all()) == 1


def test_sqlite_feed_item_unique_per_feed(tmp_path: Path):
    db_path = tmp_path / "rss.db"
    repos = Repositories.build_sqlite(db_path)
    feed_source = FeedSource(url="https://example.com/rss")
    repos.feed_sources.add(feed_source)
    item = FeedItem(feed_source_id=feed_source.id, guid_hash="guid", url="https://a")
    repos.feed_items.add(item)
    repos.feed_items.add(item)

    items = repos.feed_items.list_by_feed(feed_source.id)
    assert len(items) == 1
