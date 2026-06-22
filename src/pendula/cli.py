from .s02 import agent_loop


def main() -> None:
    print("s02: Tool Use — typed dispatch via Pydantic models")
    print("输入问题,回车发送。输入 q 退出。\n")

    history = []
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        last_msg = history[-1]
        if last_msg["role"] == "assistant" and last_msg["content"]:
            print(last_msg["content"])
        print()
