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
        # chunk 是一个字典，如 {'agent': {...}} 或 {'tools': {...}}
        for node_name, output in chunk.items():
            if "messages" in output:
                last_msg = output["messages"][-1]
                # 如果是 AIMessage 且有文本内容，则更新最终答案
                if hasattr(last_msg, "content") and last_msg.content:
                    final_answer = last_msg.content
    print(final_answer)

def main() -> None:
    agent = build_agent()
    context = build_runtime_context(user_id="user_1")
    config = build_config(thread_id="user_1_session")
    while True:
        user_input = input("请输入您的问题：")
        stream_answer(agent, context, config, user_input)
        print("-" * 50,end="\n\n")

if __name__ == "__main__":
    main()
