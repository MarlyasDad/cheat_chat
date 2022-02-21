import asyncio
from datetime import datetime
from socket import gaierror
from typing import Optional
import json
from main import (
    read_arguments, setup_logger, authorize, Account, InvalidToken,
)
import gui_register as gui
import aiofiles
from anyio import create_task_group
from tkinter import messagebox


def format_dialog_message(message):
    received_at = datetime.now().strftime("%H:%m:%S %d-%m-%Y")
    return f"[{received_at}] {message}"


async def register_workflow(host, port, messages_queue, sending_queue,
                            status_updates_queue, logger):
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except gaierror:
        message = f"Невозможно подключиться к серверу регистрации {host}"
        logger.warning(message)
        messagebox.showerror("Нет соединения", message)
        raise asyncio.CancelledError

    event = gui.SendingConnectionStateChanged.ESTABLISHED
    status_updates_queue.put_nowait(event)

    try:
        account: Optional[Account] = await authorize(reader, writer, logger)
    except InvalidToken:
        account = None

    if account:
        event = gui.NicknameReceived(account.nickname)
        status_updates_queue.put_nowait(event)
        await messages_queue.put(format_dialog_message(
            f"Выполнена авторизация. Пользователь {account.nickname}."))
        await messages_queue.put(format_dialog_message(
            f"Ваш ключ действителен."))
        await messages_queue.put(format_dialog_message(
            f"Приятного общения!"))
        await asyncio.sleep(15)
        raise asyncio.CancelledError

    await messages_queue.put(format_dialog_message(
        f"Токен не существует или введён не верно."
    ))
    await messages_queue.put(format_dialog_message(
        f"Для регистрации нового пользователя введите имя в поле ниже\n"
        f"и нажмите кнопку \"Зарегистрировать\"."
    ))

    message = await sending_queue.get()
    prepared_message = message.replace("\n", "")
    writer.write(f"{prepared_message}\n\n".encode())
    await writer.drain()

    account_json = await reader.readline()
    try:
        account = Account(**json.loads(account_json))
    except (json.decoder.JSONDecodeError, TypeError):
        raise InvalidToken

    event = gui.NicknameReceived(account.nickname)
    status_updates_queue.put_nowait(event)

    register_message = f"Успешная регистрация. Пользователь {account.nickname}."
    await messages_queue.put(format_dialog_message(register_message))
    logger.info(register_message)

    async with aiofiles.open("chat_token.txt", mode="w") as f:
        await f.write(account.account_hash)

    writer.close()
    await writer.wait_closed()
    await asyncio.sleep(15)
    raise asyncio.CancelledError


async def start_register_client(arguments, logger):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    async with create_task_group() as tg:
        tg.start_soon(gui.draw, messages_queue, sending_queue,
                      status_updates_queue)
        tg.start_soon(register_workflow, arguments.host, arguments.w_port,
                      messages_queue, sending_queue, status_updates_queue,
                      logger)


def main():
    arguments = read_arguments()
    root_logger = setup_logger("", arguments.log)
    try:
        asyncio.run(start_register_client(arguments, root_logger))
    except InvalidToken:
        message = "Ошибка при регистрации. Ответ сервера не опознан."
        root_logger.info(message)
    except (KeyboardInterrupt, gui.TkAppClosed):
        message = "Клиент регистрации остановлен"
        root_logger.info(message)
        print(message)
    except Exception as e:
        message = f"Клиент регистрации завершил работу с ошибкой {e}"
        root_logger.info(message)
        print(message)


if __name__ == "__main__":
    main()
