#BotForUser
=
Бот для вашей страницы ВК
### Установка и запуск:
~~~~
1. pip install vk_api
2. python main.py
~~~~

### Основной функционал:

* Отправка стикера по триггер слову.
* Удаление последних нескольких сообщений по триггер слову.
* Транслит последнего сообщения в диалоге EN->RU и наоборот по триггер слову.
* Упоминание всех, кто есть в конфереции по триггер слову.
* Создание розыгрышей среди участников беседы. 
---
### Настройка: `(config.json)`
* "Token" - Сюда вписывать токен страницы

* "TriggerWordForStickers" - Массив слов триггеров, по которым отправляется стикер в беседу.

* "Stickers" - Массив стикеров, которые отправляются по триггеру выше.

* "TimeWait" - Время в минутах перезарядки кд срабатывания триггера сверху.

* "TriggerWordForDelete" - Триггер слово для удаления последних нескольких сообщений.<br>
Использование:<br>
~~~~
Word<count> - где "Word" триггер слово а "count" сколько сообщений требуется удалить
Например "ой5" - удалит 5 последних ваших сообщений
~~~~

* "TriggerWordForTranslate" - Триггер слово для транслита последнего сообщения в диалоге EN->RU и наоборот.

* "TriggerWordForEveryone" - Триггер слово, и то что вставляется вместо упоминания.<br>
Например:
~~~~
TriggerWordForEveryone = [
    # Триггер слово для @everyone
    "@все",

    # То, что будет в сообщении
    "&#8300;" # Пустой символ
]

!!!ВАЖНО!!!
Не ставьте слишком большой теекст во второй аргумент.
Сообщение может получиться слишком длинным и не отправиться.
~~~~
* "TriggerWordForContest" - Триггер слово для создания розыгрыша.<br>
Например:
`роз 5 заходи)`<br>
Создаст конкурс на 5 минут со словом для участия "заходи)"<br>
**!!! Зависит от регистра !!!**

