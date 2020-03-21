import time
import vk_api
import re
import random
import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from config import config

triggers = ["чачлык", "маккарди лох"]
Stickers = [18791]
LastSend = datetime.datetime.now()

vk_session = vk_api.VkApi(token=config["token"])
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

user_id = vk.users.get()[0]["id"]

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        for x in triggers:
            find = re.search("(\[id" + str(user_id) + "\|(?:|@).{2,15}\])|(\s{0,1}" + str(x) + "\s{0,1})",
                             event.text.lower())
            if find is not None and LastSend is not None:
                if datetime.datetime.now() >= LastSend:
                    try:
                        time.sleep(.3)
                        vk.messages.send(peer_id=event.peer_id, sticker_id=random.choice(Stickers),
                                         random_id=random.randint(-1000000, 1000000))
                    except Exception as s:
                        print(s)
                    finally:
                        LastSend = datetime.datetime.now() + datetime.timedelta(minutes=5)
                else:
                    print("Осталось", LastSend - datetime.datetime.now())
                break
