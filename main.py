import datetime
import random
import re
import time

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

Token = ""

# Слова триггеры
TriggerWordForStickers = ["чачлык", "евстегней"]

# Стикеры...
Stickers = [18791, 14234, 14213, 13849]

# Время в минутах ожидания след. срабатывания
TimeWait = 5

# Триггер слово для ой-бота
TriggerWordForDelete = "ой"

# Триггер слово для транслита клавиатуры
TriggerWordForTranslate = "перевод"

TriggerWordForEveryone = [
    # Триггер слово для @everyone
    "@все",

    # То что будет в сообщении
    "сюда блин"
]

LastSend = datetime.datetime.now()

vk_session = vk_api.VkApi(token=Token.strip())
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

user_id = vk.users.get()[0]["id"]

while True:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:

                message = event.text.lower()
                for x in TriggerWordForStickers:
                    find = re.search(r"(\[id" + str(user_id) + r"\|(?:|@).{2,15}\])|(\s?" + str(x) + r"\s?)",
                                     message.lower())
                    if find is not None and LastSend is not None:
                        if datetime.datetime.now() >= LastSend:
                            try:
                                time.sleep(.3)
                                vk.messages.send(peer_id=event.peer_id, sticker_id=random.choice(Stickers),
                                                 random_id=random.randint(-1000000, 1000000))
                            except Exception as s:
                                print(s)
                            finally:
                                LastSend = datetime.datetime.now() + datetime.timedelta(minutes=TimeWait)
                        else:
                            print("Осталось", LastSend - datetime.datetime.now())
                        break

                if (message.startswith(TriggerWordForDelete)
                        and event.from_chat
                        and event.user_id == user_id):

                    message = message.replace(TriggerWordForDelete, '')

                    if len(message) is 0:
                        message = str(abs(len(message) + 1))
                    if message.isdigit():
                        try:
                            response = vk.messages.getHistory(peer_id=event.peer_id)
                        except Exception as s:
                            print(s)
                            continue
                        count = 0
                        count_max = int(message) + 1
                        to_del = []
                        for x in response.get('items', []):

                            if x['from_id'] == user_id:
                                to_del.append(x['id'])
                                count += 1
                            if count >= count_max:
                                break
                        if len(to_del) != 0:
                            try:
                                vk.messages.delete(message_ids=to_del, delete_for_all=1)
                            except Exception as s:
                                print(s)

                if (message == TriggerWordForEveryone[0]
                        and event.from_chat
                        and event.user_id == user_id):
                    response = vk.messages.getChat(chat_id=event.chat_id)
                    users = response['users']
                    text = TriggerWordForEveryone[1]
                    for x in users:
                        if x < 0:
                            pass
                        else:
                            text += f"[id{x}|&#8300;] "  # &#8300;
                    vk.messages.edit(peer_id=event.peer_id, message_id=event.message_id,
                                     message=text)
                    continue

                if (message == TriggerWordForTranslate
                        and event.from_chat
                        and event.user_id == user_id):
                    eng_chars = "~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
                    rus_chars = "ё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
                    trans_table = dict(zip(eng_chars + rus_chars, rus_chars + eng_chars))
                    swapped_message = ""
                    for c in event.text:
                        try:
                            swapped_message += trans_table.get(c, c)
                        except Exception as s:
                            print(s)
                    print(swapped_message)
    except Exception as s:
        print(s)
