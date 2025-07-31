# run_receive.py
import os
import time
import threading
import tempfile
import shutil
import pythoncom
from typing import List
from wxauto import WeChat
import config as cfg
from volcenginesdkarkruntime import Ark
from utils.image_utils import image_to_base64
from utils.video_utils import extract_keyframes

_client = Ark(api_key=cfg.ARK_API_KEY)
SAVE_DIR = "received_images"
os.makedirs(SAVE_DIR, exist_ok=True)

messages_record = [cfg.MODEL_ROLE]
buffer_lock = threading.Lock()
buffer_msgs = []          # 元素: {"type": "text|image|video", "content": str, "ts": float}

# ---------------- 监听线程 ----------------
def listener(nickname: str):
    pythoncom.CoInitialize()
    wx = WeChat()
    wx.ChatWith(nickname)

    def on_message(msg, chat):
        now = time.time()
        if msg.type == 'text':
            with buffer_lock:
                buffer_msgs.append({"type": "text", "content": msg.content, "ts": now})
                print("[实时文字]", msg.content)

        elif msg.type == 'image':
            path = msg.download(dir_path=SAVE_DIR)
            if path:
                with buffer_lock:
                    buffer_msgs.append({"type": "image", "content": path, "ts": now})
                    print("[实时图片]", path)

        elif msg.type == 'video':
            path = msg.download(dir_path=SAVE_DIR)
            if path:
                with buffer_lock:
                    buffer_msgs.append({"type": "video", "content": path, "ts": now})
                    print("[实时视频]", path)

    wx.AddListenChat(nickname=nickname, callback=on_message)
    try:
        while True:
            time.sleep(1)
    finally:
        try:
            wx.RemoveListenChat(nickname)
        except KeyError:
            pass
        pythoncom.CoUninitialize()

# ---------------- 主循环 ----------------
def run_continuous(nickname: str, interval: int = 20):
    threading.Thread(target=listener, args=(nickname,), daemon=True).start()

    try:
        while True:
            time.sleep(interval)

            with buffer_lock:
                if not buffer_msgs:
                    print("【AI】这 20 秒内没有新消息")
                    continue

                # 按时间排序
                buffer_msgs.sort(key=lambda x: x["ts"])
                # 直接按顺序拼成 messages content
                content = []
                temp_dirs = []
                try:
                    for m in buffer_msgs:
                        if m["type"] == "text":
                            content.append({"type": "text", "text": m["content"]})
                        elif m["type"] == "image":
                            b64 = image_to_base64(m["content"])
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
                            })
                        elif m["type"] == "video":
                            tmp = tempfile.mkdtemp(prefix="vframes_")
                            temp_dirs.append(tmp)
                            frames = extract_keyframes(m["content"], output_dir=tmp, max_frames=5)
                            for f in frames:
                                b64 = image_to_base64(f)
                                content.append({
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}
                                })
                    buffer_msgs.clear()
                finally:
                    for td in temp_dirs:
                        shutil.rmtree(td, ignore_errors=True)

            # 一次性发送
            messages_record.append({"role": "user", "content": content})
            resp = _client.chat.completions.create(
                model=cfg.MODEL_ID,
                messages=messages_record
            )
            ai_reply = resp.choices[0].message.content
            messages_record.append({"role": "assistant", "content": ai_reply})

            print("********************")
            print("【AI】", ai_reply)
            print("********************")

    except KeyboardInterrupt:
        print("\n用户中断，退出监听。")

# ---------------- 运行 ----------------
if __name__ == "__main__":
    run_continuous("大号张俊杰", 20)