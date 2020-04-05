import datetime
import json
import random
import re
import time
from threading import Thread

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


class Settings:
    __slots__ = ["Token", "TriggerStickers", "Stickers",
                 "TimeWait", "TriggerDelete",
                 "TriggerTranslate", "TriggerEveryone",
                 "TriggerContest", "TriggerAddStickers",
                 "filename", "_data"]

    def __init__(self, filename):
        self.filename = filename
        self._data = None

    def load(self, ):
        with open(self.filename, "r", encoding="utf-8") as file:
            self._data = json.load(file)
            for (k, v) in self._data.items():
                setattr(self, k, v)

    def save(self):
        if self._data is not None:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self._data, file, ensure_ascii=False, indent=4)

    def edit(self, _name, _value):
        self._data[_name] = _value
        setattr(self, _name, _value)

    def update(self):
        for k in self.__slots__[:-2]:
            self._data[k] = getattr(self, k)

    @property
    def get_data(self):
        return str(self._data)


setting = Settings("config.json")
setting.load()

vk_session = vk_api.VkApi(token=setting.Token)
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
    days, sec = duration.days, duration.seconds
    h = days * 24 + sec // 3600
    minute = (sec % 3600) // 60
    sec = (sec % 60)
    return h, minute, sec


def CheckMarkUser(for_finder):
    finder = re.search(r"\s?(" + str("|".join(setting.TriggerStickers)) + r")\s?", for_finder)
    if finder is not None:
        return True
    finder = re.search(r"\[id" + str(user_id) + r"\|(?:|@).{2,15}\]", for_finder)
    if finder is not None:
        return True
    return False


def MessageEdit(mid, t, peer):
    vk.messages.edit(peer_id=peer,
                     message_id=mid,
                     message=t)


def GetNameUsers(user_ids):
    names = []
    resp = vk.users.get(user_ids=user_ids)
    for u in resp:
        names.append(f"@id{u['id']}({u['first_name']})")
    return ", ".join(names)


def ContestsControl():
    while True:
        try:
            con = Contests.copy()
            for key, v in con.items():
                t = v["time"] - datetime.datetime.now()
                _hours, _minutes, _seconds = convert_timedelta(t)
                if not _minutes and _seconds:
                    _minutes = 1
                check_time = t.total_seconds() <= 20
                if check_time:
                    _hours = 0
                    _minutes = 0
                MessageEdit(v["message_id"],
                            ContestText.format(
                                f"{_hours} ч. {_minutes} мин.",
                                v["trigger"],
                                GetNameUsers(v["users"])),
                            v["peer_id"])
                if check_time:
                    vk.messages.send(peer_id=v["peer_id"],
                                     message=ContestTextWin.format(GetNameUsers([random.choice(v["users"])])),
                                     random_id=random.randint(-1000000, 1000000))
                    del Contests[key]
        except Exception as error:
            print("Поток Конкурсов:", error)
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
                        if message == value["trigger"].lower() and value["peer_id"] == event.peer_id:
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
                                vk.messages.send(peer_id=event.peer_id, sticker_id=random.choice(setting.Stickers),
                                                 random_id=random.randint(-1000000, 1000000))
                            except Exception as s:
                                print(s)
                            finally:
                                LastSend = datetime.datetime.now() + datetime.timedelta(minutes=setting.TimeWait)
                        else:
                            print("Осталось", LastSend - datetime.datetime.now())

                    if event.from_chat and event.user_id == user_id:

                        if message.startswith(setting.TriggerContest + " "):
                            if Contests.get(event.peer_id) is not None:
                                continue
                            message_ = event.text[len(setting.TriggerContest) + 1:]
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

                        elif message.startswith(setting.TriggerDelete):
                            message_ = message.replace(setting.TriggerDelete, '')

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
                                        print("Удаление сообщения:", s)

                        elif message == setting.TriggerEveryone[0]:
                            response = vk.messages.getChat(chat_id=event.chat_id)
                            users = response['users']
                            text = "@everyone "
                            for x in users:
                                if x < 0:
                                    pass
                                else:
                                    text += f"[id{x}|{setting.TriggerEveryone[1]}] "  # &#8300;
                            vk.messages.edit(peer_id=event.peer_id, message_id=event.message_id,
                                             message=text)
                            continue

                        elif message == setting.TriggerTranslate:
                            message_ = LastMyMessage.get(event.peer_id)
                            if message_ is not None:
                                response = vk.messages.getById(message_ids=message_)
                                msg = response.get("items", [{}])[0]
                                text = msg.get("text")
                                if text is not None:
                                    eng_chars = "~!@#%^&qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>"
                                    rus_chars = "ё!\"№%:?йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ"
                                    trans_table = dict(zip(eng_chars + rus_chars, rus_chars + eng_chars))
                                    swapped_message = ""
                                    for c in text:
                                        swapped_message += trans_table.get(c, c)
                                    try:
                                        vk.messages.edit(peer_id=event.peer_id, message=swapped_message,
                                                         message_id=message_)
                                        vk.messages.delete(message_ids=event.message_id, delete_for_all=1)
                                    finally:
                                        pass
                        elif message.startswith(setting.TriggerAddStickers):
                            sticker_id = None
                            response = vk.messages.getById(message_ids=event.message_id)["items"]
                            if response:
                                response = response[0]
                                get_sticker = response.get("reply_message")
                                if get_sticker is None:
                                    get_sticker = response.get("reply_message")
                                if get_sticker is not None:
                                    attach = get_sticker.get("attachments")[0]
                                    attach = attach.get("sticker")
                                    if attach is not None:
                                        sticker_id = attach["sticker_id"]

                            if sticker_id is not None:
                                if sticker_id in setting.Stickers:
                                    setting.Stickers.remove(sticker_id)
                                    MessageEdit(event.message_id, f"Стикер <<{sticker_id}>> удален.", event.peer_id)
                                else:
                                    setting.Stickers.append(sticker_id)
                                    MessageEdit(event.message_id, f"Стикер <<{sticker_id}>> добавлен.", event.peer_id)
                                setting.update()
                                setting.save()
                                continue

                            args: str = message.strip()
                            if args.isdigit():
                                pass


                        else:
                            if event.text != "":
                                LastMyMessage.update({event.peer_id: event.message_id})

            except Exception as s:
                print("-----------------")
                print("Ошибка выполнения:", s)
                print(event.raw)
                print("Отправьте это разработчику!")
                print("-----------------")

    except Exception as s:
        print('Ошибка ЛП: ', s)
