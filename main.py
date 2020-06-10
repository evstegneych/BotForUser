import datetime
import json
import random
import re
import time
from threading import Thread

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


class Settings:
    __slots__ = ["Token", "TriggerStickers", "Answers",
                 "TimeWait", "TriggerDelete",
                 "TriggerTranslate",
                 "TriggerContest", "TriggerAddStickers",
                 "TriggerIgnore", "IgnoreList",
                 "TimeOutDel", "filename", "_data"]

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

    def update(self):
        for k in self.__slots__[:-2]:
            self._data[k] = getattr(self, k)


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

ContestText2 = f"Вы уже забыли про конкурс?\n" \
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


def MessageDelete(mid, delete_for_all=1):
    vk.messages.delete(message_ids=mid,
                       delete_for_all=delete_for_all)


def GetNameUsers(user_ids):
    names = []
    resp = vk.users.get(user_ids=user_ids)
    for u in resp:
        names.append(f"@id{u['id']}({u['first_name']})")
    return ", ".join(names)


def run(target, arg=None, timeout=None):
    if arg is None:
        arg = []
    Thread(target=void, args=[target, arg, timeout], daemon=True).start()


def void(target, arg=None, timeout=None):
    if timeout is not None:
        time.sleep(timeout)
    if arg is None:
        arg = []
    target(*arg)


def ContestsControl():
    while True:
        try:
            con = Contests.copy()
            for key, v in con.items():
                t = v["time"] - datetime.datetime.now()
                _hours, _minutes, _seconds = convert_timedelta(t)
                if not _minutes and _seconds:
                    _minutes = 1
                check_time = t.total_seconds() <= 30
                if check_time:
                    _hours = 0
                    _minutes = 0
                i = 0
                res = vk.messages.getHistory(peer_id=v["peer_id"])["items"]
                for val in res:
                    if val["id"] == v["message_id"]:
                        break
                    else:
                        i += 1
                if i >= 15 and not check_time:
                    MessageDelete(v["message_id"])
                    Contests[v["peer_id"]]["message_id"] = vk.messages.send(peer_id=v["peer_id"],
                                                                            message=ContestText2.format(
                                                                                f"{_hours} ч. {_minutes} мин.",
                                                                                v["trigger"],
                                                                                GetNameUsers(Contests[key]["users"])),
                                                                            random_id=random.randint(-1000000, 1000000),
                                                                            disable_mentions=1)
                else:
                    MessageEdit(v["message_id"],
                                ContestText.format(
                                    f"{_hours} ч. {_minutes} мин.",
                                    v["trigger"],
                                    GetNameUsers(Contests[key]["users"])), v["peer_id"])
                if check_time:
                    del Contests[key]
                    winner = random.choice(v["users"] if len(v["users"]) else 0)
                    vk.messages.send(peer_id=v["peer_id"],
                                     message=ContestTextWin.format(GetNameUsers([winner])),
                                     random_id=random.randint(-1000000, 1000000),
                                     forward_messages=v["message_id"])
                    MessageDelete(v["message_id"])
        except Exception as error:
            print("Поток Конкурсов:", error)
        finally:
            time.sleep(140)


run(ContestsControl)
print("Бот запущен")
while True:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if not event.text:
                    continue
                message = event.message.lower()

                if event.from_chat:
                    contest = None
                    for (peer_id, value) in Contests.items():
                        if message == value["trigger"].lower() and value["peer_id"] == event.peer_id:
                            contest = value
                            break
                    if contest is not None:
                        if event.user_id not in contest["leave_users"]:
                            if event.user_id not in contest["users"]:
                                Contests[contest["peer_id"]]["users"].append(event.user_id)
                            else:
                                Contests[contest["peer_id"]]["leave_users"].append(event.user_id)
                                Contests[contest["peer_id"]]["users"].remove(event.user_id)
                            t_lp = contest["time"] - datetime.datetime.now()
                            _hours_lp, _minutes_lp, _seconds_lp = convert_timedelta(t_lp)
                            if not _minutes_lp and _seconds_lp:
                                _minutes_lp = 1
                            check_time_lp = t_lp.total_seconds() <= 30
                            if check_time_lp:
                                _hours_lp = 0
                                _minutes_lp = 0
                            MessageEdit(contest["message_id"],
                                        ContestText.format(
                                            f"{_hours_lp} ч. {_minutes_lp} мин.",
                                            contest["trigger"],
                                            GetNameUsers(contest["users"])),
                                        contest["peer_id"])

                    find = CheckMarkUser(message)
                    if (
                            find
                            and LastSend is not None
                            and event.user_id != user_id
                            and event.peer_id not in setting.IgnoreList
                    ):

                        if datetime.datetime.now() >= LastSend:
                            choice_msg = random.choice(setting.Answers)
                            try:
                                time.sleep(.3)
                                if isinstance(choice_msg, int):
                                    vk.messages.send(peer_id=event.peer_id, sticker_id=choice_msg,
                                                     random_id=random.randint(-1000000, 1000000))
                                else:
                                    vk.messages.send(peer_id=event.peer_id, message=choice_msg,
                                                     random_id=random.randint(-1000000, 1000000))
                            except Exception as s:
                                print("Отправка сообещния на упоминание:", s)
                            finally:
                                LastSend = datetime.datetime.now() + datetime.timedelta(minutes=setting.TimeWait)
                        else:
                            print("Осталось до отправки стикера:", LastSend - datetime.datetime.now())

                    if event.user_id == user_id:

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
                                MessageEdit(event.message_id, text, event.peer_id)
                                Contests.update(
                                    {
                                        event.peer_id:
                                            {
                                                "peer_id": event.peer_id,
                                                "users": [],
                                                "message_id": event.message_id,
                                                "trigger": " ".join(trigger),
                                                "time": datetime.datetime.now() + time_,
                                                "leave_users": []
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
                                        MessageDelete(to_del)
                                    except Exception as s:
                                        print("Удаление сообщения:", s)

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
                                        MessageEdit(message_, swapped_message, event.peer_id)
                                        MessageDelete(event.message_id)
                                    finally:
                                        pass
                        elif message.startswith(setting.TriggerAddStickers):
                            sticker_id = None
                            response = vk.messages.getById(message_ids=event.message_id)["items"]
                            if response:
                                response = response[0]
                                get_sticker = response.get("reply_message")
                                if get_sticker is None:
                                    get_sticker = response.get("fwd_messages")
                                    if get_sticker:
                                        get_sticker = get_sticker[0]
                                    else:
                                        get_sticker = None
                                if get_sticker is not None:
                                    attach = get_sticker.get("attachments")
                                    if attach:
                                        attach = attach[0].get("sticker")
                                        if attach is not None:
                                            sticker_id = attach["sticker_id"]

                            if sticker_id is not None:
                                if sticker_id in setting.Answers:
                                    setting.Answers.remove(sticker_id)
                                    MessageEdit(event.message_id, f"Стикер <<{sticker_id}>> удален.", event.peer_id)
                                else:
                                    setting.Answers.append(sticker_id)
                                    MessageEdit(event.message_id, f"Стикер <<{sticker_id}>> добавлен.",
                                                event.peer_id)
                                run(MessageDelete, arg=[event.message_id], timeout=setting.TimeOutDel)
                                setting.update()
                                setting.save()
                                continue
                        elif message == setting.TriggerIgnore:
                            dialog_id = event.peer_id
                            if dialog_id in setting.IgnoreList:
                                setting.IgnoreList.remove(dialog_id)
                                MessageEdit(event.message_id, f"Диалог <<{dialog_id}>> удален из игнор листа.",
                                            dialog_id)
                            else:
                                setting.IgnoreList.append(event.peer_id)
                                MessageEdit(event.message_id, f"Диалог <<{dialog_id}>> добавлен в игнор лист.",
                                            dialog_id)
                            run(MessageDelete, arg=[event.message_id], timeout=setting.TimeOutDel)
                            setting.update()
                            setting.save()
                            continue

                        else:
                            LastMyMessage.update({event.peer_id: event.message_id})

    except Exception as s:
        print('Критическая ошибка: ', s)
