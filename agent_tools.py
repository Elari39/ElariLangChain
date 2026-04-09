from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import os

import requests
import urllib3
from bs4 import BeautifulSoup
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool
from mossia_pixiv_tool import get_mossia_pixiv_image as structured_get_mossia_pixiv_image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Context:
    user_id: str


PROXY = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}


@lru_cache(maxsize=1)
def get_search() -> SerpAPIWrapper:
    return SerpAPIWrapper()


def format_request_error(tool_name: str, exc: Exception) -> str:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        status_code = exc.response.status_code
        reason = exc.response.reason or "Unknown"
        return f"{tool_name}调用失败: HTTP {status_code} {reason}"
    return f"{tool_name}调用失败: {str(exc)}"


@tool(description="查询天气")
def get_weather(city: str) -> dict:
    """获取指定城市的天气信息，返回一个包含天气数据的字典。"""
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get(f"https://wttr.in/{city}?format=j1", timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": format_request_error("天气查询", exc)}


@tool(description="搜索网络实时信息")
def web_search(query: str) -> str:
    """搜索网络实时信息。"""
    try:
        return get_search().run(query)
    except Exception as exc:
        return format_request_error("网络搜索", exc)


@tool(description="读取本地文件")
def read_local_file(filename: str) -> str:
    """仅读取 ./post 目录下的文件。"""
    safe_path = f"./post/{filename.strip()}"
    if not safe_path.startswith("./post/") or ".." in safe_path:
        return "禁止访问路径"
    try:
        with open(safe_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as exc:
        return f"读取失败: {str(exc)}"


@tool(description="抓取网页正文文本")
def fetch_webpage(url: str) -> str:
    """抓取网页正文文本。"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text("\n", strip=True)
        return text[:12000]
    except Exception as exc:
        return format_request_error("网页抓取", exc)


get_mossia_pixiv_image = structured_get_mossia_pixiv_image


@tool(description="保存图片到本地")
def save_image_from_url(image_url: str, filename: str = "downloaded_image.jpg") -> str:
    """将图片保存到当前工作目录下的 img 目录。"""
    try:
        session = requests.Session()
        session.trust_env = False
        session.proxies.update(PROXY)
        response = session.get(image_url, stream=True, timeout=15, verify=False)
        response.raise_for_status()
        img_dir = os.path.join(os.getcwd(), "img")
        os.makedirs(img_dir, exist_ok=True)
        save_path = os.path.join(img_dir, filename)
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return f"图片已成功保存到本地路径: {save_path}"
    except Exception as exc:
        return f"保存失败，错误信息: {str(exc)}"


def build_tools() -> list[Any]:
    tools = load_tools(
        ["arxiv", "wikipedia"],
        allow_dangerous_tools=True,
    )
    tools.append(PythonREPLTool())
    return tools + [
        fetch_webpage,
        save_image_from_url,
        get_weather,
        web_search,
        read_local_file,
        get_mossia_pixiv_image,
    ]
