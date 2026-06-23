from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai.llm import LLM
from dotenv import load_dotenv
import os

load_dotenv()

top_k_env = os.getenv("BEDROCK_TOP_K", "5")
model_kwargs = {}
model_kwargs["top_k"] = int(top_k_env)
llm = LLM(
    model=f"bedrock/{os.getenv('BEDROCK_MODEL')}",
    region_name=os.getenv('BEDROCK_REGION', 'ap-southeast-2'),
    temperature=0.0,
    max_tokens=8000,
    additional_model_request_fields=model_kwargs
)

@CrewBase
class ContentCrew:
    """Content Crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config["planner"],  # type: ignore[index]
            llm=llm
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],  # type: ignore[index]
            llm=llm
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config["editor"],  # type: ignore[index]
            llm=llm
        )

    @task
    def planning_task(self) -> Task:
        return Task(
            config=self.tasks_config["planning_task"],  # type: ignore[index]
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["writing_task"],  # type: ignore[index]
        )

    @task
    def editing_task(self) -> Task:
        return Task(
            config=self.tasks_config["editing_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Content Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
