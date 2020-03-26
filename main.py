import datetime
import random
import re
import time
from threading import Thread

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
    # &#8300; Пустой символ
    "&#8300;"
]

# Триггер слово для начала розыгрыша
TriggerWordForContest = "роз"

vk_session = vk_api.VkApi(token=Token.strip())
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

user_info = vk.users.get()[0]
user_id = user_info["id"]
user_name = f"{user_info['first_name']} {user_info['last_name']}"
LastSend = datetime.datetime.now()
LastMyMessage = {}
Contests = {}

# Не изменять! Возможны критические ошибки!
ContestText = f"<<{user_name}>> устроил конкурс!\n" \
              "Времени осталось: {}\n" \
              "Для участия напиши: {}\n" \
              "Участники: {}"
ContestTextWin = "Встречайте победителя!\n" \
                 "Им стал: {}"


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours, minutes, seconds


def CheckMarkUser(for_finder):
    finder = re.search(r"\s?(" + str("|".join(TriggerWordForStickers)) + r")\s?", for_finder)
    if finder is not None:
        return True
    finder = re.search(r"\[id" + str(user_id) + r"\|(?:|@).{2,15}\]", for_finder)
    if finder is not None:
        return True
    return False


def MessageEdit(message_id, t, peer_id):
    try:
        vk.messages.edit(peer_id=peer_id,
                         message_id=message_id,
                         message=t)
    except Exception as s:
        print(s)


def GetNameUsers(user_ids):
    names = []
    resp = vk.users.get(user_ids=user_ids)
    for x in resp:
        names.append(f"@id{x['id']}({x['first_name']})")
    return ", ".join(names)


def ContestsControl():
    while True:
        try:
            con = Contests.copy()
            for c, v in con.items():
                t = v["time"] - datetime.datetime.now()
                hours, minutes, seconds = convert_timedelta(t)
                if not minutes and seconds:
                    minutes = 1
                check_time = t.total_seconds() <= 20
                if check_time:
                    hours = 0
                    minutes = 0
                MessageEdit(v["message_id"],
                            ContestText.format(
                                f"{hours} ч. {minutes} мин.",
                                v["trigger"],
                                GetNameUsers(v["users"])),
                            v["peer_id"])
                if check_time:
                    vk.messages.send(peer_id=v["peer_id"],
                                     message=ContestTextWin.format(GetNameUsers([random.choice(v["users"])])),
                                     random_id=random.randint(-1000000, 1000000))
                    del Contests[c]
        except Exception as s:
            print("Поток Конкурсов", s)
        finally:
            time.sleep(40)


Thread(target=ContestsControl, args=[], daemon=True).start()
print("Бот запущен")
while True:
    try:
        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW:
                    if not event.text:
                        continue
                    message = event.message.lower()

                    contest = None
                    for (peer_id, value) in Contests.items():
                        if event.text == value["trigger"] and value["peer_id"] == event.peer_id:
                            contest = value
                            break
                    if contest is not None:
                        if event.user_id not in contest["users"]:
                            Contests[contest["peer_id"]]["users"].append(event.user_id)
                            hours, minutes, seconds = convert_timedelta(contest["time"] - datetime.datetime.now())
                            MessageEdit(contest["message_id"],
                                        ContestText.format(
                                            f"{hours} ч. {minutes} мин.",
                                            contest["trigger"],
                                            GetNameUsers(contest["users"])),
                                        contest["peer_id"])

                    find = CheckMarkUser(message)
                    if find and LastSend is not None and event.user_id != user_id:
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

                        if message.startswith(TriggerWordForContest + " "):
                            if Contests.get(event.peer_id) is not None:
                                continue
                            message_ = event.text[len(TriggerWordForContest) + 1:]
                            args = message_.split()
                            if len(args) >= 2:
                                time_ = args[0]
                                if not time_.isdigit():
                                    continue
                                time_ = datetime.timedelta(minutes=int(time_))
                                hours, minutes, seconds = convert_timedelta(time_)
                                trigger = args[1:]
                                text = ContestText.format(f"{hours} ч. {minutes} мин.",
                                                          " ".join(trigger), "")
                                message_id = vk.messages.send(peer_id=event.peer_id,
                                                              message=text,
                                                              random_id=random.randint(-1000000, 1000000))
                                vk.messages.delete(message_ids=event.message_id, delete_for_all=1)
                                Contests.update(
                                    {
                                        event.peer_id:
                                            {
                                                "peer_id": event.peer_id,
                                                "users": [],
                                                "message_id": message_id,
                                                "trigger": " ".join(trigger),
                                                "time": datetime.datetime.now() + time_
                                            }
                                    }
                                )

                            del message_, args

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
                            text = "@everyone "
                            for x in users:
                                if x < 0:
                                    pass
                                else:
                                    text += f"[id{x}|{TriggerWordForEveryone[1]}] "  # &#8300;
                            vk.messages.edit(peer_id=event.peer_id, message_id=event.message_id,
                                             message=text)
                            continue

                        elif message == TriggerWordForTranslate:
                            message_ = LastMyMessage.get(event.peer_id)
                            if message_ is not None:
                                response = vk.messages.getById(message_ids=message_)
                                msg = response.get("items", [{}])[0]
                                text = msg.get("text")
                                if text is not None:
                                    eng_chars = "~!@#%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
                                    rus_chars = "ё!\"№%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,"
                                    trans_table = dict(zip(eng_chars + rus_chars, rus_chars + eng_chars))
                                    swapped_message = ""
                                    for c in text:
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
                raise

    except Exception as s:
        print(s)
        raise
