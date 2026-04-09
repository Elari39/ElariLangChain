import unittest
from unittest.mock import MagicMock, patch

import requests

import agent_tools
from mossia_pixiv_tool import (
    MOSSIA_PIXIV_API_URL,
    MOSSIA_TIMEOUT,
    build_mossia_pixiv_payload,
    fetch_mossia_pixiv_image,
    get_mossia_pixiv_image,
)


class MossiaPixivToolTests(unittest.TestCase):
    def test_build_payload_ignores_none_and_empty_values(self) -> None:
        payload, error = build_mossia_pixiv_payload(
            num=3,
            pid=[],
            uid=None,
            author="  artist  ",
            proxy="",
            sizeList=["original", " small ", ""],
        )

        self.assertIsNone(error)
        self.assertEqual(
            payload,
            {
                "num": 3,
                "author": "artist",
                "sizeList": ["original", "small"],
            },
        )

    def test_invalid_num_returns_param_error(self) -> None:
        result = fetch_mossia_pixiv_image(num=21)

        self.assertFalse(result["success"])
        self.assertEqual(result["errCode"], "PARAM_ERROR")
        self.assertIn("num", result["message"])

    @patch("mossia_pixiv_tool.requests.Session")
    def test_no_filters_uses_get(self, session_cls: MagicMock) -> None:
        session = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "success": True,
            "errCode": "0",
            "message": "ok",
            "data": [],
        }
        session.get.return_value = response
        session_cls.return_value = session

        result = fetch_mossia_pixiv_image()

        session.get.assert_called_once_with(MOSSIA_PIXIV_API_URL, timeout=MOSSIA_TIMEOUT, verify=False)
        session.post.assert_not_called()
        self.assertTrue(result["success"])

    @patch("mossia_pixiv_tool.requests.Session")
    def test_filters_use_post_and_normalize_response(self, session_cls: MagicMock) -> None:
        session = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "success": True,
            "errCode": "0",
            "message": "ok",
            "data": [
                {
                    "pid": 100,
                    "uid": 200,
                    "title": "sample",
                    "author": "artist",
                    "width": 1200,
                    "height": 800,
                    "ext": "png",
                    "aiType": 1,
                    "pcreateDate": 1710000000000,
                    "puploadDate": 1710001000000,
                    "tagsList": [
                        {"tagName": "猫", "tagEn": "cat"},
                        {"tagName": "风景", "tagEn": ""},
                    ],
                    "urlsList": [
                        {"urlSize": "original", "url": "https://example.com/original.png"},
                        {"urlSize": "small", "url": "https://example.com/small.jpg"},
                    ],
                }
            ],
        }
        session.post.return_value = response
        session_cls.return_value = session

        result = fetch_mossia_pixiv_image(num=2, author="artist", sizeList=["original", "small"])

        session.post.assert_called_once_with(
            MOSSIA_PIXIV_API_URL,
            json={"num": 2, "author": "artist", "sizeList": ["original", "small"]},
            timeout=MOSSIA_TIMEOUT,
            verify=False,
        )
        normalized_item = result["data"][0]
        self.assertEqual(normalized_item["pid"], 100)
        self.assertEqual(
            normalized_item["tagsList"],
            [
                {"tagName": "猫", "tagEn": "cat"},
                {"tagName": "风景", "tagEn": None},
            ],
        )
        self.assertEqual(
            normalized_item["urlsList"],
            {
                "original": "https://example.com/original.png",
                "small": "https://example.com/small.jpg",
            },
        )

    @patch("mossia_pixiv_tool.requests.Session")
    def test_missing_tags_and_urls_are_normalized_to_empty_collections(self, session_cls: MagicMock) -> None:
        session = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "success": True,
            "errCode": "0",
            "message": "ok",
            "data": [
                {
                    "pid": 1,
                    "uid": 2,
                    "title": "sample",
                    "author": "artist",
                }
            ],
        }
        session.get.return_value = response
        session_cls.return_value = session

        result = fetch_mossia_pixiv_image()

        self.assertEqual(result["data"][0]["tagsList"], [])
        self.assertEqual(result["data"][0]["urlsList"], {})

    @patch("mossia_pixiv_tool.requests.Session")
    def test_http_error_returns_request_error(self, session_cls: MagicMock) -> None:
        session = MagicMock()
        response = MagicMock()
        response.status_code = 502
        response.reason = "Bad Gateway"
        session.get.return_value = response
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        session_cls.return_value = session

        result = fetch_mossia_pixiv_image()

        self.assertFalse(result["success"])
        self.assertEqual(result["errCode"], "REQUEST_ERROR")
        self.assertIn("HTTP 502 Bad Gateway", result["message"])

    @patch("mossia_pixiv_tool.requests.Session")
    def test_invalid_json_returns_response_format_error(self, session_cls: MagicMock) -> None:
        session = MagicMock()
        response = MagicMock()
        response.json.side_effect = ValueError("invalid json")
        session.get.return_value = response
        session_cls.return_value = session

        result = fetch_mossia_pixiv_image()

        self.assertFalse(result["success"])
        self.assertEqual(result["errCode"], "RESPONSE_FORMAT_ERROR")
        self.assertIn("合法 JSON", result["message"])

    def test_tool_schema_exposes_structured_fields(self) -> None:
        schema = get_mossia_pixiv_image.args_schema.model_json_schema()

        self.assertIn("num", schema["properties"])
        self.assertIn("sizeList", schema["properties"])
        self.assertNotIn("params", schema["properties"])

    @patch("agent_tools.PythonREPLTool")
    @patch("agent_tools.load_tools")
    def test_build_tools_registers_structured_pixiv_tool(
        self,
        load_tools_mock: MagicMock,
        python_repl_tool_mock: MagicMock,
    ) -> None:
        load_tools_mock.return_value = ["arxiv-tool", "wikipedia-tool"]
        python_repl_tool_mock.return_value = "python-repl-tool"

        tools = agent_tools.build_tools()

        self.assertIn(get_mossia_pixiv_image, tools)


if __name__ == "__main__":
    unittest.main()
