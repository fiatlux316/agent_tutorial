#!/usr/bin/env python
from pathlib import Path
from pydantic import BaseModel
from crewai.flow import Flow, listen, start, and_, or_, router
from data_annotating_flow.crews.data_annotating_crew.crew import DataAnnotatingCrew


class ContentState(BaseModel):
    input_file: str = ""
    final_post: str = ""

class DataAnnotatingFlow(Flow[ContentState]):

    @start()    
    def start(self, crewai_trigger_payload: dict = None):
        print("flow start")

        if crewai_trigger_payload:
            self.state.input_file = crewai_trigger_payload.get("input_file", "챗봇로그_0503.csv")
            print(f"Using trigger payload: {crewai_trigger_payload}")
        else:
            self.state.input_file = "챗봇로그_0503.csv"

        print(f"input_file: {self.state.input_file}")

    @listen(start)
    def annotation_crew(self):
        print(f"input_file: {self.state.input_file}")
        result = (
            DataAnnotatingCrew()
            .crew()
            .kickoff(inputs={"input_file": f"input/{self.state.input_file}"})
        )

        print("챗봇응답분석 결과 출력")
        self.state.final_post = result.raw

    @listen(annotation_crew)
    def reporting(self):
        print("결과 취합 및 저장")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "chatbot_response_analysis.md", "w") as f:
            f.write(self.state.final_post)
        print("결과 저장 완료")


def kickoff():
    data_annotating_flow = DataAnnotatingFlow()
    data_annotating_flow.kickoff()


def plot():
    data_annotating_flow = DataAnnotatingFlow()
    data_annotating_flow.plot()


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

    data_annotating_flow = DataAnnotatingFlow()

    try:
        result = data_annotating_flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    kickoff()
