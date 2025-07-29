# 统一放配
import os

ARK_API_KEY = os.environ.get("ARK_API_KEY")
# MODEL_ID = "doubao-1-5-vision-pro-32k-250115"
MODEL_ID = "ep-m-20250608121023-4kdn2"
MODEL_ROLE =   {
        "role": "system",
        "content": """你是一个动漫专家，认识所有动漫。""",
    }