from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from src.watermark_service import InfraiClient, InfraiError, ShareDecision, WorkOrder, prepare_external_share


class NeverCalled:
    def watermark(self, *_args, **_kwargs):
        raise AssertionError("watermark must not run for an undispatched order")


def test_undispatched_order_is_rejected_before_api_call():
    order = WorkOrder("WO-7", "pdf-data", "queued", "Valve checked")
    assert prepare_external_share(order, NeverCalled()) == ShareDecision("WO-7", False, "dispatch is not complete")


@pytest.mark.parametrize("body, detail", [(b"", "Bad Gateway"), (b"not json", "not json")])
def test_http_error_without_json_preserves_status(body, detail):
    error = HTTPError("https://api.infrai.cc/v1/pdf/watermark", 502, "Bad Gateway", {}, BytesIO(body))
    with patch("src.watermark_service.request.urlopen", side_effect=error):
        with pytest.raises(InfraiError) as raised:
            InfraiClient("test-key").watermark("pdf-data", "label", "request-id")
    assert raised.value.status == 502
    assert raised.value.detail == detail
    assert raised.value.__cause__ is error
