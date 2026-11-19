# evals

대표 task의 **2섹션 응답 계약 pass-rate**를 주기적으로 측정하는 디렉터리입니다.
`scripts/smoke.py`가 "1회 통과/실패"를 보는 반면, 여기서는 **여러 번 돌려 안정성(pass-rate)**을
숫자로 추적해, 프롬프트/모델 변경이 계약 준수율에 주는 영향을 catch합니다.

## 실행

서버가 떠 있는 상태에서:

```bash
python evals/run_evals.py                 # 기본 5회
EVAL_RUNS=10 python evals/run_evals.py    # 반복 횟수 변경
EVAL_MIN=0.8 python evals/run_evals.py    # 통과 임계 pass-rate 변경
EVAL_URL=http://host/analyze python evals/run_evals.py
```
```powershell
python evals/run_evals.py
$env:EVAL_RUNS="10"; python evals/run_evals.py
```

입력은 `fixtures/sample_kakao.csv`, 측정 대상은 `/analyze`입니다.

## 계약 체크

매 실행이 다음을 모두 만족해야 1건 통과로 셉니다(= `scripts/smoke.py`와 동일한 계약,
`api/CLAUDE.md`의 "시스템 프롬프트 계약"과 짝).

- HTTP 200
- `대화 요약` 헤딩 포함
- `액션 아이템` 헤딩 포함
- 인라인 오류 블록(`class="error"`) 없음

## 종료 코드 · 산출물

- `0` pass-rate ≥ `EVAL_MIN`, `1` 미달, `2` 픽스처 없음, `3` 서버 도달 불가.
- 실행마다 `evals/results/latest.json`에 요약(pass-rate·실행별 상세)을 기록합니다.
  이 출력 디렉터리는 런타임 산출물이라 `.gitignore`에 등록되어 커밋되지 않습니다.

## 주의

매 실행이 **실제 Claude 호출**이므로 `EVAL_RUNS`만큼 API 비용이 발생합니다
(`ANTHROPIC_API_KEY` 필요). CI 자동 실행 대신 수동/주기 실행을 전제로 합니다.
