# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 실행 방법

의존성을 설치하고 개발 서버를 실행합니다.

```powershell
# Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --reload        # http://127.0.0.1:8000
```
```bash
# Git Bash / WSL / Linux
pip install -r requirements.txt
uvicorn main:app --reload        # http://127.0.0.1:8000
```

**Why:** `.env`의 `ANTHROPIC_API_KEY`는 서버 기동 *전에* 있어야 합니다 — `anthropic.Anthropic()` 클라이언트가 모듈 import 시점에 생성되므로, 키가 없으면 기동 자체가 실패합니다. `python-dotenv`가 import 시 `.env`를 자동 로드합니다.

**Note:** Python 3.9+ 필요(`list[dict]` 내장 제네릭 사용). 버전 핀 파일·린터·빌드 단계는 없습니다. 기동 후 http://127.0.0.1:8000 에서 카카오톡 CSV를 업로드합니다.

### 개발 서버 헬퍼 (선택)

백그라운드 기동·상태 확인·로그 조회용 스크립트가 있습니다.

```powershell
scripts/dev.ps1 start            # 백그라운드 기동 후 헬스체크 (기본 8000 포트)
scripts/dev.ps1 status           # 실행 여부 확인
scripts/dev.ps1 logs             # stdout/stderr 마지막 40줄
scripts/dev.ps1 stop             # 중지
scripts/dev.ps1 start -Port 9000 # Note: 포트 변경
```
```bash
# Git Bash / WSL / Linux (동작 동일)
scripts/dev.sh start             # start|stop|status|restart|logs
PORT=9000 scripts/dev.sh start   # Note: 포트 변경은 PORT 환경변수
```

### 스모크 테스트

서버가 떠 있는 상태에서 `fixtures/sample_kakao.csv`를 `/analyze`에 POST 하여
두 섹션(`대화 요약`·`액션 아이템`) 응답 계약을 검증합니다.

```powershell
python scripts/smoke.py          # 종료코드 0=성공 1=계약실패 2=픽스처없음 3=서버불가
$env:SMOKE_URL="http://host/analyze"; python scripts/smoke.py   # Note: 대상 URL 변경
```
```bash
python scripts/smoke.py
SMOKE_URL=http://host/analyze python scripts/smoke.py           # Note: 대상 URL 변경
```

**Note:** 서버가 떠 있어야 하며, **실제 Claude 호출이 발생**하므로 `ANTHROPIC_API_KEY`가 필요합니다(API 비용 발생). 계약 세부는 [`api/CLAUDE.md`](api/CLAUDE.md) 참고.

### 문서 경로 검증 훅 (선택)

`scripts/check_paths.py`는 추적 중인 `*.md`가 참조하는 파일 경로가 실제로 존재하는지 검사해, stale/hallucinated 참조가 머지되는 것을 막습니다. pre-push 훅으로 한 번만 활성화합니다.

```bash
git config core.hooksPath scripts/hooks   # clone마다 1회
python scripts/check_paths.py             # 수동 실행도 가능
```

**Note:** 훅을 건너뛰려면 `git push --no-verify`. gitignore된 런타임 산출물(`.env`, `scripts/.dev.*`)은 없어도 통과합니다.

## 하위 가이드

- 전체 아키텍처(구성 요소, 레이어 구분, 요청 흐름)는 [`architecture.md`](architecture.md)를 참고하세요.
- API/라우트/Claude 호출 세부 사항(CSV 포맷, `MAX_MESSAGES = 500`, 시스템 프롬프트 계약, 오류·거부 처리, 응답 렌더링의 신뢰 가정)은 [`api/CLAUDE.md`](api/CLAUDE.md)에 정리되어 있습니다.
