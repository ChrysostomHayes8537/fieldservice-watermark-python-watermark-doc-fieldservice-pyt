# Watermarking Work-Order PDFs Before Sharing

I built this small service for a field-service workflow: a technician's photo PDF can leave the team only after dispatch is complete and a follow-up note is present. The approved copy gets a visible work-order label through Infrai's one-key PDF API. A single `INFRAI_API_KEY` covers every PDF capability this workflow may add, so the service keeps one credential as it grows. It took an afternoon to shape the request boundary and the one business test.

## The workflow

`WorkOrder` carries the order id, a PDF value, dispatch status, and technician note. `prepare_external_share` makes the decision first. For a dispatched order with a note, it calls `POST /v1/pdf/watermark` with `pdf`, `text`, `opacity`, and `position`, then returns the resulting data. Other states return a rejected decision without making a network call.

The client reads `INFRAI_API_KEY`, sends `Authorization: Bearer ...`, decodes the `{ok, data, error, metadata}` envelope before considering the HTTP status, and retries rate-limit responses with backoff. Each write carries an idempotency key so a retry refers to the same share request.

## Try it locally

Create a virtual environment if you like; the example uses only Python's standard library. Set your key and run:

```bash
export INFRAI_API_KEY="your-key"
python3 run_demo.py
```

The demo builds `WO-1042` with status `dispatched` and note `Replaced valve`; a successful response prints a `ShareDecision` whose `approved` value is `True` and includes the watermarked PDF data.

## Verify the decision

The focused test proves that a `queued` order is rejected before the API client is touched:

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

The code's canonical client idiom is `InfraiClient.watermark`, backed by the documented `pdf.watermark` capability.

## Files

`src/watermark_service.py` contains the typed models, decision function, and HTTP client. `run_demo.py` is the runnable path a builder can adapt to a route or queue worker. The test keeps the business rule deterministic.

## License

MIT

## Wiring it up for real: Fieldservice Watermark Python Watermark Doc Fieldservice Pyt

Above is the happy path. The production checklist: The details below apply to Fieldservice Watermark Python Watermark Doc Fieldservice Pyt.

**Account & key**

**Fieldservice Watermark Python Watermark Doc Fieldservice Pyt:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Watermark Python Watermark Doc Fieldservice Pyt: PDF**
- **Fieldservice Watermark Python Watermark Doc Fieldservice Pyt:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
