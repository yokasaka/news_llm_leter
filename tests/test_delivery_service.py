from rss_digest.models import GroupDestination
from rss_digest.repository import DeliveriesRepo
from rss_digest.services.digest.delivery import DeliveryService, EmailSender, SlackSender


class FailingEmailSender(EmailSender):
    def send(self, destination: GroupDestination, markdown: str) -> None:
        raise RuntimeError("smtp down")


class FailingSlackSender(SlackSender):
    def send(self, destination: GroupDestination, markdown: str) -> None:
        raise RuntimeError("slack down")


def test_delivery_records_failures():
    deliveries = DeliveriesRepo()
    service = DeliveryService(deliveries, FailingEmailSender(), FailingSlackSender())
    email_dest = GroupDestination(type="email", destination="user@example.com")
    slack_dest = GroupDestination(type="slack", destination="https://hooks.slack.test")

    result = service.deliver("digest-id", [email_dest, slack_dest], markdown="body")

    assert len(result.deliveries) == 2
    statuses = {delivery.status for delivery in result.deliveries}
    assert statuses == {"failed"}
