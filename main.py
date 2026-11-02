import csv
import io
import os
from pathlib import Path

import anthropic
import markdown as md
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

MAX_MESSAGES = 500
MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """당신은 카카오톡 그룹방/오픈톡의 **방장**을 돕는 어시스턴트입니다.
입력으로 받은 채팅 로그를 분석해 아래 두 섹션으로만 한국어로 답하세요.
불필요한 서론·결론·사족 금지. 반드시 아래 마크다운 형식을 그대로 따르세요.

## 대화 요약
- 주요 주제/논점을 3~5개의 bullet로 간결하게.

## 액션 아이템
방장이 처리하면 좋을 일을 번호 리스트로 1~7개. 각 항목은 다음 형식:
1. **(카테고리)** 구체적인 할 일 — 이유를 짧게.

카테고리 예시: 공지, FAQ 정리, 중재, 핀 고정, 환영, 규칙 정비, 자료 공유 등.
방장 입장에서 즉시 실행 가능한 수준으로 구체적으로 쓰세요."""

app = FastAPI()
client = anthropic.Anthropic()


def parse_kakao_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    messages = []
    for row in reader:
        if row.get("type") != "message":
            continue
        msg = (row.get("message") or "").strip()
        if not msg:
            continue
        messages.append({
            "date": row.get("date") or "",
            "time": row.get("time") or "",
            "nickname": row.get("nickname") or "",
            "message": msg,
        })
    return messages


def format_for_llm(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        ts = f"{m['date']} {m['time']}".strip()
        lines.append(f"[{ts}] {m['nickname']}: {m['message']}")
    return "\n".join(lines)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, file: UploadFile = File(...)):
    raw = await file.read()
    all_messages = parse_kakao_csv(raw)
    total = len(all_messages)

    if total == 0:
        return templates.TemplateResponse(request, "index.html", {
            "error": "분석할 메시지가 없습니다. CSV의 type 컬럼에 'message' 행이 있는지 확인하세요.",
        })

    used = all_messages[-MAX_MESSAGES:]
    truncated = total > MAX_MESSAGES
    chat_text = format_for_llm(used)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": chat_text}],
            thinking={"type": "adaptive"},
        )
    except anthropic.APIStatusError as e:
        return templates.TemplateResponse(request, "index.html", {
            "error": f"Claude API 오류 (HTTP {e.status_code}): {e.message}",
        })

    if response.stop_reason == "refusal":
        return templates.TemplateResponse(request, "index.html", {
            "error": "모델이 응답을 거부했습니다. 입력 내용을 확인하세요.",
        })

    text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    result_md = "\n".join(text_parts).strip()
    result_html = md.markdown(result_md)

    return templates.TemplateResponse(request, "index.html", {
        "result_html": result_html,
        "filename": file.filename,
        "total_messages": total,
        "used_messages": len(used),
        "truncated": truncated,
    })
