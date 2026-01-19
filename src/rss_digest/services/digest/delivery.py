"""Delivery services for digests."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import smtplib
from typing import Mapping

import httpx

from rss_digest.models import Delivery, GroupDestination
from rss_digest.repository import DeliveriesRepo


@dataclass
class DeliveryResult:
    deliveries: list[Delivery]


class EmailSender:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1025,
        username: str | None = None,
        password: str | None = None,
        from_address: str = "rss-digest@example.com",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_address = from_address

    def send(self, destination: GroupDestination, markdown: str) -> None:
        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = destination.destination
        message["Subject"] = "RSS Digest"
        message.set_content(markdown or "")
        with smtplib.SMTP(self._host, self._port) as server:
            if self._username and self._password:
                server.starttls()
                server.login(self._username, self._password)
            server.send_message(message)


class SlackSender:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=10)

    def send(self, destination: GroupDestination, markdown: str) -> None:
        url = destination.destination
        headers: Mapping[str, str] | None = None
        if destination.token_enc:
            headers = {"Authorization": f"Bearer {destination.token_enc}"}
        response = self._client.post(url, json={"text": markdown or ""}, headers=headers)
        response.raise_for_status()


class DeliveryService:
    def __init__(
        self,
        deliveries: DeliveriesRepo,
        email_sender: EmailSender | None = None,
        slack_sender: SlackSender | None = None,
    ) -> None:
        self._deliveries = deliveries
        self._email_sender = email_sender or EmailSender()
        self._slack_sender = slack_sender or SlackSender()

    def deliver(
        self,
        digest_id,
        destinations: list[GroupDestination],
        markdown: str | None = None,
    ) -> DeliveryResult:
        deliveries: list[Delivery] = []
        for destination in destinations:
            status = "sent"
            error_message = None
            try:
                if destination.type == "email":
                    self._email_sender.send(destination, markdown or "")
                elif destination.type == "slack":
                    self._slack_sender.send(destination, markdown or "")
                else:
                    raise ValueError("Unknown destination type")
            except Exception as exc:  # noqa: BLE001
                status = "failed"
                error_message = str(exc)
            delivery = Delivery(
                digest_id=digest_id,
                destination_id=destination.id,
                status=status,
                error_message=error_message,
            )
            self._deliveries.add(delivery)
            deliveries.append(delivery)
        return DeliveryResult(deliveries=deliveries)
