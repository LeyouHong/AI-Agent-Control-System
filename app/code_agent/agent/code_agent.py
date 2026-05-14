import asyncio
import time

from langchain.messages import AIMessage, ToolMessage
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig

from app.code_agent.tools.file_saver import FileSaver
from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.tools.file_tools import file_toolskit
from app.code_agent.tools.terminal_tools import get_stdio_terminal_tools

def format_debug_output(step_name: str, content: str, is_tool_call = False) -> None:
    if is_tool_call:
        print(f"🔄 [Tool Call: {step_name}]")
        print ("-" * 40)
        print(content.strip())
        print ("-" * 40)
    else:
        print(f"💭 [{step_name}]")
        print ("-" * 40)
        print(content.strip())
        print ("-" * 40)

async def run_agent():
    saver = FileSaver()

    terminal_tools = await get_stdio_terminal_tools()
    tools = file_toolskit + terminal_tools

    config = RunnableConfig(configurable={"thread_id": 3})

    agent = create_agent(
        model=llm_gpt, 
        tools=tools, 
        checkpointer=saver,
    )

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            break

        print("\n🤖 AI is thinking...\n")
        print("=" * 60)

        iteration_count = 0
        start_time = time.time()
        last_tool_time = start_time

        async for chunk in agent.astream(input={"messages": [
            ("user", user_input)
        ]}, config=config):
            iteration_count += 1

            print(f"\n📊 This is {iteration_count} step: ")
            print("-" * 30)
            
            items = chunk.items()
            for node_name, node_output in items:
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.content:
                                format_debug_output("AI thinking", msg.content)
                            else:
                                for tool in msg.tool_calls:
                                    format_debug_output(f"Tool Call", f"{tool['name']}: {tool['args']}")
                        elif isinstance(msg, ToolMessage):
                            tool_name = getattr(msg, "name", "Unknown Tool")
                            tool_content = msg.content

                            current_time = time.time()
                            tool_duration = current_time - last_tool_time
                            last_tool_time = current_time

                            tool_result = f"""
                            🔧 Tool: {tool_name}
🤖 Result: {tool_content}
✅ Status: Completed, start next task
🕒 Duration: {tool_duration:.2f} seconds
"""

                            format_debug_output(f"Tool Output", tool_result, is_tool_call=True)
                        else:
                            format_debug_output("Not Implemented", f"Not implemented {chunk}.")

        print()
    
asyncio.run(run_agent())