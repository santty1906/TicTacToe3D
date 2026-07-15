# Nebula 4x4x4 Arena

Nebula 4x4x4 Arena es un juego multijugador de TicTacToe tridimensional hecho con Python, Tkinter y WebSockets. La idea es simple: dos personas abren el cliente, se conectan al mismo servidor y juegan sobre un tablero de 4x4x4 completamente sincronizado en tiempo real.

## Qué incluye

- `server.py`: recibe las conexiones, asigna cada jugador a una silla y retransmite los movimientos entre ambos.
- `main_tictactoe3d.py`: abre la ventana del juego, pinta la interfaz y mantiene el estado local del tablero.

## Requisitos

Necesitas lo siguiente en cada equipo que vaya a ejecutar el cliente:

- Python 3.9 o superior
- La librería `websockets`

Instalación rápida:

```bash
pip install -r requirements.txt
```

## Preparar el servidor

Si vas a publicar el juego en Render u otro servicio similar, configura el proceso de esta forma:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server.py`

Cuando el servicio quede en línea, obtendrás una URL pública parecida a esta:

```text
https://tu-servidor.onrender.com
```

Para el cliente, esa dirección debe usarse con `wss://`.

## Ajustar el cliente

Abre `main_tictactoe3d.py` y cambia esta constante:

```python
SERVER_URL = "wss://tu-servidor-aqui.onrender.com"
```

Reemplázala por la dirección real de tu servidor. Ejemplo:

```python
SERVER_URL = "wss://tu-servidor.onrender.com"
```

Si el servidor usa HTTPS en el navegador, en el cliente debe ir como WebSocket seguro (`wss://`).

## Ejecutar una partida

En cada computadora, ejecuta el cliente con:

```bash
python main_tictactoe3d.py
```

Flujo de conexión:

1. El primer jugador que entra recibe el puesto 1.
2. El segundo jugador ocupa el puesto 2.
3. Cuando ambos están conectados, la partida empieza automáticamente.
4. Cada jugada viaja al servidor y se refleja en la otra pantalla.

## Despliegue local del servidor

Si quieres probar todo en tu propia máquina antes de publicar, abre una terminal en la carpeta del proyecto y ejecuta:

```bash
python server.py
```

Luego apunta el cliente a la dirección del servidor que estés usando en ese momento.

## Controles

- Haz clic en una celda disponible para marcar tu jugada.
- Usa **Nuevo tablero** para reiniciar la partida.
- Usa **Salir** para cerrar la ventana.

## Observaciones

- El servidor solo admite dos jugadores por partida.
- Si uno de los dos se desconecta, la sala se cierra y debe abrirse otra partida.
- Si el servicio de hosting entra en reposo, el primer intento de conexión puede tardar unos segundos más de lo normal.
