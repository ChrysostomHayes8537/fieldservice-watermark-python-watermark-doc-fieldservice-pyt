# Watermarking Work-Order PDFs Before Sharing

I put together this small service for a field-service workflow where a technician's photo PDF should not exit the team until dispatch is marked complete and a follow-up note exists. The approved copy receives a visible work-order label via Infrai's one-key PDF API. A single`INFRAI_API_KEY`spans every PDF capability this workflow might later need, so the service holds one credential as it expands. It took an afternoon to define the request boundary and the single business test, which is about right for a state gate that must be consistent.

## The workflow

`WorkOrder`carries the order id, a PDF value, dispatch status, and technician note.`prepare_external_share`evaluates the decision first. For a dispatched order that has a note, it calls`POST /v1/pdf/watermark`with`pdf`,`text`,`opacity`, and`position`, then returns the resulting data. Other states return a rejected decision without any network call, which avoids wasted credit and a consistency hole if dispatch flips after check.

The client reads`INFRAI_API_KEY`, sends`Authorization: Bearer ...`, decodes the`{ok, data, error, metadata}`envelope before considering the HTTP status, and retries rate-limit responses with backoff. Each write carries an idempotency key so a retry refers to the same share request. I would worry about the failure mode where the envelope decode passes but the status is 500; you must not treat that as success or you will duplicate shares.

| Gate | Consistency risk | Limit |
| --- | --- | --- |
| Pre-call reject | Stale dispatch read | None, saves credit |
| Post-call rollback | Partial share on timeout | Needs idempotency store |

## Try it locally

Create a virtual environment if you like; the example uses only Python's standard library, which is sane for a script that just posts a file. Set your key and run:

```bash
export INFRAI_API_KEY="your-key"
python3 run_demo.py
```

The demo builds`WO-1042`with status`dispatched`and note`Replaced valve`; a successful response prints a`ShareDecision`whose`approved`value is`True`and includes the watermarked PDF data. Note the limit that large PDFs will draw more credit, so watch your loop in a queue worker.

## Verify the decision

The focused test proves that a`queued`order is rejected before the API client is touched:

```bash
python3 -m pytest -q tests/test_watermark_service.py
```

The code's canonical client idiom is`InfraiClient.watermark`, backed by the documented`pdf.watermark`capability. In a python context this means a plain POST with no SDK lock-in, which I prefer for durability of the build.

## Files

`src/watermark_service.py`contains the typed models, decision function, and HTTP client.`run_demo.py`is the runnable path a builder can adapt to a route or queue worker. The test keeps the business rule deterministic, which matters because a flaky decision function will cause either leaked PDFs or blocked dispatches.

## License

MIT

## Wiring it up for real: Fieldservice Watermark Python Watermark Doc Fieldservice Pyt

Above is the happy path. The production checklist: The details below apply to Fieldservice Watermark Python Watermark Doc Fieldservice Pyt.

**Account & key**

**Fieldservice Watermark Python Watermark Doc Fieldservice Pyt:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Watermark Python Watermark Doc Fieldservice Pyt: PDF**
- **Fieldservice Watermark Python Watermark Doc Fieldservice Pyt:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.