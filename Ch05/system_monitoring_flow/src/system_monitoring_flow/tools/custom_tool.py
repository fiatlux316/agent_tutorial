from crewai.tools import tool
import os
import requests

@tool
def check_datadog_500_errors(service_name: str) -> str:
    """
    Datadog API를 호출하여 특정 서비스의 최근 15분간 500 에러 발생 횟수와 트렌드를 반환합니다.
    - service_name: 조회할 대상 서비스의 영문 이름 (예: 'payment-gateway', 'auth-service')
    """
    # TODO: datadog_api_client 연동 로직 추가
    return f"[{service_name}] Datadog Alert: 최근 15분간 500 에러 42건 발생. 급증 추세 (임계치 초과)."

@tool
def check_frontweb_health(url: str) -> str:
    """주어진 프론트엔드 웹 URL의 HTTP 상태 코드와 응답 속도를 체크합니다."""
    try:
        response = requests.get(url, timeout=5)
        return f"[Web Health] {url} - Status: {response.status_code}, Response Time: {response.elapsed.total_seconds()}s"
    except Exception as e:
        return f"[Web Health] {url} - 접근 실패. 상세: {str(e)}"

@tool
def check_eks_pod_status(namespace: str) -> str:
    """AWS EKS 클러스터의 특정 네임스페이스 내 비정상(CrashLoopBackOff, Pending 등) Pod 목록을 반환합니다."""
    # TODO: kubernetes client 또는 boto3 연동 로직 추가
    return f"[EKS Status] namespace: {namespace} 내 비정상 Pod 감지. 'payment-service-pod-xyz' (CrashLoopBackOff)"

@tool
def check_db_resource_capacity(db_instance_id: str) -> str:
    """지정된 데이터베이스 인스턴스의 CPU 사용량, 커넥션 수, 스토리지 가용량을 확인합니다."""
    # TODO: AWS RDS API 또는 직접 DB 쿼리(pg_stat_activity 등) 연동
    return f"[DB Resource] {db_instance_id} - CPU: 85%, Active Connections: 150/200, Storage Free: 40GB. 커넥션 풀 병목 의심."

@tool
def analyze_log_anomalies(service_name: str) -> str:
    """로그 시스템(Elasticsearch/Opensearch 등)에서 특정 서비스의 최근 에러 로그 스택트레이스를 분석합니다."""
    # TODO: Elasticsearch 쿼리 연동 로직 추가
    return f"[Log Analysis] {service_name}에서 'java.sql.SQLTransientConnectionException: Connection is not available' 반복 발생 확인."