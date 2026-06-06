# ==== Gradio 4.x: Chatbot은 messages 형식을 기대 ====
import gradio as gr
from agent import conversation_manager


# Step1. Gradio UI 함수
def ui_process_message(message, history):
    if not message:
        return "", history, ""
    
    answer, log = conversation_manager.process_message(message)
    
    # Gradio 4.x 메시지 포맷: {"role": "user"/"assistant", "content": "..."}
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer}
    ]
    
    return "", history, log


# Step2. 대화 초기화 함수
def clear_conversation():
    """대화 이력 초기화"""
    conversation_manager.clear_history()
    return [], ""


# Step3. Gradio 인터페이스 구성
with gr.Blocks(css="footer {visibility: hidden}") as demo:
    gr.Markdown("# 쇼핑몰 고객 지원 에이전트 (LangChain Function Calling)")
    gr.Markdown("고객 프로필, 주문 내역, 배송 상태, 포인트, 결제 정보 등에 관한 질문을 해보세요.")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(label="질문을 입력하세요", placeholder="예: 고객 ID C001의 프로필 정보를 알려주세요")
            clear = gr.Button("대화 초기화")
        with gr.Column(scale=1):
            log_output = gr.Textbox(label="실행 로그", lines=15)

    msg.submit(ui_process_message, inputs=[msg, chatbot], outputs=[msg, chatbot, log_output])
    clear.click(clear_conversation, outputs=[chatbot, log_output])

    gr.Markdown("""
    ### 예시 질문:
    - 고객 ID C001의 프로필 정보를 알려주세요
    - 그 고객의 주문 내역을 조회해주세요
    - 배송 상태도 확인해주세요
    - 고객 ID C002의 주문 내역을 조회해주세요
    - 고객 ID C003의 배송 상태를 확인하고 싶어요
    - 고객 ID C004의 포인트 정보가 궁금합니다
    """)

demo.launch(debug=True)
#demo.launch(share=True)