# ==== Gradio 4.x: Chatbot은 messages 형식을 기대 ====
import gradio as gr
from agent import conversation_manager



def chat_with_agent(message, history):
    try:
        response, execution_log = conversation_manager.process_message(message)
    except Exception as e:
        err_msg = f"[오류] {type(e).__name__}: {e}"
        print(err_msg)  # 콘솔에 오류 출력
        response = err_msg
        execution_log = err_msg

    history = (history or []) + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ]
    return "", history, execution_log

def clear_chat_history():
    conversation_manager.clear_history()
    return [], ""   # 빈 messages, 빈 로그

with gr.Blocks() as demo:
    gr.HTML("<style>footer{visibility:hidden}</style>")
    gr.Markdown("# ReACT 에이전트")
    gr.Markdown("일본과 미국의 ICT 정책 또는 미국의 블록체인 동향에 관한 질문을 해보세요. 대화 컨텍스트를 유지합니다.")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=500)  # type 인자 없이 사용. 단, messages 형식 데이터를 넘겨야 함.
            msg = gr.Textbox(label="질문을 입력하세요", placeholder="예: 일본의 AI 정책에 대해 알려줘")
            clear = gr.Button("대화 초기화")

        with gr.Column(scale=1):
            logs = gr.Textbox(label="ReACT 실행 로그", lines=25, max_lines=25)

    msg.submit(chat_with_agent, inputs=[msg, chatbot], outputs=[msg, chatbot, logs])
    clear.click(clear_chat_history, inputs=None, outputs=[chatbot, logs])

demo.launch(debug=True)