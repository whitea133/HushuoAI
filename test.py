from api_manager import textFn, imageFn, videoFn, generate_image
import config as cfg
# 初始化模型role
messages_record = [cfg.MODEL_ROLE]
print(messages_record)
# a = textFn("你好你好，我在测试接口！", messages=messages_record)
# print(a)

# print(textFn("我上一句问了你什么？", messages=messages_record))

# print(textFn("你上一句说了什么？", messages=messages_record))

# print(textFn("你还记得你是什么专家吗", messages=messages_record))
# b = imageFn('./xiaohuolong.jpg', "这是什么动漫的图片", messages=messages_record)
# print(b)

# c = videoFn('./vid.MP4', "这段视频的人在干什么？并且回答你是谁", messages=messages_record)
# print(c)

generate_image("生成一张小猫的图片", "256x256", messages=messages_record)
