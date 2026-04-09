from agent_factory import build_agent, build_config, build_runtime_context


def invoke_answer(agent, context, config, user_input):
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"{user_input}"}]},
        context=context,
        config=config,
    )
    print(result["messages"][-1].content)


def stream_answer(agent, context, config, user_input):
    final_answer = None
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        context=context,
        config=config,
    ):
        # chunk 是一个字典，如 {"agent": {...}} 或 {"tools": {...}}
        for node_name, output in chunk.items():
            if "messages" in output:
                last_msg = output["messages"][-1]
                if hasattr(last_msg, "content") and last_msg.content:
                    final_answer = last_msg.content
    print(final_answer)


def read_multiline_input(
    prompt: str = "请输入您的问题：",
    continuation_prompt: str = "... ",
) -> str:
    lines: list[str] = []
    empty_line_count = 0

    while True:
        current_prompt = prompt if not lines else continuation_prompt
        line = input(current_prompt)

        if line == "":
            empty_line_count += 1
            if empty_line_count == 2:
                if lines and lines[-1] == "":
                    lines.pop()
                break
            lines.append("")
            continue

        empty_line_count = 0
        lines.append(line)

    return "\n".join(lines)


def main() -> None:
    agent = build_agent()
    context = build_runtime_context(user_id="user_1")
    config = build_config(thread_id="user_1_session")
    try:
        while True:
            user_input = read_multiline_input()
            if not user_input.strip():
                continue
            try:
                stream_answer(agent, context, config, user_input)
                print("-" * 50, end="\n\n")
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print(f"本轮处理失败：{str(exc)}")
                print("-" * 50, end="\n\n")
    except KeyboardInterrupt:
        print("\n已退出程序")


if __name__ == "__main__":
    main()
