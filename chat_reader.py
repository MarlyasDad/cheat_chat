import asyncio
import argparse
from datetime import datetime
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
                                  default=5000)
    arguments_parser.add_argument("--history", type=str,
                                  help="Путь к файлу лога",
                                  default="./chat_log.txt")

    return arguments_parser.parse_args()


async def main(host: str, port: int, history: str):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        while True:
            incoming_message = await reader.readline()
            received_at = datetime.now().strftime("%H:%m:%S %d-%m-%Y")
            prepared_message = f"[{received_at}] {incoming_message.decode()!s}"
            print(prepared_message, end="")

            async with aiofiles.open(history, mode="a") as f:
                await f.write(prepared_message)
    except KeyboardInterrupt:
        print("CTRL-C")
    finally:
        print("Close the connection")
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    arguments = read_arguments()
    asyncio.run(main(arguments.host, arguments.port, arguments.history))
