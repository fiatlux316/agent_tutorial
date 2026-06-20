from crewai import Agent, Task
from pydantic import BaseModel

from agents import blog_agent, analyst, writer, real_estate_researcher, report_writer
from tools import serper_tool

# 블로그 출력 구조 정의(Pydantic) → Task 결과 형식 강제
class Blog(BaseModel):
    title: str
    content: str

# 1) 블로그 글 생성 Task: 원본 콘텐츠 만들기
write_blog_task = Task(
    description=(
        "{topic}에 대한 블로그 제목과 본문을 작성하라. "
        "본문은 200단어 이내로 구성하고, 비전공자도 이해할 수 있게 설명한다."
    ),
    expected_output=(
        "다음 필드를 갖는 결과를 생성한다.\n"
        "- title: 블로그 제목 한 문장\n"
        "- content: 200단어 이내의 블로그 본문"
    ),
    agent=blog_agent,          # 블로그 작성 전담 에이전트
    output_pydantic=Blog       # 출력 형식을 Blog 모델로 강제
)

# 2) 생성된 글을 기반으로 요약·정리 Task: 2차 가공 + 파일 저장
save_task = Task(
    description=(
        "이전 Task에서 생성한 블로그 글을 바탕으로, "
        "핵심 내용을 요약하고 주요 포인트를 정리하라. "
        "경영진이 빠르게 읽을 수 있는 요약본 형식으로 작성한다."
    ),
    expected_output=(
        "다음 구조의 Markdown 텍스트를 생성한다.\n"
        "1. 3문장 이내 전체 요약\n"
        "2. 핵심 포인트 3~5개를 불릿 리스트로 정리"
    ),
    agent=blog_agent,
    context=[write_blog_task],       # 이전 Task 결과를 입력으로 사용
    markdown=True,                   # Markdown 포맷으로 결과 생성
    output_file="output/blog_summary.md",  # 요약본을 파일로 저장
    create_directory=True            # 경로가 없으면 자동 생성
)

# 데이터 분석 Task
analyze_task = Task(
    description=(
        "'{topic}'에 대해 수집된 정보를 분석하여 핵심 인사이트 3가지를 도출하세요."
    ),
    expected_output="핵심 인사이트 목록.",
    agent=analyst
)

# 보고서 작성 Task
write_task = Task(
    description=(
        "'{topic}'에 대한 분석 내용을 기반으로 간단한 보고서를 작성하세요."
    ),
    expected_output="300자 내외 보고서 문단.",
    agent=writer
)


# 3-1) 웹에서 정보 수집
search_task = Task(
    description=(
        "다음 질문에 대해 SerperDevTool을 사용해 웹을 검색하고, "
        "관련성이 높은 기사와 리포트를 찾아 요약하라.\n"
        "질문: {question}\n\n"
        "요구사항:\n"
        "1) 최근 1~2년 내 기사/보고서를 우선적으로 참고한다.\n"
        "2) 서로 다른 출처(언론사, 리포트)를 최소 2개 이상 포함한다.\n"
    ),
    expected_output=(
        "다음 형식의 요약 노트를 작성한다.\n\n"
        "1. 참고한 주요 기사/리포트 목록 (제목 · 출처 · URL)\n"
        "2. 기사/리포트에서 공통적으로 언급하는 핵심 키워드 3~5개\n"
        "3. 각 키워드에 대한 한두 문장 요약"
    ),
    agent=real_estate_researcher,
    tools=[serper_tool],
    verbose=True,
)

# 3-2) 수집된 내용을 바탕으로 전망 리포트 작성
analysis_task = Task(
    description=(
        "이전 태스크에서 정리한 웹 검색 요약을 바탕으로 "
        "한국 부동산 시장 전망에 대해 분석 리포트를 작성하라.\n"
        "질문: {question}\n\n"
        "요구사항:\n"
        "1) 단기(1년 이내)와 중기(3년 이내) 전망을 나누어 서술한다.\n"
        "2) 상승/하락 요인과 리스크 요인을 구분해 정리한다.\n"
        "3) 과도한 확신 표현은 피하고, '가능성이 높다/낮다' 수준으로 표현한다.\n"
    ),
    expected_output=(
        "다음 구조의 한국어 리포트를 작성한다.\n\n"
        "1. 한 줄 요약\n"
        "2. 단기 전망 (1년 이내)\n"
        "3. 중기 전망 (3년 이내)\n"
        "4. 주요 상승 요인\n"
        "5. 주요 하락·리스크 요인\n"
        "6. 참고: 사용한 기사/리포트의 간단한 출처 요약"
    ),
    agent=report_writer,
    context=[search_task],  # ✅ 검색 결과를 컨텍스트로 활용
    verbose=True,
)

