import asyncio
import argparse
from datetime import datetime
import aiofiles

m = argparse.ArgumentParser(description="Скрипт для чтения сообщений из чата",
                            prog="chat_reader")

m.add_argument("--host", type=str, default="minechat.dvmn.org",
               help="Хост для подключения")
m.add_argument("--port", type=int, default=5000,
               help="Порт для подключения")
m.add_argument("--history", type=str,
               help="Путь к файлу лога", default="./chat_log.txt")

arguments = m.parse_args()


async def chat_client_reader(options: argparse.Namespace):
    reader, writer = await asyncio.open_connection(options.host, options.port)

    try:
        while True:
            data = await reader.readline()
            received_at = datetime.now().strftime("%H:%m:%S %d-%m-%Y")
            message = f"[{received_at}] {data.decode()!s}"
            print(message, end="")

            async with aiofiles.open(options.history, mode="a") as f:
                await f.write(message)
    except KeyboardInterrupt:
        print("CTRL-C")
    finally:
        print('Close the connection')
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(chat_client_reader(arguments))
