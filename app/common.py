import os

from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# =========================
# 1. LLM 定义
# =========================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ["OPENAI_API_KEY"],
    streaming=True,
)

# =========================
# 2. Tool 定义
# =========================

ROOT_DIR = "/Users/leyouhong/workspace/ai-projects/ai-agent-test"

file_toolkit = FileManagementToolkit()
file_tools = file_toolkit.get_tools()
