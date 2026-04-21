import asyncio
import logging

from rich.logging import RichHandler

from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger(settings.server_name)


class ChatRoom:
    def __init__(self, max_clients: int, server_name: str) -> None:
        self._clients: dict[asyncio.StreamWriter, str] = {}
        self._max_clients = max_clients
        self._server_name = server_name

    @property
    def online_nicks(self) -> list[str]:
        return list(self._clients.values())

    async def broadcast(self, message: str, *, exclude: asyncio.StreamWriter | None = None) -> None:
        for writer in list(self._clients):
            if writer is exclude:
                continue
            try:
                writer.write(message.encode())
                await writer.drain()
            except ConnectionError:
                self._remove_client(writer)

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if len(self._clients) >= self._max_clients:
            await self._reject(writer, "Server is full. Try again later.\n")
            return

        nick = await self._register(reader, writer)
        if nick is None:
            return

        try:
            await self._message_loop(nick, reader, writer)
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            self._remove_client(writer)
            log.info(f"{nick} disconnected")
            await self.broadcast(f"<< {nick} left the chat\n")

    async def _register(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> str | None:
        addr = writer.get_extra_info("peername")

        writer.write(f"Welcome to {self._server_name}! Enter your nickname: ".encode())
        await writer.drain()

        try:
            data = await asyncio.wait_for(reader.readline(), timeout=30)
        except asyncio.TimeoutError:
            writer.close()
            return None

        nick = data.decode().strip() or f"anon-{addr[1]}"
        self._clients[writer] = nick
        log.info(f"{nick} connected from {addr}")

        writer.write(f"Hi {nick}! {len(self._clients)} user(s) online. Type /quit to leave.\n".encode())
        await writer.drain()
        await self.broadcast(f">> {nick} joined the chat\n", exclude=writer)
        return nick

    async def _message_loop(self, nick: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = data.decode().strip()
            if msg == "/quit":
                break
            if msg == "/who":
                writer.write(f"Online: {', '.join(self.online_nicks)}\n".encode())
                await writer.drain()
            elif msg:
                await self.broadcast(f"{nick}: {msg}\n", exclude=writer)

    def _remove_client(self, writer: asyncio.StreamWriter) -> None:
        self._clients.pop(writer, None)
        writer.close()

    async def _reject(self, writer: asyncio.StreamWriter, message: str) -> None:
        writer.write(message.encode())
        await writer.drain()
        writer.close()


async def main() -> None:
    room = ChatRoom(settings.max_clients, settings.server_name)
    server = await asyncio.start_server(
        room.handle_connection, settings.host, settings.port
    )
    log.info(f"listening on {settings.host}:{settings.port}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
