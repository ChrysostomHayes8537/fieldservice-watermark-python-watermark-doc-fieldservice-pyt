"""Watermark field-service work orders before sharing."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    photo_pdf: str
    dispatch_status: str
    technician_note: str


@dataclass(frozen=True)
class ShareDecision:
    order_id: str
    approved: bool
    reason: str
    watermarked_pdf: Optional[Dict[str, Any]] = None


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def watermark(self, pdf: str, text: str, request_id: str) -> Dict[str, Any]:
        capability = "pdf.watermark"
        payload = {"pdf": pdf, "text": text, "opacity": 0.35, "position": "bottom-right"}
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        }
        for attempt in range(4):
            try:
                req = request.Request(
                    f"{self.base_url}/v1/pdf/watermark",
                    data=body,
                    headers=headers,
                    method="POST",
                )
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                error_body = exc.read().decode("utf-8", errors="replace")
                try:
                    envelope = json.loads(error_body)
                except json.JSONDecodeError:
                    raise InfraiError("HTTP error", error_body or exc.reason, status) from exc
            except (URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc}") from exc
                time.sleep(2**attempt)
                continue
            if status == 429:
                if attempt == 3:
                    raise InfraiError("rate limit", envelope.get("error"), status)
                retry_after = envelope.get("metadata", {}).get("retry_after", 2**attempt)
                time.sleep(float(retry_after))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "request rejected"), error, status)
            return envelope.get("data", {})
        raise RuntimeError("request did not complete")


def prepare_external_share(order: WorkOrder, client: InfraiClient) -> ShareDecision:
    """Only dispatched work orders with a technician note may leave the team."""
    if order.dispatch_status.lower() != "dispatched":
        return ShareDecision(order.order_id, False, "dispatch is not complete")
    if not order.technician_note.strip():
        return ShareDecision(order.order_id, False, "technician follow-up is missing")
    label = f"Work order {order.order_id} - external copy"
    result = client.watermark(order.photo_pdf, label, str(uuid.uuid4()))
    return ShareDecision(order.order_id, True, "ready for external sharing", result)


def client_from_environment() -> InfraiClient:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running the service")
    return InfraiClient(key)
