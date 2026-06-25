# 🚨 공식 인시던트 진단 리포트 (Incident Diagnosis Report)

---

> **문서 번호:** INC-20250715-001
> **작성 시각:** 2025-07-15T10:25:00Z
> **작성자:** SM Incident Commander
> **배포 대상:** 경영진 / 운영팀 / 개발팀

---

## 1. 📋 인시던트 개요 (Incident Summary)

| 항목 | 내용 |
|------|------|
| **인시던트 명** | payment-gateway 서비스 복합 장애 |
| **장애 감지 시각** | 2025-07-15T09:58:12Z (최초 에러 발생) |
| **공식 선언 시각** | 2025-07-15T10:23:45Z |
| **현재 상태** | 🔴 **ACTIVE — 장애 진행 중** |
| **영향 서비스** | `payment-gateway` (결제 처리 서비스) |
| **영향 범위** | 결제 요청의 약 3.8% 실패 중, 향후 15~20분 내 전면 장애 전환 위험 |
| **프론트엔드 상태** | ✅ 정상 (HTTP 200, 응답시간 142ms) |

---

## 2. 🔴 장애 심각도 (Severity Assessment)

### **Severity 1 (SEV-1) — CRITICAL**

> 결제 핵심 서비스의 부분 장애가 진행 중이며, 현재 추세 지속 시 **15~20분 내 전면 서비스 중단(Total Outage)** 으로 확대될 위험이 매우 높습니다.

| 심각도 판단 근거 | 세부 내용 |
|----------------|----------|
| **비즈니스 영향** | 결제 처리 실패율 3.8%, 15분간 500 에러 47건 발생 및 증가 추세 |
| **인프라 위험도** | DB 스토리지 97.5% 소진 (잔여 12.3GB), 커넥션 426/500 (85.2%) 지속 증가 |
| **서비스 가용성** | 전체 8개 Pod 중 3개(37.5%) 비정상 — CrashLoopBackOff 2개, Pending 1개 |
| **장애 확산성** | DB 커넥션 한계 도달 예상 시간 약 15~20분 이내 — 전면 장애 임박 |
| **복구 복잡도** | 단일 원인이 아닌 DB 스토리지 → 커넥션 누수 → OOM → Pod Crash의 **연쇄 복합 장애** |

---

## 3. 🔍 장애 현상 요약 (Incident Symptoms)

### 3-1. 서비스 레이어 이상 징후

- **결제 API 500 에러:** 최근 15분간 **47건** 발생 (임계치 20건의 2.35배 초과), 에러율 **3.8%**, 지속 증가 추세
- **에러 피크:** 2025-07-15T10:15~10:20Z 구간에서 47건/5분 수준으로 폭증
- **총 에러 건수:** 최근 30분간 **134건** (DatabaseConnectionException 89건, OutOfMemoryError 31건, StorageWriteException 14건)

### 3-2. 인프라 레이어 이상 징후

| 컴포넌트 | 이상 현상 | 수치 |
|---------|----------|------|
| **EKS Pod** | CrashLoopBackOff 2개 (재시작 반복 중) | xk2p1: 14회↑, mn3q7: 11회↑ |
| **EKS Pod** | Pending 1개 (스케줄링 불가) | rp5w2: 노드 메모리 부족으로 배치 실패 |
| **EKS 노드** | 메모리 압박 상태 | 3개 노드 중 2개 `MemoryPressure=True` |
| **DB 스토리지** | 임계 수준 포화 | 97.5% 사용, 잔여 12.3GB |
| **DB 커넥션** | 지속 증가 중 | 426/500 (85.2%), 최근 10분간 +28 증가 |
| **DB CPU** | 경고 수준 | 78.4% |

### 3-3. 에러 발생 타임라인

| 시간대 | 에러 건수 | 상태 |
|--------|----------|------|
| 09:58 ~ 10:05 | 8건 | 초기 징후 시작 |
| 10:05 ~ 10:10 | 19건 | 급격한 증가 시작 |
| 10:10 ~ 10:15 | 34건 | 가속화 |
| **10:15 ~ 10:20** | **47건** | 🔴 **피크 — Datadog 경보 발령** |
| 10:20 ~ 10:23 | 26건 | Pod 재시작으로 일시 감소 |

---

## 4. 🧩 근본 원인 분석 (Root Cause Analysis)

### 4-1. 근본 원인 연쇄 구조 (Root Cause Chain)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 [최초 트리거] DB 스토리지 포화 (prod-payment-db: 97.5%, 잔여 12.3GB)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        │
        ▼
[1단계] 감사 로그(Audit Log) 쓰기 실패
        → IOException: No space left on device
        → AuditLogWriter.write() → AuditService.record() → PaymentService.processPayment()
        │
        ▼
[2단계] 트랜잭션 롤백 증가 → DB 커넥션 미반환 (누수 시작)
        → 감사 로그 저장 실패 시 트랜잭션 롤백 처리 과정에서 커넥션 반환 누락
        │
        ▼
[3단계] 커넥션 풀 완전 고갈 (50/50)
        → Timeout waiting for connection from pool (30,000ms)
        → PostgreSQL 서버 레벨 커넥션 한계 도달 임박 (426/500)
        │
        ▼
[4단계] 결제 처리 불가 → 요청 큐 적체
        → 처리 대기 중인 결제 요청이 TransactionCache에 누적
        │
        ▼
[5단계] JVM 힙 메모리 고갈 (98.7%)
        → GC overhead limit exceeded (GC가 CPU 시간의 98% 이상 소비)
        → TransactionCache.put() → PaymentService.cacheTransaction()
        │
        ▼
[6단계] OutOfMemoryError → JVM 강제 종료 → Pod Crash
        → Pod 비정상 종료 시 커넥션 미반환 → 커넥션 누수 반복 심화
        │
        ▼
[7단계] CrashLoopBackOff 루프 진입
        → xk2p1: 14회 재시작, mn3q7: 11회 재시작
        → 재시작 시마다 커넥션 누수 반복
        │
        ▼
[8단계] 노드 메모리 압박 (MemoryPressure=True)
        → CrashLoopBackOff Pod들의 반복 기동이 노드 메모리 소진
        → Pending Pod(rp5w2) 스케줄링 불가 → 가용 Pod 수 회복 불가
        │
        ▼
[9단계] 가용 Pod 5개로 트래픽 집중 → 500 에러 폭증
        → 15분간 47건, 에러율 3.8%, 지속 증가 추세
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4-2. 근본 원인 요약

> **최초 트리거:** `prod-payment-db` 스토리지 포화 (97.5%)
>
> DB 스토리지 포화가 결제 감사 로그 쓰기 실패를 유발하였고, 이것이 트랜잭션 롤백 증가 → DB 커넥션 누수 → 커넥션 풀 고갈 → 요청 큐 적체 → JVM 힙 OOM → Pod CrashLoopBackOff → 노드 메모리 압박 → Pending Pod 스케줄링 실패 → 500 에러 폭증의 **9단계 연쇄 복합 장애**를 유발하였습니다.
>
> 단일 인프라 자원(스토리지) 포화가 애플리케이션 레이어 전체를 마비시킨 전형적인 **Resource Exhaustion Cascade Failure** 패턴입니다.

### 4-3. 에러 유형별 기술 원인

| 에러 유형 | 건수 | 비율 | 기술 원인 | 핵심 코드 위치 |
|-----------|------|------|----------|--------------|
| `DatabaseConnectionException` | 89건 | 66.4% | 커넥션 풀 50/50 고갈, DB 서버 커넥션 한계 도달 | `ConnectionPool.java:142` |
| `OutOfMemoryError` | 31건 | 23.1% | TransactionCache 힙 과점유, GC 오버헤드 한계 초과 | `TransactionCache.java:203` |
| `StorageWriteException` | 14건 | 10.5% | DB 스토리지 포화로 감사 로그 기록 불가 | `AuditLogWriter.java:78` |

---

## 5. ⚡ 즉각적인 Action Item (엔지니어 지시용)

> ⚠️ **긴급 공지:** 현재 DB 커넥션이 426/500으로 지속 증가 중이며, 약 **15~20분 내 전면 장애 전환** 위험이 있습니다. 아래 Action Item을 **즉시 병렬 실행**하십시오.

---

### 🔴 P1 — 즉시 실행 (지금 당장, 15분 이내)

#### [Action 1] DB 스토리지 긴급 확보 — **DBA / 인프라팀**

**목적:** 최초 트리거 제거 및 StorageWriteException 차단

```bash
# 1. 현재 스토리지 사용 현황 확인
df -h /var/lib/postgresql/data

# 2. 불필요 로그 파일 즉시 정리 (WAL 아카이브, 오래된 로그)
find /var/log/postgresql/ -name "*.log" -mtime +7 -delete
find /var/lib/postgresql/data/pg_wal/ -type f -mtime +3 -delete

# 3. 임시 테이블 및 dead tuple 정리
VACUUM FULL ANALYZE;

# 4. (권장) RDS/EBS 스토리지 즉시 확장 — AWS Console 또는 CLI
aws rds modify-db-instance \
  --db-instance-identifier prod-payment-db \
  --allocated-storage 1000 \
  --apply-immediately
```

**성공 기준:** 스토리지 사용률 80% 이하 확보, `StorageWriteException` 발생 중단

---

#### [Action 2] CrashLoopBackOff Pod 강제 재배포 및 JVM 힙 설정 조정 — **DevOps / 개발팀**

**목적:** OOM 원인 제거 및 Pod 정상화

```bash
# 1. 현재 CrashLoopBackOff Pod 로그 수집 (증거 보존)
kubectl logs payment-gateway-7d9f8b-xk2p1 --previous -n payment-gateway > /tmp/crash_xk2p1.log
kubectl logs payment-gateway-7d9f8b-mn3q7 --previous -n payment-gateway > /tmp/crash_mn3q7.log

# 2. 비정상 Pod 강제 삭제 (재스케줄링 유도)
kubectl delete pod payment-gateway-7d9f8b-xk2p1 -n payment-gateway
kubectl delete pod payment-gateway-7d9f8b-mn3q7 -n payment-gateway

# 3. Deployment 환경변수에서 JVM 힙 설정 조정 (현재 설정 확인 후 증설)
kubectl edit deployment payment-gateway -n payment-gateway
# 아래 환경변수 수정:
# - JAVA_OPTS: "-Xms512m -Xmx2g" → "-Xms1g -Xmx3g" (노드 가용 메모리 확인 후 조정)
# - TransactionCache 최대 크기 제한 추가: -Dcache.transaction.maxSize=10000

# 4. Pod 상태 모니터링
kubectl get pods -n payment-gateway -w
```

**성공 기준:** CrashLoopBackOff Pod 0개, 전체 8개 Pod Running 상태 복구

---

#### [Action 3] DB 커넥션 풀 누수 긴급 차단 — **DBA / 개발팀**

**목적:** 커넥션 한계(500) 도달 방지 — 현재 426/500, 약 15~20분 내 한계 도달 예상

```sql
-- 1. 현재 유휴 커넥션 강제 종료 (즉시 실행)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '5 minutes'
  AND datname = 'payment_db';

-- 2. 장시간 대기 중인 커넥션 확인 및 종료
SELECT pid, usename, application_name, state, state_change, query
FROM pg_stat_activity
WHERE state != 'active'
  AND state_change < NOW() - INTERVAL '2 minutes'
ORDER BY state_change ASC;

-- 3. 최대 커넥션 수 임시 증설 (postgresql.conf 또는 RDS 파라미터 그룹)
-- max_connections: 500 → 700 (즉시 적용 후 재시작 필요 시 점검)
```

```bash
# 4. 애플리케이션 커넥션 풀 설정 확인 (application.yml 또는 환경변수)
# HikariCP 기준:
# maximumPoolSize: 50 → 30으로 축소 (Pod당 커넥션 수 감소)
# connectionTimeout: 30000 → 10000 (빠른 실패 처리)
# idleTimeout: 600000 → 300000
# leakDetectionThreshold: 60000 (커넥션 누수 감지 활성화)
```

**성공 기준:** DB 커넥션 수 350 이하로 감소, `DatabaseConnectionException` 발생 중단

---

### 🟠 P2 — 긴급 실행 (30분 이내)

#### [Action 4] Pending Pod 스케줄링 복구 — **DevOps / 인프라팀**

**목적:** 가용 Pod 수 8개 완전 복구

```bash
# 1. Pending Pod 스케줄링 실패 원인 상세 확인
kubectl describe pod payment-gateway-7d9f8b-rp5w2 -n payment-gateway
# → Events 섹션에서 "Insufficient memory" 또는 "MemoryPressure" 확인

# 2. 노드 메모리 압박 상태 확인
kubectl describe nodes | grep -A5 "MemoryPressure"
kubectl top nodes

# 3. 노드 메모리 압박 해소 방법 선택:
# 옵션 A: EKS 노드 그룹 스케일 아웃 (권장)
aws eks update-nodegroup-config \
  --cluster-name prod-cluster \
  --nodegroup-name payment-nodegroup \
  --scaling-config minSize=3,maxSize=6,desiredSize=5

# 옵션 B: 타 네임스페이스 저우선순위 Pod 임시 축소
kubectl scale deployment <low-priority-app> --replicas=0 -n <namespace>

# 4. 노드 메모리 압박 해소 후 Pending Pod 자동 스케줄링 확인
kubectl get pods -n payment-gateway -w
```

**성공 기준:** `payment-gateway-7d9f8b-rp5w2` Running 상태 전환

---

#### [Action 5] 감사 로그 처리 정책 임시 변경 — **개발팀**

**목적:** 스토리지 확보 전까지 감사 로그 실패로 인한 커넥션 누수 차단

```java
// AuditService.java 임시 수정 방향:
// 현재: 감사 로그 저장 실패 시 → 트랜잭션 롤백 (커넥션 누수 유발)
// 변경: 감사 로그 저장 실패 시 → 비동기 재시도 큐에 적재 후 결제 처리 계속

// 단기 조치: Feature Flag로 감사 로그 동기 저장 비활성화
// application.yml:
// audit.log.sync-enabled: false
// audit.log.async-retry-enabled: true
// audit.log.retry-queue-size: 10000
```

**성공 기준:** `StorageWriteException` 발생 시 트랜잭션 롤백 없이 처리 계속, 커넥션 누수 감소

---

### 📊 P3 — 복구 후 검증 (1시간 이내)

#### [Action 6] 복구 검증 및 모니터링 강화 — **운영팀**

```bash
# 1. 전체 Pod 상태 정상화 확인
kubectl get pods -n payment-gateway
# 기대값: 8개 모두 Running, RESTARTS 증가 없음

# 2. 500 에러율 정상화 확인 (Datadog)
# 기대값: 에러율 0.5% 이하, 에러 건수 임계치(20건/15분) 이하

# 3. DB 커넥션 수 정상화 확인
# 기대값: 커넥션 수 300 이하, 증가 추세 없음

# 4. DB 스토리지 여유 확인
# 기대값: 스토리지 사용률 80% 이하

# 5. 결제 처리 성공률 확인
# 기대값: 결제 성공률 99.5% 이상 복구
```

---

## 6. 📊 조치 우선순위 요약표

| 우선순위 | Action | 담당 | 예상 소요 시간 | 완료 기준 |
|---------|--------|------|--------------|----------|
| 🔴 **P1-1** | DB 스토리지 긴급 확보 | DBA / 인프라팀 | 즉시 ~ 10분 | 스토리지 80% 이하 |
| 🔴 **P1-2** | CrashLoopBackOff Pod 재배포 + JVM 힙 조정 | DevOps / 개발팀 | 즉시 ~ 15분 | 전체 Pod Running |
| 🔴 **P1-3** | DB 유휴 커넥션 강제 종료 + 누수 차단 | DBA / 개발팀 | 즉시 ~ 10분 | 커넥션 350 이하 |
| 🟠 **P2-1** | Pending Pod 스케줄링 복구 (노드 스케일 아웃) | DevOps / 인프라팀 | 15 ~ 30분 | rp5w2 Running |
| 🟠 **P2-2** | 감사 로그 비동기 처리 임시 전환 | 개발팀 | 20 ~ 30분 | 롤백 없이 처리 |
| 📊 **P3** | 복구 검증 및 모니터링 확인 | 운영팀 | 복구 후 30분 | 에러율 0.5% 이하 |

---

## 7. ⚠️ 에스컬레이션 기준 (Escalation Criteria)

아래 조건 중 하나라도 해당될 경우 **즉시 경영진 및 On-Call 아키텍트에게 에스컬레이션**하십시오:

- [ ] DB 커넥션 수가 **480/500** 초과 시 → DB 전면 장애 임박
- [ ] DB 스토리지 잔여 용량 **5GB 이하** 도달 시 → 즉각 쓰기 중단 위험
- [ ] 500 에러율이 **10% 초과** 시 → 결제 서비스 사실상 불가 상태
- [ ] 정상 Pod 수가 **3개 이하**로 감소 시 → 서비스 처리 용량 임계 수준
- [ ] 위 P1 Action 중 하나라도 **15분 내 착수 불가** 시

---

## 8. 📝 사후 조치 권고 (Post-Incident Recommendations)

> 즉각 복구 후 **72시간 이내** 아래 항목에 대한 개선 계획을 수립하십시오.

| 분류 | 개선 항목 | 우선순위 |
|------|----------|---------|
| **모니터링** | DB 스토리지 80% 도달 시 사전 경보 설정 (현재 경보 없음) | 🔴 High |
| **모니터링** | JVM 힙 사용률 80% 초과 시 자동 알림 설정 | 🔴 High |
| **아키텍처** | 감사 로그 저장소를 DB와 분리 (별도 스토리지 또는 S3/Kafka) | 🔴 High |
| **코드** | Pod 종료 시 커넥션 반환 보장 로직 추가 (`@PreDestroy`, Graceful Shutdown) | 🔴 High |
| **운영** | DB 스토리지 자동 확장(Auto Scaling) 정책 설정 | 🟠 Medium |
| **코드** | `TransactionCache` 최대 크기 제한 및 TTL 설정 | 🟠 Medium |
| **아키텍처** | 결제 서비스 Circuit Breaker 패턴 도입 (커넥션 풀 고갈 시 빠른 실패 처리) | 🟠 Medium |
| **운영** | 정기 DB 용량 검토 프로세스 수립 (월 1회) | 🟡 Low |

---

## 9. 📌 현재 상태 스냅샷 (10:25Z 기준)

| 컴포넌트 | 상태 | 수치 | 위험도 |
|---------|------|------|--------|
| 프론트엔드 웹 | ✅ 정상 | HTTP 200, 142ms | - |
| payment-gateway 500 에러 | 🔴 위험 | 47건/15분, 3.8%, 증가 중 | CRITICAL |
| EKS Pod 상태 | 🔴 위험 | 5/8 정상, CrashLoop 2개, Pending 1개 | CRITICAL |
| DB 스토리지 | 🔴 위험 | 97.5% 사용, 잔여 12.3GB | CRITICAL |
| DB 커넥션 | 🔴 위험 | 426/500 (85.2%), 지속 증가 | CRITICAL |
| DB CPU | ⚠️ 경고 | 78.4% | WARNING |
| EKS 노드 메모리 | 🔴 위험 | 3개 중 2개 MemoryPressure=True | CRITICAL |

---

> **⏰ 다음 상태 업데이트:** 2025-07-15T10:45:00Z (20분 후)
>
> **인시던트 채널:** `#incident-payment-20250715` (Slack)
>
> **문서 최종 업데이트:** 2025-07-15T10:25:00Z | SM Incident Commander