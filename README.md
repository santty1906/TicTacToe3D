# 4x4x4 TicTacToe

## Descripción general

4x4x4 TicTacToe es un juego multijugador en línea de tres dimensiones desarrollado con Python, Tkinter y WebSockets. Dos jugadores se conectan al mismo servidor y comparten una partida sincronizada en un tablero cúbico de 4x4x4, donde gana quien complete primero una línea de cuatro fichas.

## Objetivo del proyecto

El objetivo es ofrecer una implementación funcional y visualmente clara de TicTacToe 3D con comunicación en tiempo real entre cliente y servidor. El proyecto sirve como ejemplo de integración entre interfaz gráfica, lógica de juego y mensajería WebSocket.

## Características principales

- Tablero tridimensional de 64 celdas organizadas en 4 niveles.
- Partidas en tiempo real entre dos jugadores.
- Detección de victoria en líneas horizontales, verticales, diagonales de nivel y diagonales espaciales.
- Reinicio de tablero sincronizado entre ambos clientes.
- Interfaz de escritorio con Tkinter.
- Servidor ligero con WebSockets para coordinar la sala.

## Tecnologías utilizadas

- Python 3.9 o superior.
- Tkinter para la interfaz gráfica.
- asyncio para concurrencia asíncrona.
- websockets para comunicación cliente-servidor.

## Estructura del proyecto

- [main_tictactoe3d.py](main_tictactoe3d.py): cliente de escritorio, interfaz de usuario, estado local del tablero y sincronización con el servidor.
- [server.py](server.py): servidor WebSocket que asigna jugadores, retransmite jugadas y gestiona el ciclo de vida de la partida.
- [requirements.txt](requirements.txt): dependencias del proyecto.

## Requisitos

- Python 3.9 o superior.
- Acceso a Internet si el cliente se conecta a un servidor remoto.
- La dependencia `websockets`, instalada desde `requirements.txt`.

## Instalación paso a paso

1. Abre una terminal en la carpeta del proyecto.
2. Crea un entorno virtual si lo deseas.
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Verifica que el servidor que usarás esté disponible o ejecútalo localmente con `python server.py`.
5. Si el servidor cambia de dirección, actualiza la constante `SERVER_URL` en [main_tictactoe3d.py](main_tictactoe3d.py).

## Cómo ejecutar el proyecto

### Servidor local

```bash
python server.py
```

### Cliente

```bash
python main_tictactoe3d.py
```

Si el servidor se publica en un entorno HTTPS, el cliente debe usar una URL WebSocket segura con `wss://`.

## Cómo jugar

1. Ejecuta el cliente en dos equipos o en dos instancias separadas.
2. Espera a que el servidor asigne a cada jugador su puesto.
3. El jugador 1 comienza automáticamente cuando ambos están conectados.
4. Haz clic en una celda vacía para colocar tu marca.
5. Gana quien complete una línea de cuatro fichas en cualquier dirección válida del cubo.
6. Usa **Nuevo tablero** para reiniciar la partida.

## Arquitectura general

La aplicación se divide en dos capas:

- El cliente visualiza el tablero, controla los eventos de la interfaz y mantiene una copia local del estado para responder con rapidez a la interacción del usuario.
- El servidor actúa como árbitro simple: asigna una silla a cada jugador, retransmite jugadas válidas y notifica reinicios o desconexiones.

El cliente no decide por sí solo el ganador final; calcula la victoria con el estado local recibido y sincronizado. La lista de líneas ganadoras se genera al inicio para cubrir todas las combinaciones posibles del cubo 4x4x4, incluidas las diagonales espaciales.

## Clases y módulos principales

### [main_tictactoe3d.py](main_tictactoe3d.py)

- `SpatialTicTacToeApp`: encapsula la interfaz gráfica, la red, el estado del tablero y las acciones del usuario.
- `build_winning_lines()`: construye todas las líneas posibles que pueden producir una victoria.
- `main()`: punto de entrada del cliente.

### [server.py](server.py)

- `MatchHub`: administra la sala de juego, la asignación de jugadores y el reenvío de mensajes.
- `handle_socket()`: procesa cada conexión WebSocket entrante.
- `main()`: arranca el servidor asíncrono.

## Capturas de pantalla

### Pantalla principal

<!-- Sustituir por una captura real del cliente -->

### Partida en curso

<!-- Sustituir por una captura real de una partida activa -->

## Posibles mejoras futuras

- Añadir un historial visual de jugadas.
- Incluir indicadores más claros de estado de conexión y reconexión.
- Incorporar pruebas automatizadas para la detección de líneas ganadoras.
- Permitir personalizar el color de las fichas o el tema visual.
- Soportar salas múltiples o matchmaking automático.

## Autores

- Proyecto original: equipo del repositorio.
- Documentación actualizada: GitHub Copilot.

## Licencia

No se ha declarado una licencia en el repositorio. Si el proyecto se va a distribuir públicamente, conviene añadir una licencia explícita como MIT, Apache 2.0 o GPLv3.
