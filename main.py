import asyncio
import json
from dataclasses import dataclass
import logging
from typing import Optional
from datetime import datetime
from socket import gaierror
import gui_main as gui
from tkinter import messagebox
import argparse
import aiofiles
from async_timeout import timeout
from anyio import create_task_group, ExceptionGroup


class InvalidToken(Exception):
    pass


@dataclass
class Account:
    nickname: str
    account_hash: str


def read_arguments():
    arguments_parser = argparse.ArgumentParser(
        description="Скрипт для чтения сообщений из чата",
        prog="chat_reader")

    arguments_parser.add_argument("--host", type=str,
                                  help="Хост для подключения",
                                  default="minechat.dvmn.org")
    arguments_parser.add_argument("--r_port", type=int,
                                  help="Порт для подключения",
                                  default=5000)
    arguments_parser.add_argument("--w_port", type=int,
                                  help="Порт для подключения",
                                  default=5050)
    arguments_parser.add_argument("--history", type=str,
                                  help="Путь к файлу лога",
                                  default="./chat_history.txt")
    arguments_parser.add_argument("--log", type=str,
                                  help="Путь к файлу лога",
                                  default="./chat.log")

    return arguments_parser.parse_args()


def setup_logger(name: str, log_filename: str, log_format: str = None):
    new_logger = logging.getLogger(name)
    new_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename, mode="a")
    if not log_format:
        log_format = "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    new_logger.addHandler(file_handler)
    return new_logger


async def authorize(reader, writer, root_logger) -> Optional[Account]:
    try:
        async with aiofiles.open("chat_token.txt", mode="r") as f:
            chat_token = await f.read()
    except FileNotFoundError:
        chat_token = None

    # Skip greeting message
    root_logger.debug(str(await reader.readline()))

    writer.write(f"{chat_token}\n".encode())
    await writer.drain()

    account_json = await reader.readline()
    try:
        account = Account(**json.loads(account_json))
        return account
    except (json.decoder.JSONDecodeError, TypeError):
        # Skip message if token incorrect
        if chat_token:
            root_logger.debug(str(await reader.readline()))
        raise InvalidToken


async def save_messages(filepath, queue: asyncio.Queue):
    while True:
        message = await queue.get()
        async with aiofiles.open(filepath, mode="a") as f:
            await f.write(message)


async def load_messages(filepath, queue: asyncio.Queue):
    async with aiofiles.open(filepath, mode="r") as f:
        while True:
            message = await f.readline()
            if not message:
                break
            await queue.put(message.replace("\n", ""))


async def read_msgs(host: str, port: int, messages_queue: asyncio.Queue,
                    status_updates_queue: asyncio.Queue,
                    history_queue: asyncio.Queue):
    event = gui.ReadConnectionStateChanged.INITIATED
    status_updates_queue.put_nowait(event)

    try:
        reader, writer = await asyncio.open_connection(host, port)
    except gaierror:
        raise ConnectionError

    event = gui.ReadConnectionStateChanged.ESTABLISHED
    status_updates_queue.put_nowait(event)

    try:
        while True:
            incoming_message = await reader.readline()
            received_at = datetime.now().strftime("%H:%m:%S %d-%m-%Y")
            prepared_message = f"[{received_at}] {incoming_message.decode()!s}"
            messages_queue.put_nowait(prepared_message.replace("\n", ""))
            history_queue.put_nowait(prepared_message)
    finally:
        writer.close()
        await writer.wait_closed()


async def submit_messages(writer, sending_queue):
    while True:
        message = await sending_queue.get()
        prepared_message = message.replace("\n", "")
        writer.write(f"{prepared_message}\n\n".encode())
        await writer.drain()


async def send_msgs(host, port, sending_queue: asyncio.Queue,
                    status_updates_queue: asyncio.Queue,
                    root_logger: logging.Logger):
    event = gui.SendingConnectionStateChanged.INITIATED
    status_updates_queue.put_nowait(event)

    try:
        reader, writer = await asyncio.open_connection(host, port)
    except gaierror:
        raise ConnectionError

    event = gui.SendingConnectionStateChanged.ESTABLISHED
    status_updates_queue.put_nowait(event)

    account: Optional[Account] = await authorize(reader, writer, root_logger)

    message = f"Выполнена авторизация. Пользователь {account.nickname}."
    root_logger.info(message)
    print(message)

    event = gui.NicknameReceived(account.nickname)
    status_updates_queue.put_nowait(event)

    try:
        async with create_task_group() as tg:
            tg.start_soon(submit_messages, writer, sending_queue)
            tg.start_soon(watch_for_connection, writer)
    finally:
        writer.close()
        await writer.wait_closed()


async def watch_for_connection(writer):
    ping = ""
    while True:
        try:
            async with timeout(10):
                writer.write(ping.encode())
                await writer.drain()
            await asyncio.sleep(15)
        except (gaierror, asyncio.exceptions.TimeoutError):
            raise ConnectionError


def reconnect(func):
    async def wrapper(*args, **kwargs):
        while True:
            try:
                await func(*args, **kwargs)
            except (ConnectionError, gaierror, ExceptionGroup):
                status_updates_queue = args[5]

                event = gui.SendingConnectionStateChanged.CLOSED
                status_updates_queue.put_nowait(event)

                event = gui.ReadConnectionStateChanged.CLOSED
                status_updates_queue.put_nowait(event)

                await asyncio.sleep(5)
    return wrapper


@reconnect
async def handle_connection(host, r_port, w_port, messages_queue, sending_queue,
                            status_updates_queue, history_queue, root_logger):
    async with create_task_group() as tg:
        tg.start_soon(read_msgs, host, r_port, messages_queue,
                      status_updates_queue, history_queue)
        tg.start_soon(send_msgs, host, w_port, sending_queue,
                      status_updates_queue, root_logger)


async def start_chat_client(arguments, root_logger):
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    await load_messages(arguments.history, messages_queue)

    async with create_task_group() as tg:
        tg.start_soon(gui.draw, messages_queue, sending_queue,
                      status_updates_queue)
        tg.start_soon(handle_connection, arguments.host, arguments.r_port,
                      arguments.w_port, messages_queue, sending_queue,
                      status_updates_queue, history_queue, root_logger)
        tg.start_soon(save_messages, arguments.history, history_queue)


def main():
    arguments = read_arguments()
    root_logger = setup_logger("", arguments.log)
    try:
        asyncio.run(start_chat_client(arguments, root_logger))
    except InvalidToken:
        message = "Проверьте токен, сервер его не узнал."
        root_logger.info(message)
        messagebox.showerror("Неверный токен", message)
    except (KeyboardInterrupt, gui.TkAppClosed):
        message = "Клиент остановлен"
        root_logger.info(message)
        print(message)
    except Exception as e:
        message = f"Клиент завершил работу с ошибкой {e}"
        root_logger.info(message)
        print(message)


if __name__ == "__main__":
    main()
