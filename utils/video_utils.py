import os
import cv2
from typing import List, Optional
import time # to count time
import shutil # 文件操作库，用于删除目录
from enum import Enum # 导入枚举库,用于定义抽帧策略

# 定义抽帧策略枚举类
class Strategy(Enum):
    # 固定间隔抽帧策略，例如每1秒抽一帧
    CONSTANT_INTERVAL = "constant_interval"
    # 均匀间隔抽帧策略，根据设定的最大帧数均匀从视频全长度抽取
    EVEN_INTERVAL = "even_interval"

def extract_keyframes(
    video_path: str,
    output_dir: str,
    strategy: Strategy = Strategy.EVEN_INTERVAL,
    interval_sec: float = 1.0,
    max_frames: int = 10,
    name_pattern: str = "frame_{:04d}.jpg"
) -> List[str]:
    """
    将视频按指定策略抽帧，并把关键帧保存为图片。
    ----
    video_path : str
        待抽帧的本地视频文件完整路径。
    output_dir : str
        关键帧图片保存目录；若已存在，会被清空后重建。
    strategy : Strategy, optional
        抽帧策略，默认 Strategy.EVEN_INTERVAL。
        - CONSTANT_INTERVAL：按固定时间间隔（interval_sec）抽帧；
        - EVEN_INTERVAL：在视频全长内均匀抽取 max_frames 帧。
    interval_sec : float, optional
        仅在 strategy=CONSTANT_INTERVAL 时生效，表示每隔多少秒抽取一帧。
    max_frames : int, optional
        最大抽取帧数；达到此数量或视频结束时停止。
    name_pattern : str, optional
        关键帧文件命名模板，支持 format 占位符；默认 "frame_{:04d}.jpg"。
    ----
    List[str]
        已保存的关键帧图片完整路径列表，按抽取顺序排列。
    """
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    step = (
        int(fps * interval_sec)
        if strategy == Strategy.CONSTANT_INTERVAL
        else max(1, total // max_frames)
    )

    idx, frames = 0, []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            path = os.path.join(output_dir, name_pattern.format(len(frames)))
            cv2.imwrite(path, frame)
            frames.append(path)
            if len(frames) >= max_frames:
                break
        idx += 1
    cap.release()
    return frames