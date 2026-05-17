import os
from typing import Annotated

from alibabacloud_bailian20231229 import client as bailian_20231229_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from dotenv import load_dotenv
from langsmith import traceable
from mcp.server.fastmcp import FastMCP
from pydantic import Field

load_dotenv()

mcp = FastMCP()

_REQUIRED_ENV = (
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    "ALIBABA_CLOUD_INDEX_ID",
)
_WORKSPACE_ENV_KEYS = ("ALIBABA_CLOUD_WORKSPACE_ID", "WORKSPACE_ID")


def _get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise KeyError(name)
    return value


def _get_workspace_id() -> str:
    for key in _WORKSPACE_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return value
    raise KeyError(" or ".join(_WORKSPACE_ENV_KEYS))


def _create_client() -> bailian_20231229_client.Client:
    config = open_api_models.Config(
        access_key_id=_get_env("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=_get_env("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    )
    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian_20231229_client.Client(config=config)


def _retrieve_index(client, workspace_id: str, index_id: str, query: str):
    headers = {}
    retrieve_request = bailian_20231229_models.RetrieveRequest(
        index_id=index_id,
        query=query,
    )
    runtime = util_models.RuntimeOptions()
    return client.retrieve_with_options(
        workspace_id, retrieve_request, headers, runtime
    )


def _format_nodes(rag) -> str:
    body = getattr(rag, "body", None)
    data = getattr(body, "data", None) if body else None
    nodes = getattr(data, "nodes", None) if data else None
    nodes = nodes or []

    if not nodes:
        return "No results found."

    sections: list[str] = []
    for index, node in enumerate(nodes, start=1):
        text = getattr(node, "text", None) or ""
        sections.append(f"{index} section: knowledge\n{text}\n--")
    return "\n".join(sections)


@traceable(run_type="tool", name="Query RAG")
@mcp.tool(name="query_rag", description="Query knowledge from bailian")
def query_rag_from_bailian(
    query: Annotated[
        str,
        Field(
            description="query content",
            json_schema_extra={"example": "Terminal Operation Instruction"},
        ),
    ],
) -> str:
    try:
        for name in _REQUIRED_ENV:
            _get_env(name)
        workspace_id = _get_workspace_id()
        index_id = _get_env("ALIBABA_CLOUD_INDEX_ID")

        bailian_client = _create_client()
        rag = _retrieve_index(bailian_client, workspace_id, index_id, query)
        return _format_nodes(rag)
    except KeyError as e:
        return f"Missing environment variable: {e}"
    except Exception as e:
        return f"RAG query failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
