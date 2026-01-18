"""Delivery services for digests."""

from __future__ import annotations

from dataclasses import dataclass

from rss_digest.models import Delivery, GroupDestination
from rss_digest.repository import DeliveriesRepo


@dataclass
class DeliveryResult:
    deliveries: list[Delivery]


class DeliveryService:
    def __init__(self, deliveries: DeliveriesRepo) -> None:
        self._deliveries = deliveries

    def deliver(self, digest_id, destinations: list[GroupDestination]) -> DeliveryResult:
        deliveries: list[Delivery] = []
        for destination in destinations:
            delivery = Delivery(
                digest_id=digest_id,
                destination_id=destination.id,
                status="sent",
            )
            self._deliveries.add(delivery)
            deliveries.append(delivery)
        return DeliveryResult(deliveries=deliveries)
