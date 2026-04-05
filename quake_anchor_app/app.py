
import base64
import imghdr
import json
import os
from typing import Tuple

from flask import Flask, jsonify, render_template, request
from openai import OpenAI

app = Flask(__name__)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """你是一個台灣新聞台的地震快訊文稿助手。
你的工作是讀取中央氣象署地震速報圖卡，輸出：
1. 主播可直接朗讀的新聞文稿
2. 一行新聞標題

規則：
- 完全依照圖片內容，不自行補充未出現在圖上的資訊。
- 日期、時間、地點、規模、深度、各地震度都要準確。
- 文稿語氣要像台灣電視新聞主播，流暢、自然、正式。
- 若圖片內出現「臺」字，輸出時保留為「臺」。
- 標題格式盡量接近：『7:19臺南楠西規模4.3地震　最大震度4級』
- 文稿格式盡量接近：
  『最新消息，根據氣象署最新資訊，今天3月16號上午7點19分發生芮氏規模4.3地震，地震深度7.5公里，震央位於臺南市政府東北方40.1公里，位於臺南市楠西區。
    各地最大震度方面，臺南市曾文測得4級，嘉義縣大埔為3級……』
- 若時間是凌晨 0:00–5:59，文稿可用「凌晨」；06:00–11:59 用「上午」；12:00–17:59 用「下午」；18:00–23:59 用「晚間」。
- 若有多個同震度地點，請用頓號或逗號自然串接。
- 僅輸出 JSON，不要加任何前後說明。
"""

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "earthquake_news_output",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "script": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["title", "script", "notes"]
        },
        "strict": True
    }
}


def image_to_data_url(file_storage) -> str:
    raw = file_storage.read()
    if not raw:
        raise ValueError("上傳的圖片內容是空的。")

    image_type = imghdr.what(None, h=raw)
    if image_type not in {"jpeg", "png", "gif", "webp"}:
        # Fallback to jpeg; many browser uploads are jpg
        image_type = "jpeg"

    b64 = base64.b64encode(raw).decode("utf-8")
    return f"data:image/{image_type};base64,{b64}"


def extract_json_text(response) -> str:
    # Works with current OpenAI Python SDK response objects
    if hasattr(response, "choices") and response.choices:
        message = response.choices[0].message
        if hasattr(message, "content") and isinstance(message.content, str):
            return message.content
    # Fallback: try generic dict conversion
    try:
        as_dict = response.model_dump()
        return as_dict["choices"][0]["message"]["content"]
    except Exception as exc:
        raise ValueError(f"無法解析模型回傳內容：{exc}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"error": "請先上傳一張地震速報圖卡。"}), 400

    image = request.files["image"]

    if not os.getenv("OPENAI_API_KEY"):
        return jsonify({"error": "伺服器尚未設定 OPENAI_API_KEY。"}), 500

    try:
        data_url = image_to_data_url(image)

        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.2,
            response_format=RESPONSE_FORMAT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "請根據這張中央氣象署地震速報圖卡，產出主播文稿與標題。"},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ]
        )

        text = extract_json_text(completion)
        result = json.loads(text)

        return jsonify({
            "title": result["title"].strip(),
            "script": result["script"].strip(),
            "notes": result.get("notes", "").strip()
        })

    except Exception as exc:
        return jsonify({"error": f"生成失敗：{str(exc)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)
