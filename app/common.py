from langchain_community.agent_toolkits import FileManagementToolkit
from dotenv import load_dotenv

load_dotenv()

# =========================
# 2. Tool 定义
# =========================

FILE_DIR = "/Users/leyouhong/workspace/ai-projects/ai-agent-test/app/temp"

file_toolkit = FileManagementToolkit(root_dir=FILE_DIR)
file_tools = file_toolkit.get_tools()