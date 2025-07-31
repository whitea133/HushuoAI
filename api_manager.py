import base64
import os
import shutil
import tempfile
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

# 单图片功能
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

# 多图片功能
def images_batchFn(image_paths: List[str],
                   prompt: str = "请根据下面文字和图片回答",
                   messages: list = []) -> str:
    """
    一次把多张图片 + 一段文字打包发给模型
    """
    content = [{"type": "text", "text": prompt}]
    for p in image_paths:
        b64 = image_to_base64(p)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
        })

    messages.append({"role": "user", "content": content})
    resp = _client.chat.completions.create(model=cfg.MODEL_ID, messages=messages)
    messages.append({"role": "assistant", "content": resp.choices[0].message.content})
    return resp.choices[0].message.content

# 单视频功能
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
        shutil.rmtree(".tmp", ignore_errors=True)

# 多视频统一描述
def video_batchFn(video_paths: List[str],
                  prompt: str = "请根据下面文字和多个视频内容回答",
                  max_frames_per_video: int = 5,
                  messages: list = []) -> str:
    """
    一次性把多个视频的所有关键帧 + 文字打包发送
    """
    content = [{"type": "text", "text": prompt}]
    temp_dirs = []

    try:
        for vpath in video_paths:
            # 每个视频独立目录，避免文件名冲突
            tmp = tempfile.mkdtemp(prefix="video_frames_")
            temp_dirs.append(tmp)

            frames = extract_keyframes(
                vpath,
                output_dir=tmp,
                max_frames=max_frames_per_video
            )
            for frame in frames:
                b64 = image_to_base64(frame)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
                })

        messages.append({"role": "user", "content": content})
        resp = _client.chat.completions.create(model=cfg.MODEL_ID, messages=messages)
        messages.append({"role": "assistant", "content": resp.choices[0].message.content})
        return resp.choices[0].message.content

    finally:
        # 清理所有临时目录
        for td in temp_dirs:
            shutil.rmtree(td, ignore_errors=True)

# ---------- 统一多模态接口 ----------
def multimodal(text: str, imgs: List[str], videos: List[str], messages: list) -> str:
    """
    把文字 + 所有图片 + 所有视频关键帧一次性打包
    """
    content = [{"type": "text", "text": text}]
    temp_dirs = []

    try:
        # 1. 图片直接转
        for img in imgs:
            b64 = image_to_base64(img)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
            })

        # 2. 视频抽帧
        for vid in videos:
            tmp = tempfile.mkdtemp(prefix="vframes_")
            temp_dirs.append(tmp)
            frames = extract_keyframes(vid, output_dir=tmp, max_frames=5)
            for f in frames:
                b64 = image_to_base64(f)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
                })

        messages.append({"role": "user", "content": content})
        resp = _client.chat.completions.create(model=cfg.MODEL_ID, messages=messages)
        messages.append({"role": "assistant", "content": resp.choices[0].message.content})
        return resp.choices[0].message.content

    finally:
        for td in temp_dirs:
            shutil.rmtree(td, ignore_errors=True)

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