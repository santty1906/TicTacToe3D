import asyncio
import json
import os

import websockets


PORT = int(os.environ.get("PORT", 8765))


class MatchHub:
    """Gestiona una sala única de 4x4x4 TicTacToe para dos jugadores.

    Su responsabilidad es mantener el registro de sockets activos, asignar
    asientos, reenviar jugadas y cerrar la partida si uno de los participantes
    abandona la conexión.
    """

    def __init__(self):
        """Inicializa la sala, el bloqueo de concurrencia y los asientos libres."""
        self._peers = {}
        self._next_seat = 0
        self._gate = asyncio.Lock()

    async def join(self, socket):
        """Registra un nuevo cliente si todavía queda un lugar disponible."""
        async with self._gate:
            if len(self._peers) >= 2:
                await socket.close(reason="matchroom-full")
                return None

            seat = self._next_seat
            self._next_seat += 1
            self._peers[seat] = socket
            return seat

    async def start_if_ready(self):
        """Notifica el inicio cuando ya están conectados ambos jugadores."""
        if len(self._peers) == 2:
            await self._send_all({"event": "match_start"})

    async def relay(self, sender_seat, message):
        """Reenvía al oponente un evento válido originado por el emisor."""
        recipient = next((sock for seat, sock in self._peers.items() if seat != sender_seat), None)
        if recipient is not None:
            await recipient.send(json.dumps(message))

    async def notify_exit_and_reset(self, leaving_seat):
        """Informa la salida de un jugador y reinicia la sala para la próxima partida."""
        async with self._gate:
            self._peers.pop(leaving_seat, None)

            if self._peers:
                await self._send_all({"event": "match_closed"})

            self._peers.clear()
            self._next_seat = 0

    async def _send_all(self, message):
        """Difunde un mensaje a todos los sockets conectados a la sala."""
        payload = json.dumps(message)
        for socket in list(self._peers.values()):
            try:
                await socket.send(payload)
            except Exception:
                pass


hub = MatchHub()


async def handle_socket(socket):
    """Controla el ciclo de vida de una conexión WebSocket individual."""
    seat = await hub.join(socket)
    if seat is None:
        return

    try:
        await socket.send(json.dumps({"event": "seat", "seat": seat}))
        await hub.start_if_ready()

        async for raw_message in socket:
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            message_type = message.get("event")
            if message_type in {"move", "restart"}:
                await hub.relay(seat, message)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await hub.notify_exit_and_reset(seat)


async def main():
    """Arranca el servidor WebSocket escuchando en la interfaz configurada."""
    async with websockets.serve(handle_socket, "0.0.0.0", PORT, ping_interval=20, ping_timeout=20):
        print(f"Servidor activo en el puerto {PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
