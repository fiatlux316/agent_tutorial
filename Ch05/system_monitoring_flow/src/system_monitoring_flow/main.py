#!/usr/bin/env python
from pathlib import Path
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
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
    def analysis(self):
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

    @listen(analysis)
    def reporting(self):
        print("장애영향분석 결과 저장")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "post.md", "w") as f:
            f.write(self.state.final_post)
        print("장애영향분석 결과 저장 완료")


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
