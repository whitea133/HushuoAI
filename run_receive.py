# run_receive.py
import os
import time
import threading
import pythoncom
from wxauto import *
from api_manager import textFn, images_batchFn
import config as cfg

# ---------------- 全局变量 ----------------
messages_record = [cfg.MODEL_ROLE]
buffer_lock = threading.Lock()

buffer_text = []          # 指定时间段内文字
buffer_imgs = []          # 指定时间段内图片路径
SAVE_DIR = "received_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------- 监听线程 ----------------
def listener(nickname: str):
    pythoncom.CoInitialize()
    wx = WeChat()
    wx.ChatWith(nickname)

    def on_message(msg, chat):
        if msg.type == 'text':
            with buffer_lock:
                buffer_text.append(msg.content)
                print("[实时文字]", msg.content)

        elif msg.type == 'image':
            path = msg.download(dir_path=SAVE_DIR)
            if path:
                with buffer_lock:
                    buffer_imgs.append(path)
                    print("[实时图片]", path)

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
def run_continuous(nickname: str, interval: int = 15):
    threading.Thread(target=listener, args=(nickname,), daemon=True).start()

    try:
        while True:
            time.sleep(interval)

            with buffer_lock:
                text = "\n".join(buffer_text)
                imgs = buffer_imgs.copy()
                buffer_text.clear()
                buffer_imgs.clear()

            if not text and not imgs:
                print("【AI】这 15 秒内没有新消息")
                continue

            if text and not imgs:                       # 只有文字
                ai_reply = textFn(text, messages=messages_record)

            elif imgs and not text:                     # 只有图片
                prompt = ""
                ai_reply = images_batchFn(imgs, prompt=prompt, messages=messages_record)

            else:                                       # 文字 + 图片
                # prompt = "以下是用户发的文字与图片，请结合回答：\n" + text
                prompt = text
                ai_reply = images_batchFn(imgs, prompt=prompt, messages=messages_record)

            print("********************")
            print("【AI】", ai_reply)
            print("********************")

    except KeyboardInterrupt:
        print("\n用户中断，退出监听。")

# ---------------- 运行 ----------------
if __name__ == "__main__":
    run_continuous("大号张俊杰", 20)