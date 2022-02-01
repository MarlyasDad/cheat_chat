# Cheat chat

Чат для обмена кодами к Minecraft

## Как запустить

Для начала установите необходимые пакеты

```commandline
$ cd /path/to/cheat_chat/folder
$ python3 -m pip install -r requirements.txt
```

Чтобы начать читать сообщения запустите chat_reader.py

```commandline
$ python3 chat_reader.py
```

Агрументы:

```commandline
--host minechat.dvmn.org (хост для подключения)
--port 5000 (порт для подключения)
--history chat_log.txt (путь к файлу для записи чата)
```

Чтобы написать сообщение в чат запустите chat_writer.py

```commandline
$ python3 chat_writer.py --message "Hi it's me"
```

--message является обязательным аргументом

Аргументы:

```commandline
--host minechat.dvmn.org (хост для подключения)
--port 5050 (порт для подключения)
--history chat_log.txt (путь к файлу для записи чата)
--nickname Anonymous (имя пользователя, которое будет использоваться при регистрации в чате)
--message "Hi" (сообщение для чата)
```

### **Дополнительная информация**
Код создан в учебных целях. В рамках учебного курса по веб-разработке - [DVMN.org](https://dvmn.org)
