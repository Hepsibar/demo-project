# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 실행 방법

의존성을 설치하고 개발 서버를 실행합니다. `.env`에 `ANTHROPIC_API_KEY`가 있어야 하며, `python-dotenv`가 자동으로 로드합니다.

```powershell
pip install -r requirements.txt
uvicorn main:app --reload
```

이후 http://127.0.0.1:8000 에 접속해 카카오톡 CSV를 업로드합니다.

테스트 스위트, 린터, 빌드 단계는 설정되어 있지 않습니다.

## 하위 가이드

- 전체 아키텍처(구성 요소, 레이어 구분, 요청 흐름)는 [`architecture.md`](architecture.md)를 참고하세요.
- API/라우트/Claude 호출 세부 사항(CSV 포맷, `MAX_MESSAGES = 500`, 시스템 프롬프트 계약, 오류·거부 처리, 응답 렌더링의 신뢰 가정)은 [`api/CLAUDE.md`](api/CLAUDE.md)에 정리되어 있습니다.
