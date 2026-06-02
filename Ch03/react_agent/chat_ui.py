# ==== Gradio 4.x: Chatbot은 messages 형식을 기대 ====
import gradio as gr
from contextlib import redirect_stdout
import io
from react_agent import run_react

class ConversationManager:
    def __init__(self):
        self.chat_history = []     # [(user_text, assistant_text), ...] 내부 보관은 유지
        self.execution_logs = []

    def process_message(self, message: str):
        self.execution_logs = []
        try:
            context_str = ""
            if self.chat_history:
                context_str = "이전 대화 내용:\n"
                for i, (q, a) in enumerate(self.chat_history):
                    context_str += f"질문 {i+1}: {q}\n답변 {i+1}: {a}\n"
                context_str += "\n위 대화 맥락을 고려해서 다음 질문에 답변해주세요.\n\n"

            full_message = context_str + message

            f = io.StringIO()
            with redirect_stdout(f):
                result = run_react(full_message, max_iters=10)
                response = result["output"]
                exec_log = result.get("log", "")

            execution_log = f.getvalue() + "\n" + exec_log
            self.execution_logs.append(execution_log)

            # 내부 기록은 기존대로 유지
            self.chat_history.append((message, response))
            return response, execution_log
        except Exception as e:
            error_message = f"오류가 발생했습니다: {str(e)}"
            self.chat_history.append((message, error_message))
            return error_message, f"실행 중 오류: {str(e)}"

    def clear_history(self):
        self.chat_history = []
        self.execution_logs = []
        return []

conversation_manager = ConversationManager()

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