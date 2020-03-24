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
TriggerWordForTranslate = "рас"

TriggerWordForEveryone = [
    # Триггер слово для @everyone
    "@все",

    # То что будет в сообщении
    "сюда блин"
]

vk_session = vk_api.VkApi(token=Token.strip())
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

user_id = vk.users.get()[0]["id"]
LastSend = datetime.datetime.now()
LastMyMessage = {}


def CheckMarkUser(message):
    finder = re.search(r"\[id" + str(user_id) + r"\|(?:|@).{2,15}\]", message)
    if finder is not None:
        return True
    finder = re.search(r"\s?(" + str("|".join(TriggerWordForStickers)) + r")\s?", message)
    if finder is not None:
        return True
    return False


while True:
    try:
        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW:
                    if not event.text:
                        continue
                    message = event.message.lower()
                    find = CheckMarkUser(message)
                    if find and LastSend is not None:
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

                    if event.from_chat and event.user_id == user_id:

                        if message.startswith(TriggerWordForDelete):
                            message_ = message.replace(TriggerWordForDelete, '')

                            if len(message_) is 0:
                                message_ = str(abs(len(message_) + 1))
                            if message_.isdigit():
                                try:
                                    response = vk.messages.getHistory(peer_id=event.peer_id)
                                except Exception as s:
                                    print(s)
                                    continue
                                count = 0
                                count_max = int(message_) + 1
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

                        elif message == TriggerWordForEveryone[0]:
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

                        elif message == TriggerWordForTranslate:
                            message_ = LastMyMessage.get(event.peer_id)
                            if message_ is not None:
                                response = vk.messages.getById(message_ids=message_)
                                msg = response.get("items", [{}])[0].get("text")
                                if msg is not None:
                                    eng_chars = "~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
                                    rus_chars = "ё!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
                                    trans_table = dict(zip(eng_chars + rus_chars, rus_chars + eng_chars))
                                    swapped_message = ""
                                    for c in msg:
                                        try:
                                            swapped_message += trans_table.get(c, c)
                                        except Exception as s:
                                            print(s)
                                    try:
                                        vk.messages.edit(peer_id=event.peer_id, message=swapped_message,
                                                         message_id=message_)
                                        vk.messages.delete(message_ids=event.message_id, delete_for_all=1)
                                    except Exception as s:
                                        print(s)

                        else:
                            LastMyMessage.update({event.peer_id: event.message_id})

            except Exception as s:
                print(s)
                print(event.raw)

    except Exception as s:
        print(s)
