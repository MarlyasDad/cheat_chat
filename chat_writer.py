import asyncio
import argparse
import logging
import json
import aiofiles


def read_arguments():
    arguments_parser = argparse.ArgumentParser(
        description="Скрипт для чтения сообщений из чата",
        prog="chat_reader")

    arguments_parser.add_argument("--host", type=str,
                                  help="Хост для подключения",
                                  default="minechat.dvmn.org")
    arguments_parser.add_argument("--port", type=int,
                                  help="Порт для подключения",
                                  default=5050)
    arguments_parser.add_argument("--history", type=str,
                                  help="Путь к файлу лога",
                                  default="./chat_log.txt")
    arguments_parser.add_argument("--nickname", type=str,
                                  help="Имя пользователя для регистрации",
                                  default="Anonymous")
    arguments_parser.add_argument("--message", type=str,
                                  help="Сообщение для отправки",
                                  required=True)

    return arguments_parser.parse_args()


def setup_logger(log_filename):
    new_logger = logging.getLogger()
    new_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename, mode="a")
    formatter = logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s "
                                  "- %(message)s")
    file_handler.setFormatter(formatter)
    new_logger.addHandler(file_handler)
    return new_logger


async def authorize(reader, writer, logger) -> bool:
    try:
        async with aiofiles.open("chat_token.txt", mode="r") as f:
            chat_token = await f.read()
    except FileNotFoundError:
        chat_token = None

    logger.debug(str(await reader.readline()))
    writer.write(f"{chat_token}\n".encode())
    await writer.drain()

    login_response = await reader.readline()
    try:
        login_message = json.loads(login_response)
    except json.decoder.JSONDecodeError:
        return False

    if not login_message:
        # Skip login message
        await reader.readline()
        return False
    return True


async def register(reader, writer, nickname) -> None:
    prepared_nickname = nickname.replace("\n", "")
    writer.write(f"{prepared_nickname}\n".encode())
    await writer.drain()
    credentials_content = await reader.readline()
    access_credentials = json.loads(credentials_content)
    async with aiofiles.open("chat_token.txt", mode="w") as f:
        await f.write(access_credentials["account_hash"])


async def submit_message(writer, message):
    prepared_message = message.replace("\n", "")
    writer.write(f"{prepared_message}\n\n".encode())
    await writer.drain()


async def main(host: str, port: int, nickname: str, message: str,
               logger: logging.Logger):
    reader, writer = await asyncio.open_connection(host, port)

    authorized: bool = await authorize(reader, writer, logger)

    if not authorized:
        await register(reader, writer, nickname)

    await submit_message(writer, message)


if __name__ == "__main__":
    arguments = read_arguments()
    root_logger = setup_logger(arguments.history)
    asyncio.run(main(arguments.host, arguments.port, arguments.nickname,
                     arguments.message, root_logger))
