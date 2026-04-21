import asyncio
import logging
import sys

from rich.logging import RichHandler

from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("client")


class ChatClient:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        reader, self._writer = await asyncio.open_connection(self._host, self._port)
        log.info(f"Connected to {self._host}:{self._port}")

        read_task = asyncio.create_task(self._receive(reader))
        write_task = asyncio.create_task(self._send(self._writer))

        _done, pending = await asyncio.wait(
            [read_task, write_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

        await self._close()

    async def _receive(self, reader: asyncio.StreamReader) -> None:
        buffer_size = 4096
        
        while True:
            data = await reader.read(buffer_size)
            if not data:
                log.warning("Disconnected from server.")
                break
            sys.stdout.write(data.decode())
            sys.stdout.flush()

    async def _send(self, writer: asyncio.StreamWriter) -> None:
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            writer.write(line.encode())
            await writer.drain()

    async def _close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    client = ChatClient(host, settings.port)
    asyncio.run(client.connect())


if __name__ == "__main__":
    main()
