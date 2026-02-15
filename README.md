# 🛡️ API Cost Guardian

**OpenClaw용 실시간 API 비용 모니터링 시스템**

Claude API, OpenAI API 등 유료 API 사용량을 실시간으로 추적하고, 일일 예산 초과 위험을 사전에 경고합니다.

---

## ⚡ **빠른 시작**

### 1️⃣ **즉시 체크** (수동 실행)
OpenClaw 메인 세션에서:
```
API 비용 체크해줘
```

### 2️⃣ **자동 모니터링** (크론 설정)
이미 설정되어 있습니다! 매일 4회 (8시, 12시, 18시, 23시) 자동 체크.

---

## 📊 **기능**

### ✅ **실시간 비용 추적**
- 모든 API 호출 비용 합산
- 제공자별/모델별 분류
- 일일 예산 대비 사용률

### ✅ **예측 알림**
- 현재 사용 패턴 기반 일일 비용 예측
- 3단계 알림 ($3 / $5 / $7)
- 텔레그램 즉시 알림

### ✅ **자동 분석**
- 비용 높은 크론/세션 식별
- 비용 절감 제안 자동 생성
- 예상 절감 효과 계산

### 🆕 **주간/월간 리포트**
- 과거 7일 또는 30일 비용 추세 분석
- 평균, 최대, 최소, 중간값 계산
- 비용 추세 감지 (상승/하락/안정)
- ASCII 차트로 시각화

```bash
# 주간 리포트
python3 ~/.openclaw/skills/api-cost-guardian/scripts/weekly_report.py

# 월간 리포트
python3 ~/.openclaw/skills/api-cost-guardian/scripts/weekly_report.py --period monthly
```

### 🆕 **데이터 Export**
- CSV 또는 JSON 형식으로 비용 데이터 추출
- 외부 분석 도구 연동 가능
- 감사(audit) 및 보고서 생성

```bash
# CSV export (최근 7일)
python3 ~/.openclaw/skills/api-cost-guardian/scripts/export_cost_data.py --format csv

# JSON export (최근 30일)
python3 ~/.openclaw/skills/api-cost-guardian/scripts/export_cost_data.py --format json --days 30

# 요약만 출력
python3 ~/.openclaw/skills/api-cost-guardian/scripts/export_cost_data.py --summary
```

### 🆕 **모델 비교 분석**
- 모델별 비용/사용량 비교
- ASCII 차트로 시각화
- 비용 효율성 분석 ($/call, $/1K tokens)
- 절감 기회 자동 식별

```bash
# 최근 7일 모델 비교
python3 ~/.openclaw/skills/api-cost-guardian/scripts/model_comparison.py

# 최근 30일 모델 비교
python3 ~/.openclaw/skills/api-cost-guardian/scripts/model_comparison.py --days 30
```

---

## 🔧 **설정**

### **임계치 변경**
`~/.openclaw/skills/api-cost-guardian/config.json`:
```json
{
  "thresholds": {
    "warning": 3.0,
    "urgent": 5.0,
    "critical": 7.0
  },
  "cost_tracking": {
    "daily_budget": 10.0
  }
}
```

### **모니터링 주기 변경**
크론 작업 수정:
```bash
openclaw cron list  # ID 확인
openclaw cron update <ID> '{"schedule": {"kind": "cron", "expr": "0 */6 * * *", "tz": "Asia/Seoul"}}'
```

---

## 📖 **문서**

- [SKILL.md](./SKILL.md) - 전체 가이드
- [config.json](./config.json) - 설정 파일

---

## 💡 **비용 절감 팁**

1. **무료 모델 활용**
   - Ollama (GLM, Llama 등) - 완전 무료
   - 간단한 작업은 무료 모델로

2. **크론 최적화**
   - 회고/체크인: Sonnet 또는 GLM
   - Opus는 복잡한 작업에만
   - 불필요한 크론 비활성화

3. **캐시 활용**
   - Isolated 대신 메인 세션 (캐시 재사용)
   - 반복 작업 최적화

4. **모델 비교 활용**
   - 정기적으로 모델 비교 리포트 확인
   - 비싼 모델 → 저렴한 모델 전환 검토
   - $/1K tokens 메트릭으로 효율성 파악

---

## 🎯 **예시**

### **정상 상태**
```
✅ 오늘 비용: $2.45 (예상: $4.90)
```

### **주의 알림**
```
⚠️ API 비용 주의!
현재: $3.20 → 예상: $5.12

주요 원인:
1. 크론 회고 (6개) - $2.10
2. 메인 세션 - $0.80

절감 제안:
• 회고 크론 → GLM (-$1.50/일)
```

### **주간 리포트 예시**
```
============================================================
📊 Weekly Cost Report
============================================================

📅 Period: 7 days
💰 Total Cost: $28.45
📊 Average Daily: $4.06
📈 Max Daily: $6.20
📉 Min Daily: $2.10
🎯 Median Daily: $3.95

📈 Trend: RISING

💵 Period Budget: $70.00
📊 Budget Used: 40.6%

🔍 Cost by Provider:
  • anthropic: $27.80 (97.7%)
  • ollama: $0.00 (0.0%)

🤖 Cost by Model:
  • claude-sonnet-4-5: $18.20 (64.0%)
  • claude-opus-4-6: $9.60 (33.7%)

📈 Daily Cost Chart:

02-09 $  2.10 |█████████████████
02-10 $  3.45 |████████████████████████████
02-11 $  4.20 |█████████████████████████████████
02-12 $  6.20 |██████████████████████████████████████████████████
02-13 $  3.95 |████████████████████████████████
02-14 $  4.80 |██████████████████████████████████████
02-15 $  3.75 |██████████████████████████████

💡 Insights:
  ⚠️ Costs are RISING - consider optimization!
  ⚠️ Budget usage >70% - monitor closely
```

### **모델 비교 예시**
```
======================================================================
🤖 Model Comparison Report (7 days)
======================================================================

📊 Total Models: 3
💰 Total Cost: $28.45
📞 Total Calls: 245

💰 Cost by Model:

claude-sonnet-4-5              $  18.20 |██████████████████████████████████████████████████
claude-opus-4-6                $   9.60 |██████████████████████████
ollama/glm                     $   0.65 |█

📊 Usage by Model (Call Count):

claude-sonnet-4-5               180 calls |██████████████████████████████████████████████████
ollama/glm                       50 calls |█████████████
claude-opus-4-6                  15 calls |████

📋 Detailed Stats:

Model                               Cost   Calls     $/Call   $/1K tok
----------------------------------------------------------------------
claude-sonnet-4-5              $   18.20     180  $  0.1011  $  0.0023
claude-opus-4-6                $    9.60      15  $  0.6400  $  0.0095
ollama/glm                     $    0.65      50  $  0.0130  $  0.0001

💡 Cost Optimization Insights:

  📈 Most expensive: claude-sonnet-4-5 ($18.20)
  📉 Cheapest: ollama/glm ($0.0001/1K tokens)
  
  💰 Potential savings if claude-sonnet-4-5 → ollama/glm:
     Current: $18.20
     Potential: $0.79
     Savings: $17.41 (95.7%)
  
  ⚠️ High cost per call models:
     • claude-opus-4-6: $0.6400/call
     • claude-sonnet-4-5: $0.1011/call
```

---

## 🚀 **새로운 기능 (v1.1.0)**

### 1. **주간/월간 리포트**
- 과거 데이터 분석으로 비용 추세 파악
- 예산 초과 조기 경고
- ASCII 차트로 시각적 표현

### 2. **CSV/JSON Export**
- 외부 스프레드시트 분석
- 감사 보고서 생성
- BI 도구 연동

### 3. **모델 비교 분석**
- 모델별 비용 효율성 비교
- 절감 기회 자동 식별
- 데이터 기반 모델 선택

---

**버전:** 1.1.0  
**만든 사람:** Paulina 🌸  
**날짜:** 2026-02-15  
**업데이트:** 주간/월간 리포트, 데이터 export, 모델 비교 기능 추가
