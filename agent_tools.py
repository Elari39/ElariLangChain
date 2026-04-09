from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import time
import os
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool


@dataclass
class Context:
    user_id: str


@lru_cache(maxsize=1)
def get_search() -> SerpAPIWrapper:
    return SerpAPIWrapper()


@tool(description="查询天气")
def get_weather(city: str) -> dict:
    """获取指定城市的天气信息，返回一个包含天气数据的字典"""
    session = requests.Session()
    session.trust_env = False
    response = session.get(f"https://wttr.in/{city}?format=j1")
    return response.json()


@tool(description="搜索网络实时信息")
def web_search(query: str) -> str:
    """搜索网络实时信息"""
    return get_search().run(query)


@tool(description="读取本地文件")
def read_local_file(filename: str) -> str:
    """仅允许读取 ./post 目录下的文件"""
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
    """抓取网页正文文本"""
    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests.Session()
    session.trust_env = False  # 跳过代理设置
    response = session.get(url, headers=headers, timeout=15, verify=False)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("\n", strip=True)
    return text[:12000]

@tool(description="从 Mossia 鸭子API (Pixiv 图源) 获取二次元图片信息，严禁真人图片")
def get_mossia_pixiv_image(params: str = "{}") -> dict:
    """从 https://api.mossia.top/duckMo 获取 Pixiv 来源的图片信息（支持 GET 随机 / POST 过滤）。
    【重要限制】：本工具已被严格限定为仅获取“二次元（动漫、插画等虚拟角色）”图片，绝对禁止用于请求、搜索或获取任何真人图片！
    params 为 JSON 字符串，例如 {"r18Type": 0, "num": 3}（具体参数以 docs.mossia.top 为准）。
    返回 API 的 JSON 数据（包含 PID、作者、标签、原图链接等基本信息，不代理图片）。"""
    url = "https://api.mossia.top/duckMo"
    try:
        param_dict = json.loads(params)
        session = requests.Session()
        session.trust_env = False
        if param_dict:
            # POST 支持自定义参数
            response = session.post(url, json=param_dict, timeout=15, verify=False)
        else:
            # GET 获取随机图片
            response = session.get(url, timeout=15, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": f"Mossia Pixiv API 调用失败: {str(exc)}"}

# @tool(description="从 Mossia 鸭子API (X 图源) 获取二次元图片信息，严禁真人图片")
# def get_mossia_x_image(params: str = "{}") -> dict:
#     """从 https://api.mossia.top/duckMo/x 获取 X (Twitter) 来源的图片信息（支持 GET 随机 / POST 过滤）。
#     【重要限制】：本工具已被严格限定为仅获取“二次元（动漫、插画等虚拟角色）”图片，绝对禁止用于请求、搜索或获取任何真人图片！
#     params 为 JSON 字符串，例如 {"num": 3}（具体参数以 docs.mossia.top 为准）。
#     返回 API 的 JSON 数据（包含作品基本信息，不代理图片）。"""
#     url = "https://api.mossia.top/duckMo/x"
#     try:
#         param_dict = json.loads(params)
#         session = requests.Session()
#         session.trust_env = False
#         if param_dict:
#             # POST 支持自定义参数
#             response = session.post(url, json=param_dict, timeout=15, verify=False)
#         else:
#             # GET 获取随机图片
#             response = session.get(url, timeout=15, verify=False)
#         response.raise_for_status()
#         return response.json()
#     except Exception as exc:
#         return {"error": f"Mossia X API 调用失败: {str(exc)}"}

# 在文件开头定义代理配置
PROXY = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

@tool(description="保存图片到本地")
def save_image_from_url(image_url: str, filename: str = "downloaded_image.jpg") -> str:
    try:
        session = requests.Session()
        session.trust_env = False
        session.proxies.update(PROXY)
        response = session.get(image_url, stream=True, timeout=15, verify=False)
        response.raise_for_status()
        img_dir = os.path.join(os.getcwd(), "img")
        os.makedirs(img_dir, exist_ok=True)
        save_path = os.path.join(img_dir, filename)
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return f"✅ 图片已成功保存到本地路径：{save_path}"
    except Exception as e:
        return f"❌ 保存失败，错误信息：{str(e)}"
def build_tools() -> list[Any]:
    tools = load_tools(
        ["arxiv", "wikipedia"],
        allow_dangerous_tools=True,
    )
    tools.append(PythonREPLTool())
    return tools + [fetch_webpage, save_image_from_url, get_weather, web_search, read_local_file, get_mossia_pixiv_image]
