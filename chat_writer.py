import asyncio
import argparse
import logging
import json
import aiofiles


m = argparse.ArgumentParser(description="Скрипт для отправки сообщений в чат",
                            prog="chat_writer")

m.add_argument("--host", type=str, default="minechat.dvmn.org",
               help="Хост для подключения")
m.add_argument("--port", type=int, default=5050,
               help="Порт для подключения")
m.add_argument("--history", type=str,
               help="Путь к файлу лога", default="./chat_log.txt")
m.add_argument("--token", type=str,
               help="Путь к файлу с токеном", default="./chat_token.txt")
m.add_argument("--nickname", type=str,
               help="Имя пользователя для регистрации", default="Anonymous")
m.add_argument("--message", type=str, required=True,
               help="Сообщение для отправки")

arguments = m.parse_args()

logging.basicConfig(format=u"%(levelname)-8s [%(asctime)s] %(message)s",
                    level=logging.DEBUG,
                    filemode="a",
                    filename=arguments.history)


async def authorise(options, reader, writer) -> bool:
    try:
        async with aiofiles.open(options.token, mode="r") as f:
            chat_token = await f.read()
    except FileNotFoundError:
        chat_token = None

    logging.debug(await reader.readline())
    writer.write(f"{chat_token}\n".encode())

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


async def register(options, reader, writer) -> None:
    nickname = options.nickname.replace("\n", "")
    writer.write(f"{nickname}\n".encode())
    credentials_response = await reader.readline()
    user_credentials = json.loads(credentials_response)
    async with aiofiles.open(options.token, mode="w") as f:
        await f.write(user_credentials["account_hash"])


async def submit_message(writer, message):
    message = message.replace("\n", "")
    writer.write(f"{message}\n\n".encode())
    await writer.drain()


async def chat_client_writer(options: argparse.Namespace):
    reader, writer = await asyncio.open_connection(options.host, options.port)

    authorized: bool = await authorise(options, reader, writer)

    if not authorized:
        await register(options, reader, writer)

    await submit_message(writer, options.message)


if __name__ == "__main__":
    asyncio.run(chat_client_writer(arguments))
