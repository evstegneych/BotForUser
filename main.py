import vk_api
import re
from vk_api.longpoll import VkLongPoll, VkEventType
from config import config

vk_session = vk_api.VkApi(token=config["token"])
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

info = vk.users.get()
print(info)

for event in longpoll.listen():
    print(event.text)