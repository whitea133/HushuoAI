import base64
import os
from typing import List, Literal, Optional
from volcenginesdkarkruntime import Ark
from utils.image_utils import image_to_base64
from utils.video_utils import extract_keyframes, Strategy
import config as cfg

_client = Ark(api_key=cfg.ARK_API_KEY)

# def _build_payload(messages: List[dict]) -> List[dict]:
#     return messages

# 对话功能
def textFn(text: str, messages: list = []) -> str:
    messages.append({"role": "user", "content": text})
    resp = _client.chat.completions.create(model=cfg.MODEL_ID, messages=messages)
    messages.append({"role": "assistant", "content": resp.choices[0].message.content})
    return resp.choices[0].message.content

# 图片功能
def imageFn(image_path: str, prompt: str = "描述这张图片", messages: list = []) -> str:
    b64 = image_to_base64(image_path)
    append_text = {
        "type": "text",
        "text": prompt
    }
    append_img = {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
    }
    messages.append({"role": "user", "content": [append_text, append_img]})
    resp = _client.chat.completions.create(model=cfg.MODEL_ID, messages=messages)
    messages.append({"role": "assistant", "content": resp.choices[0].message.content})
    return resp.choices[0].message.content

# 视频功能
def videoFn(video_path: str, prompt: str = "描述这段视频", messages: list = []) -> str:
    # messages.append({"role": "user", "content": prompt})
    content = [
        {"type": "text", "text": prompt}
    ]
    frames = extract_keyframes(video_path, output_dir=".tmp", max_frames=15)
    try:
        for frame in frames:
            content.append(
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_to_base64(frame)}",
                        "detail": "low"
                    }
                }    
            )
        messages.append({"role": "user", "content": content})
        resp = _client.chat.completions.create(model=cfg.MODEL_ID, messages=messages)
        messages.append({"role": "assistant", "content": resp.choices[0].message.content})
        return resp.choices[0].message.content
    finally:
        import shutil
        shutil.rmtree(".tmp", ignore_errors=True)
        
def generate_image(prompt: str, size: str = "1024x1024", messages: list = []) -> str:
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": cfg.MODEL_ID,  # 火山文生图模型
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json"
    }
    resp = _client.images.generate(**payload)
    b64_data = resp.data[0].b64_json

    if not messages:
        return b64_data

    os.makedirs(os.path.dirname("generated_image.png"), exist_ok=True)
    with open("generated_image.png", "wb") as f:
        f.write(base64.b64decode(b64_data))
    return "generated_image.png"