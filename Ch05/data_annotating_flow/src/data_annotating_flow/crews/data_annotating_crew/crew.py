from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task, tool

from data_annotating_flow.tools.custom_tool import (
    load_csv as _load_csv
)

from dotenv import load_dotenv
load_dotenv()

import agentops
# 2. AgentOps 초기화 (반드시 CrewAI 컴포넌트 생성 전에 호출)
# tags 인자를 넣으면 대시보드에서 프로젝트를 분류해서 보기 편합니다.
agentops.init(tags=['data-annotating-flow'])

# devx api 호출
from ..devx_llm_wrapper import llm


@CrewBase
class DataAnnotatingCrew:
    """FAQ Data Annotating Crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ── Tool 등록 (YAML에서 이름으로 참조됨) ──
    @tool
    def load_csv(self):
        return _load_csv

    @agent
    def chatbot_data_collector(self) -> Agent:
        return Agent(
            config=self.agents_config["chatbot_data_collector"],  # type: ignore[index]
            llm=llm
        )

    @agent
    def faq_data_annotator(self) -> Agent:
        return Agent(
            config=self.agents_config["faq_data_annotator"],  # type: ignore[index]
            llm=llm
        )

    @task
    def chatbot_data_transform_task(self) -> Task:
        return Task(
            config=self.tasks_config["chatbot_data_transform_task"],  # type: ignore[index]
        )

    @task
    def faq_data_annotation_task(self) -> Task:
        return Task(
            config=self.tasks_config["faq_data_annotation_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the FAQ Annotating Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )