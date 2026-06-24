#!/usr/bin/env python
from pathlib import Path
from pydantic import BaseModel
from crewai.flow import Flow, listen, start, and_, or_, router
from system_monitoring_flow.crews.monitoring_crew.crew import MonitoringCrew


class ContentState(BaseModel):
    topic: str = "장애영향분석"
    target_url: str = "https://your-service.com/health"
    target_service: str = "payment-gateway"
    final_post: str = ""

class MonitoringFlow(Flow[ContentState]):

    @start()    
    def start(self, crewai_trigger_payload: dict = None):
        print("flow start")

        if crewai_trigger_payload:
            self.state.topic = crewai_trigger_payload.get("topic", "장애영향분석")
            print(f"Using trigger payload: {crewai_trigger_payload}")
        else:
            self.state.topic = "장애영향분석"

        print(f"Topic: {self.state.topic}")

    @listen(start)
    def analysis_crew(self):
        print(f"analysis on topic: {self.state.topic}")
        result = (
            MonitoringCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic, 
                            "target_url": self.state.target_url, 
                            "target_service": self.state.target_service})
        )

        print("장애영향분석 결과 출력")
        self.state.final_post = result.raw

    @router(analysis_crew)
    def next_step(self, result):
        # 필요시 로직 분기 처리 (코드개선 or 튜닝)
        if True:
            return "coding_crew"
        return "tuning_crew"

    @listen(next_step)
    def coding_crew(self):
        print(f"coding on topic: {self.state.topic}")
        result = "코드개선결과"

        print("코드개선 결과 출력")
        # to-do : 필요시 로직 구현
        #self.state.final_post = result

    @listen(next_step)
    def tuning_crew(self):
        print(f"tuning on topic: {self.state.topic}")
        result = "성능튜닝결과"

        print("성능튜닝 결과 출력")
        # to-do : 필요시 로직 구현
        #self.state.final_post = result

    @listen(and_(coding_crew, tuning_crew))
    def reporting(self):
        print("결과 취합 및 저장")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "post.md", "w") as f:
            f.write(self.state.final_post)
        print("결과 저장 완료")


def kickoff():
    monitoring_flow = MonitoringFlow()
    monitoring_flow.kickoff()


def plot():
    monitoring_flow = MonitoringFlow()
    monitoring_flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload.
    """
    import json
    import sys

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    monitoring_flow = MonitoringFlow()

    try:
        result = monitoring_flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    kickoff()
