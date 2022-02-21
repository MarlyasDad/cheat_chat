# Cheat chat

Чат для обмена кодами к Minecraft

## Как запустить

Для начала установите необходимые пакеты

```commandline
$ cd /path/to/cheat_chat/folder
$ python3 -m pip install -r requirements.txt
```

Прежде, чем начать общаться, зарегистрируйтесь в чате. Запустите register.py и следуйте инструкциям.

```commandline
$ python3 register.py
```

Агрументы:

```commandline
--host minechat.dvmn.org (хост для подключения)
--w_port 5050 (порт для отправки сообщений)
--log chat.log (путь к файлу для записи логов)
```

Чтобы подключиться к чату запустите main.py

```commandline
$ python3 main.py
```

Агрументы:

```commandline
--host minechat.dvmn.org (хост для подключения)
--r_port 5000 (порт для чтения сообщений)
--w_port 5050 (порт для отправки сообщений)
--history chat_history.txt (путь к файлу для записи чата)
--log chat.log (путь к файлу для записи логов)
```

### **Дополнительная информация**
Код создан в учебных целях. В рамках учебного курса по веб-разработке - [DVMN.org](https://dvmn.org)
