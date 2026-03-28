import asyncio
import json
from datetime import datetime
from pathlib import Path

import websockets

OUT = Path("/tmp/task4")
OUT.mkdir(parents=True, exist_ok=True)
LOG_PATH = OUT / "chat_failure_session.txt"

PROMPTS = [
    ("trigger_list", "List the labs"),
    ("what_wrong", "What went wrong?"),
    (
        "create_health",
        "Create a health check for this chat that runs every 2 minutes using your cron tool. "
        "Each run should check for LMS/backend errors in the last 2 minutes, inspect a trace if needed, "
        "and post a short summary here. If there are no recent errors, say the system looks healthy.",
    ),
    ("list_jobs", "List scheduled jobs."),
    ("trigger_fresh", "What labs are available?"),
]


async def recv_one(ws: websockets.WebSocketClientProtocol, timeout: int = 180) -> str:
    return await asyncio.wait_for(ws.recv(), timeout=timeout)


async def main() -> None:
    uri = "ws://127.0.0.1:42002/ws/chat?access_key=lab8-chat-pass"
    records: list[dict[str, str]] = []

    async with websockets.connect(uri, open_timeout=40, ping_interval=20) as ws:
        for tag, prompt in PROMPTS:
            await ws.send(json.dumps({"content": prompt}))
            msg = await recv_one(ws, timeout=180)
            now = datetime.utcnow().isoformat() + "Z"
            records.append({"ts": now, "type": "prompt", "tag": tag, "text": prompt})
            records.append({"ts": now, "type": "response", "tag": tag, "text": msg})

        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 210:
            try:
                msg = await recv_one(ws, timeout=20)
            except asyncio.TimeoutError:
                continue
            now = datetime.utcnow().isoformat() + "Z"
            records.append(
                {
                    "ts": now,
                    "type": "proactive",
                    "tag": "cron_report",
                    "text": msg,
                }
            )
            break

        remove_prompt = "Remove the short-interval test health-check job you just created."
        await ws.send(json.dumps({"content": remove_prompt}))
        msg = await recv_one(ws, timeout=120)
        now = datetime.utcnow().isoformat() + "Z"
        records.append(
            {"ts": now, "type": "prompt", "tag": "remove_job", "text": remove_prompt}
        )
        records.append({"ts": now, "type": "response", "tag": "remove_job", "text": msg})

    lines: list[str] = []
    for rec in records:
        lines.append(f"[{rec['ts']}] {rec['type']}::{rec['tag']}")
        lines.append(rec["text"])
        lines.append("")

    LOG_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE {LOG_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
