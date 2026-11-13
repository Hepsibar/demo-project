# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 실행 방법

의존성을 설치하고 개발 서버를 실행합니다. `.env`에 `ANTHROPIC_API_KEY`가 있어야 하며, `python-dotenv`가 자동으로 로드합니다.

```powershell
pip install -r requirements.txt
uvicorn main:app --reload
```

Python 3.9+ 필요 (`list[dict]` 내장 제네릭 사용). 버전 핀 파일은 없습니다.

이후 http://127.0.0.1:8000 에 접속해 카카오톡 CSV를 업로드합니다.

### 개발 서버 헬퍼 (선택)

백그라운드 기동·상태 확인·로그 조회용 스크립트가 있습니다.

```powershell
scripts/dev.ps1 start      # 백그라운드로 기동 후 헬스체크 (기본 8000 포트)
scripts/dev.ps1 status     # 실행 여부 확인
scripts/dev.ps1 logs       # stdout/stderr 마지막 40줄
scripts/dev.ps1 stop       # 중지
```
Git Bash/WSL/Linux에서는 `scripts/dev.sh {start|stop|status|restart|logs}`.

### 스모크 테스트

서버가 떠 있는 상태에서 `fixtures/sample_kakao.csv`를 `/analyze`에 POST 하여
두 섹션(`대화 요약`·`액션 아이템`) 응답 계약을 검증합니다 (`ANTHROPIC_API_KEY` 필요).

```powershell
python scripts/smoke.py    # SMOKE_URL 환경변수로 대상 URL 변경 가능
```

린터·빌드 단계는 설정되어 있지 않습니다.

## 하위 가이드

- 전체 아키텍처(구성 요소, 레이어 구분, 요청 흐름)는 [`architecture.md`](architecture.md)를 참고하세요.
- API/라우트/Claude 호출 세부 사항(CSV 포맷, `MAX_MESSAGES = 500`, 시스템 프롬프트 계약, 오류·거부 처리, 응답 렌더링의 신뢰 가정)은 [`api/CLAUDE.md`](api/CLAUDE.md)에 정리되어 있습니다.
