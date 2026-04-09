from typing import Any

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field

MOSSIA_PIXIV_API_URL = "https://api.mossia.top/duckMo"
MOSSIA_TIMEOUT = 30
VALID_SIZE_LIST = {"original", "regular", "small", "thumb", "mini"}


class MossiaPixivImageInput(BaseModel):
    """Pixiv 图源查询参数。"""

    num: int | None = Field(default=None, description="一次返回的结果数量，范围 1 到 20。")
    pid: list[int] | None = Field(default=None, description="返回指定 pid 图片。")
    uid: list[int] | None = Field(default=None, description="返回指定 uid 作者的作品。")
    author: str | None = Field(default=None, description="根据作者名称模糊搜索作品。")
    proxy: str | None = Field(default=None, description="设置图片地址所使用的在线反代服务。")
    aiType: int | None = Field(default=None, description="AI 类型：0 未知，1 否，2 是。")
    r18Type: int | None = Field(default=None, description="R18 类型：0 不是，1 是。")
    dateAfter: int | None = Field(default=None, description="返回在该时间及以后上传的作品，单位为毫秒时间戳。")
    dateBefore: int | None = Field(default=None, description="返回在该时间及以前上传的作品，单位为毫秒时间戳。")
    sizeList: list[str] | None = Field(
        default=None,
        description="返回指定图片规格的地址，可选值 original、regular、small、thumb、mini。",
    )
    imageSizeType: int | None = Field(default=None, description="图片尺寸：1 横图，2 竖图，3 方图。")


def format_mossia_pixiv_request_error(exc: Exception) -> str:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        status_code = exc.response.status_code
        reason = exc.response.reason or "Unknown"
        return f"Mossia Pixiv API 请求失败: HTTP {status_code} {reason}"
    return f"Mossia Pixiv API 请求失败: {str(exc)}"


def build_mossia_pixiv_error(err_code: str, message: str) -> dict[str, Any]:
    return {
        "success": False,
        "errCode": err_code,
        "message": message,
        "data": [],
    }


def create_mossia_pixiv_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def _clean_positive_int_list(values: list[int] | None, field_name: str) -> tuple[list[int] | None, str | None]:
    if values is None:
        return None, None

    cleaned_values = [value for value in values if value is not None]
    if not cleaned_values:
        return None, None
    if any(value <= 0 for value in cleaned_values):
        return None, f"{field_name} 里的值必须大于 0。"
    return cleaned_values, None


def _clean_size_list(size_list: list[str] | None) -> tuple[list[str] | None, str | None]:
    if size_list is None:
        return None, None

    cleaned_size_list = [size.strip() for size in size_list if isinstance(size, str) and size.strip()]
    if not cleaned_size_list:
        return None, None

    invalid_sizes = sorted({size for size in cleaned_size_list if size not in VALID_SIZE_LIST})
    if invalid_sizes:
        return None, f"sizeList 仅支持 {', '.join(sorted(VALID_SIZE_LIST))}，收到: {', '.join(invalid_sizes)}。"
    return cleaned_size_list, None


def build_mossia_pixiv_payload(
    num: int | None = None,
    pid: list[int] | None = None,
    uid: list[int] | None = None,
    author: str | None = None,
    proxy: str | None = None,
    aiType: int | None = None,
    r18Type: int | None = None,
    dateAfter: int | None = None,
    dateBefore: int | None = None,
    sizeList: list[str] | None = None,
    imageSizeType: int | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    if num is not None and not 1 <= num <= 20:
        return None, "num 必须在 1 到 20 之间。"
    if aiType is not None and aiType not in {0, 1, 2}:
        return None, "aiType 仅支持 0、1、2。"
    if r18Type is not None and r18Type not in {0, 1}:
        return None, "r18Type 仅支持 0、1。"
    if imageSizeType is not None and imageSizeType not in {1, 2, 3}:
        return None, "imageSizeType 仅支持 1、2、3。"
    if dateAfter is not None and dateBefore is not None and dateAfter > dateBefore:
        return None, "dateAfter 不能大于 dateBefore。"

    cleaned_pid, pid_error = _clean_positive_int_list(pid, "pid")
    if pid_error:
        return None, pid_error

    cleaned_uid, uid_error = _clean_positive_int_list(uid, "uid")
    if uid_error:
        return None, uid_error

    cleaned_size_list, size_error = _clean_size_list(sizeList)
    if size_error:
        return None, size_error

    payload: dict[str, Any] = {}
    for key, value in {
        "num": num,
        "pid": cleaned_pid,
        "uid": cleaned_uid,
        "author": author.strip() if isinstance(author, str) and author.strip() else None,
        "proxy": proxy.strip() if isinstance(proxy, str) and proxy.strip() else None,
        "aiType": aiType,
        "r18Type": r18Type,
        "dateAfter": dateAfter,
        "dateBefore": dateBefore,
        "sizeList": cleaned_size_list,
        "imageSizeType": imageSizeType,
    }.items():
        if value is not None:
            payload[key] = value

    return payload, None


def normalize_mossia_pixiv_tags(tags_list: Any) -> list[dict[str, str | None]]:
    if not isinstance(tags_list, list):
        return []

    normalized_tags: list[dict[str, str | None]] = []
    for tag in tags_list:
        if not isinstance(tag, dict):
            continue

        tag_name = tag.get("tagName")
        if not isinstance(tag_name, str) or not tag_name.strip():
            continue

        tag_en = tag.get("tagEn")
        normalized_tags.append(
            {
                "tagName": tag_name.strip(),
                "tagEn": tag_en.strip() if isinstance(tag_en, str) and tag_en.strip() else None,
            }
        )
    return normalized_tags


def normalize_mossia_pixiv_urls(urls_list: Any) -> dict[str, str]:
    if not isinstance(urls_list, list):
        return {}

    normalized_urls: dict[str, str] = {}
    for url_info in urls_list:
        if not isinstance(url_info, dict):
            continue

        url_size = url_info.get("urlSize")
        url = url_info.get("url")
        if isinstance(url_size, str) and url_size.strip() and isinstance(url, str) and url.strip():
            normalized_urls[url_size.strip()] = url.strip()
    return normalized_urls


def normalize_mossia_pixiv_item(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    return {
        "pid": item.get("pid"),
        "uid": item.get("uid"),
        "title": item.get("title"),
        "author": item.get("author"),
        "width": item.get("width"),
        "height": item.get("height"),
        "ext": item.get("ext"),
        "aiType": item.get("aiType"),
        "pcreateDate": item.get("pcreateDate"),
        "puploadDate": item.get("puploadDate"),
        "tagsList": normalize_mossia_pixiv_tags(item.get("tagsList")),
        "urlsList": normalize_mossia_pixiv_urls(item.get("urlsList")),
    }


def normalize_mossia_pixiv_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return build_mossia_pixiv_error("RESPONSE_FORMAT_ERROR", "Mossia Pixiv API 响应格式异常: 顶层结果不是对象。")

    data = payload.get("data")
    if data is None:
        normalized_data: list[dict[str, Any]] = []
    elif isinstance(data, list):
        normalized_data = []
        for item in data:
            normalized_item = normalize_mossia_pixiv_item(item)
            if normalized_item is not None:
                normalized_data.append(normalized_item)
    else:
        return build_mossia_pixiv_error("RESPONSE_FORMAT_ERROR", "Mossia Pixiv API 响应格式异常: data 字段不是数组。")

    return {
        "success": bool(payload.get("success")),
        "errCode": payload.get("errCode"),
        "message": payload.get("message"),
        "data": normalized_data,
    }


def fetch_mossia_pixiv_image(
    num: int | None = None,
    pid: list[int] | None = None,
    uid: list[int] | None = None,
    author: str | None = None,
    proxy: str | None = None,
    aiType: int | None = None,
    r18Type: int | None = None,
    dateAfter: int | None = None,
    dateBefore: int | None = None,
    sizeList: list[str] | None = None,
    imageSizeType: int | None = None,
) -> dict[str, Any]:
    payload, error_message = build_mossia_pixiv_payload(
        num=num,
        pid=pid,
        uid=uid,
        author=author,
        proxy=proxy,
        aiType=aiType,
        r18Type=r18Type,
        dateAfter=dateAfter,
        dateBefore=dateBefore,
        sizeList=sizeList,
        imageSizeType=imageSizeType,
    )
    if error_message:
        return build_mossia_pixiv_error("PARAM_ERROR", error_message)

    session = create_mossia_pixiv_session()
    try:
        if payload:
            response = session.post(MOSSIA_PIXIV_API_URL, json=payload, timeout=MOSSIA_TIMEOUT, verify=False)
        else:
            response = session.get(MOSSIA_PIXIV_API_URL, timeout=MOSSIA_TIMEOUT, verify=False)
        response.raise_for_status()
    except requests.HTTPError as exc:
        return build_mossia_pixiv_error("REQUEST_ERROR", format_mossia_pixiv_request_error(exc))
    except requests.RequestException as exc:
        return build_mossia_pixiv_error("REQUEST_ERROR", format_mossia_pixiv_request_error(exc))

    try:
        response_payload = response.json()
    except ValueError:
        return build_mossia_pixiv_error("RESPONSE_FORMAT_ERROR", "Mossia Pixiv API 响应格式异常: 返回内容不是合法 JSON。")

    return normalize_mossia_pixiv_response(response_payload)


@tool(
    args_schema=MossiaPixivImageInput,
    description="从 Mossia Pixiv 图源获取图片信息，支持随机获取和结构化筛选，仅返回作品元数据与可选尺寸图片链接。",
)
def get_mossia_pixiv_image(
    num: int | None = None,
    pid: list[int] | None = None,
    uid: list[int] | None = None,
    author: str | None = None,
    proxy: str | None = None,
    aiType: int | None = None,
    r18Type: int | None = None,
    dateAfter: int | None = None,
    dateBefore: int | None = None,
    sizeList: list[str] | None = None,
    imageSizeType: int | None = None,
) -> dict[str, Any]:
    """从 https://api.mossia.top/duckMo 获取 Pixiv 图源作品信息。"""
    return fetch_mossia_pixiv_image(
        num=num,
        pid=pid,
        uid=uid,
        author=author,
        proxy=proxy,
        aiType=aiType,
        r18Type=r18Type,
        dateAfter=dateAfter,
        dateBefore=dateBefore,
        sizeList=sizeList,
        imageSizeType=imageSizeType,
    )
