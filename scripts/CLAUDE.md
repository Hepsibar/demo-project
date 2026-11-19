# CLAUDE.md (scripts)

이 폴더의 개발 보조 스크립트가 **어떻게 동작하고, 새 스크립트를 추가할 때 어떤 패턴을 따라야 하는지**를 다룹니다. 실행 명령 요약은 루트의 [`../CLAUDE.md`](../CLAUDE.md)에 있습니다.

구성:

| 파일 | 역할 |
|------|------|
| `dev.ps1` | Windows PowerShell용 개발 서버 헬퍼 |
| `dev.sh` | Git Bash / WSL / Linux용 동일 헬퍼 |
| `smoke.py` | `/analyze` 2-섹션 응답 계약 검증 (E2E 스모크) |
| `check_paths.py` | 추적 중인 `*.md`의 참조 경로 존재 검증 (문서 drift 가드) |
| `hooks/pre-push` | 위 검증을 push 전에 자동 실행하는 git 훅 |

## dev.ps1 · dev.sh

두 스크립트는 **동일한 동작의 플랫폼 쌍**입니다. 한쪽을 고치면 다른 쪽도 맞춰야 합니다.

- 액션: `start` | `stop` | `status` | `restart` | `logs`. 인자를 생략하면 `start`.
- 포트 기본값 8000. PowerShell은 `-Port <n>`, bash는 `PORT=<n>` 환경 변수로 변경합니다.
- `start`는 `python -m uvicorn main:app`을 **백그라운드로** 띄우고, PID를 `scripts/.dev.pid`에 기록한 뒤, `http://127.0.0.1:<port>/`에 최대 10초(0.5초 × 20회) 헬스체크를 돕니다. 타임아웃 시 경고만 출력하고 프로세스는 남겨둡니다.
- stdout/stderr는 각각 `scripts/.dev.log` · `scripts/.dev.err.log`로 리다이렉트되며, `logs`는 각 파일의 마지막 40줄을 보여줍니다.
- `stop`/`status`는 PID 파일의 프로세스가 실제로 살아 있는지 확인하고 동작합니다. 죽은 PID 파일은 없는 것으로 간주합니다.

런타임 산출물(`.dev.pid` · `.dev.log` · `.dev.err.log`)은 `.gitignore`에 등록되어 커밋되지 않습니다.

## smoke.py

서버가 떠 있는 상태에서 `fixtures/sample_kakao.csv`를 `/analyze`에 멀티파트로 POST하고, 응답 HTML을 다음 기준으로 검사합니다.

- HTTP 200
- `대화 요약` 헤딩 포함
- `액션 아이템` 헤딩 포함
- 인라인 오류 블록(`class="error"`) 없음

대상 URL은 `SMOKE_URL` 환경 변수로 바꿀 수 있습니다(기본 `http://127.0.0.1:8000/analyze`). 종료 코드: `0` 성공, `1` 계약 체크 실패, `2` 픽스처 없음, `3` 서버 도달 불가. 실제 Claude 호출이 일어나므로 `ANTHROPIC_API_KEY`가 필요합니다.

검사 항목은 `api/CLAUDE.md`의 **시스템 프롬프트 계약**(2섹션: `## 대화 요약`, `## 액션 아이템`)과 짝을 이룹니다. 섹션 구조를 바꾸면 이 체크도 함께 갱신하세요.

## check_paths.py · hooks/pre-push

`check_paths.py`는 추적 중인 모든 `*.md`를 훑어, 마크다운 링크 타깃과 inline-code 토큰 중 **파일 경로처럼 보이는 것**(슬래시 포함 또는 알려진 확장자)이 실제로 존재하는지 확인합니다.

- 각 참조는 **문서 자신의 디렉터리 기준**과 **레포 루트 기준** 두 곳 모두에서 찾아보고, 한쪽이라도 존재하면 통과합니다(그래서 `api/CLAUDE.md`가 루트의 `main.py`를 언급해도 OK).
- gitignore된 경로(`.env`, `scripts/.dev.*`)는 "존재하지 않아도 정상"으로 보고 통과시킵니다.
- 코드 펜스(```` ``` ````) 안의 ASCII 트리·다이어그램, 라우트 문자열(`/analyze`), 사용법 문자열(`{start|stop}`)은 경로로 보지 않습니다.
- 종료 코드: `0` 모두 해결, `1` dangling 참조 있음, `2` git 레포 아님.

`hooks/pre-push`가 이를 push 전에 실행합니다. clone마다 한 번 `git config core.hooksPath scripts/hooks`로 활성화합니다(`.git/hooks`는 추적되지 않으므로). stale 참조를 추가하는 문서 변경은 push 단계에서 차단됩니다.

## 새 스크립트를 추가할 때

위 파일들이 확립한 관례를 따릅니다.

- **경로 기준은 스크립트 위치**: 루트는 스크립트 디렉터리의 부모로 계산합니다(`Split-Path $PSScriptRoot -Parent` / `cd "$(dirname "$0")/.."`). CWD에 의존하지 않습니다.
- **PowerShell과 bash를 쌍으로 제공**: 개발용 헬퍼는 `.ps1`과 `.sh`를 함께 두어 동작을 일치시킵니다.
- **런타임 산출물은 `scripts/` 아래에 `.`으로 시작**하게 두고 `.gitignore`에 추가합니다.
- **파이썬 스크립트는 표준 라이브러리만** 사용합니다(`smoke.py`는 `urllib`만 씀). 새 서드파티 의존성은 `requirements.txt`에 추가하기 전에 필요성을 먼저 확인합니다.
