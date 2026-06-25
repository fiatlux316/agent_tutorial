from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task, tool

from system_monitoring_flow.tools.custom_tool import (
    check_datadog_500_errors as _check_datadog_500_errors,
    check_frontweb_health as _check_frontweb_health,
    check_eks_pod_status as _check_eks_pod_status,
    check_db_resource_capacity as _check_db_resource_capacity,
    analyze_log_anomalies as _analyze_log_anomalies,
)

from dotenv import load_dotenv
load_dotenv()

import agentops
# 2. AgentOps 초기화 (반드시 CrewAI 컴포넌트 생성 전에 호출)
# tags 인자를 넣으면 대시보드에서 프로젝트를 분류해서 보기 편합니다.
agentops.init(tags=['system-monitoring-flow'])

# bedrock api 호출 
# import os

# from crewai import LLM
# top_k_env = os.getenv("BEDROCK_TOP_K", "5")
# model_kwargs = {}
# model_kwargs["top_k"] = int(top_k_env)
# llm = LLM(
#     model=f"bedrock/{os.getenv('BEDROCK_MODEL')}",
#     region_name=os.getenv('BEDROCK_REGION', 'ap-southeast-2'),
#     temperature=0.0,
#     max_tokens=8000,
#     additional_model_request_fields=model_kwargs
# )

# devx api 호출
from ..devx_llm_wrapper import llm


@CrewBase
class MonitoringCrew:
    """System Monitoring Crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ── Tool 등록 (YAML에서 이름으로 참조됨) ──
    @tool
    def check_datadog_500_errors(self):
        return _check_datadog_500_errors

    @tool
    def check_frontweb_health(self):
        return _check_frontweb_health

    @tool
    def check_eks_pod_status(self):
        return _check_eks_pod_status

    @tool
    def check_db_resource_capacity(self):
        return _check_db_resource_capacity

    @tool
    def analyze_log_anomalies(self):
        return _analyze_log_anomalies


    @agent
    def monitoring_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["monitoring_engineer"],  # type: ignore[index]
            llm=llm
        )

    @agent
    def log_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["log_analyst"],  # type: ignore[index]
            llm=llm
        )

    @agent
    def incident_commander(self) -> Agent:
        return Agent(
            config=self.agents_config["incident_commander"],  # type: ignore[index]
            llm=llm
        )

    @task
    def health_check_task(self) -> Task:
        return Task(
            config=self.tasks_config["health_check_task"],  # type: ignore[index]
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["log_analysis_task"],  # type: ignore[index]
        )

    @task
    def incident_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["incident_report_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the System Monitoring Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
