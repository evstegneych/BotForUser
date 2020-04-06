#BotForUser
=
Бот для вашей страницы ВК
### Установка и запуск:
~~~~
1. git clone https://github.com/Waitrum/BotForUser
2. cd BotForUser
3. pip install vk_api
4. python3.7 main.py

Для запуска в фоне:
1. git clone https://github.com/Waitrum/BotForUser
2. cd BotForUser
3. apt install npm
4. npm install pm2 -g
5. pip install vk_api
6. pm2 start main.py --name=HeyBot --interpreter=python3.7
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

* "TriggerStickers" - Массив слов триггеров, по которым отправляется стикер в беседу.

* "Stickers" - Массив стикеров, которые отправляются по триггеру выше.

* "TimeWait" - Время в минутах перезарядки кд срабатывания триггера сверху.

* "TriggerDelete" - Триггер слово для удаления последних нескольких сообщений.<br>
Использование:<br>
~~~~
Word<count> - где "Word" триггер слово а "count" сколько сообщений требуется удалить
Например "ой5" - удалит 5 последних ваших сообщений
~~~~

* "TriggerTranslate" - Триггер слово для транслита последнего сообщения в диалоге EN->RU и наоборот.

* "TriggerEveryone" - Триггер слово, и то что вставляется вместо упоминания.<br>
Например:
~~~~
TriggerWordForEveryone = [
    # Триггер слово для @everyone
    "@все",

    # То, что будет в сообщении
    "&#8300;" # Пустой символ
]

!!!ВАЖНО!!!
Не ставьте слишком большой текст во второй аргумент.
Сообщение может получиться слишком длинным и не отправиться.
~~~~

* "TriggerContest" - Триггер слово для создания розыгрыша.<br>
Например:
`роз 5 заходи)`<br>
Создаст конкурс на 5 минут со словом для участия "заходи)"<br>

* "TriggerAddStickers" - Триггер для добавления/удаления стикера при упоминании.

* "TriggerIgnore" - Триггер слово для добавления диалога в игнор отправки стикера при упоминании.

* "TriggerIgnoreList" - Массив диалогов в игнор листе.

* "TimeOutDel" - Задержка удаления системных сообщений.
