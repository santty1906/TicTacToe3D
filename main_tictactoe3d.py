import asyncio
import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox

import websockets


SERVER_URL = "wss://tictactoe3d-server.onrender.com"

BOARD_SIZE = 4
LAYER_COUNT = 4
CELL_COUNT = BOARD_SIZE * BOARD_SIZE * LAYER_COUNT

BOARD_CARD_STEP = 116
BOARD_CARD_MARGIN = 10
BOARD_CELL_GAP = 2
BOARD_CELL_FONT_SIZE = 10
BOARD_CELL_WIDTH = 2
BOARD_CELL_HEIGHT = 1

APP_BG = "#0f172a"
PANEL_BG = "#111827"
CARD_BG = "#1e293b"
CARD_EDGE = "#38bdf8"
TEXT_MAIN = "#e2e8f0"
TEXT_DIM = "#94a3b8"
ACCENT_A = "#06b6d4"
ACCENT_B = "#38bdf8"
MOVE_X = "#fb7185"
MOVE_O = "#60a5fa"
CELL_IDLE = "#1e293b"
CELL_IDLE_HOVER = "#263548"
CELL_WIN = "#0ea5e9"


def build_winning_lines():
    """Genera todas las combinaciones de cuatro celdas que constituyen una victoria.

    En un tablero 4x4x4, una línea ganadora puede vivir dentro de un nivel,
    cruzar niveles, o recorrer diagonales espaciales. Construirlas una sola vez
    al inicio evita recalcular la geometría en cada movimiento.
    """
    lines = []

    for z in range(LAYER_COUNT):
        for y in range(BOARD_SIZE):
            lines.append([(z, y, x) for x in range(BOARD_SIZE)])
        for x in range(BOARD_SIZE):
            lines.append([(z, y, x) for y in range(BOARD_SIZE)])
        lines.append([(z, i, i) for i in range(BOARD_SIZE)])
        lines.append([(z, i, BOARD_SIZE - 1 - i) for i in range(BOARD_SIZE)])

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            lines.append([(z, y, x) for z in range(LAYER_COUNT)])

    for y in range(BOARD_SIZE):
        lines.append([(i, y, i) for i in range(BOARD_SIZE)])
        lines.append([(i, y, BOARD_SIZE - 1 - i) for i in range(BOARD_SIZE)])

    for x in range(BOARD_SIZE):
        lines.append([(i, i, x) for i in range(BOARD_SIZE)])
        lines.append([(i, BOARD_SIZE - 1 - i, x) for i in range(BOARD_SIZE)])

    lines.append([(i, i, i) for i in range(BOARD_SIZE)])
    lines.append([(i, i, BOARD_SIZE - 1 - i) for i in range(BOARD_SIZE)])
    lines.append([(i, BOARD_SIZE - 1 - i, i) for i in range(BOARD_SIZE)])
    lines.append([(BOARD_SIZE - 1 - i, i, i) for i in range(BOARD_SIZE)])

    return lines


class SpatialTicTacToeApp:
    """Cliente de escritorio para jugar TicTacToe 3D contra otro jugador remoto.

    La clase concentra tres responsabilidades: construir la interfaz Tkinter,
    mantener el estado local del tablero y coordinar la comunicación WebSocket
    con el servidor de partida.
    """

    def __init__(self, root):
        """Inicializa la ventana, el estado de juego y el hilo de red."""
        self.root = root
        self.root.title("4x4x4 TicTacToe")
        self.root.geometry("1360x860+20+20")
        self.root.resizable(False, False)
        self.root.configure(bg=APP_BG)

        self.socket_url = SERVER_URL
        self.seat = None
        self.turn_owner = 0
        self.match_started = False
        self.match_over = False
        self.board_state = [[[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)] for _ in range(LAYER_COUNT)]
        self.cell_buttons = [None for _ in range(CELL_COUNT)]
        self.outbox = queue.Queue()
        self.win_lines = build_winning_lines()
        self.network_stop = threading.Event()
        self.current_winner_line = []

        self._build_interface()
        self._reset_board_visuals()
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.network_thread = threading.Thread(target=self._launch_network, daemon=True)
        self.network_thread.start()

    def _build_interface(self):
        """Construye la interfaz visual completa del cliente."""
        header = tk.Frame(self.root, bg=APP_BG)
        header.pack(fill="x", padx=22, pady=(18, 10))

        title_block = tk.Frame(header, bg=APP_BG)
        title_block.pack(side="left", anchor="w")

        tk.Label(
            title_block,
            text="4x4x4 TicTacToe",
            font=("Segoe UI Semibold", 24, "bold"),
            fg=TEXT_MAIN,
            bg=APP_BG,
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Duelo en línea sobre un tablero tridimensional de 64 celdas",
            font=("Segoe UI", 10),
            fg=TEXT_DIM,
            bg=APP_BG,
        ).pack(anchor="w", pady=(2, 0))

        self.connection_chip = tk.Label(
            header,
            text="Conectando...",
            font=("Segoe UI Semibold", 10),
            fg="#e0f2fe",
            bg=ACCENT_B,
            padx=14,
            pady=8,
        )
        self.connection_chip.pack(side="right")

        body = tk.Frame(self.root, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        sidebar = tk.Frame(body, bg=PANEL_BG, bd=0, highlightthickness=1, highlightbackground=CARD_EDGE)
        sidebar.pack(side="left", fill="y", padx=(0, 16))

        board_zone = tk.Frame(body, bg=APP_BG)
        board_zone.pack(side="right", fill="both", expand=True)

        tk.Label(
            sidebar,
            text="Estado de la partida",
            font=("Segoe UI Semibold", 16, "bold"),
            fg=TEXT_MAIN,
            bg=PANEL_BG,
        ).pack(anchor="w", padx=18, pady=(18, 4))

        self.status_text = tk.Label(
            sidebar,
            text="Esperando conexión al servidor...",
            font=("Segoe UI", 12),
            fg=TEXT_DIM,
            bg=PANEL_BG,
            justify="left",
            wraplength=250,
        )
        self.status_text.pack(anchor="w", padx=18, pady=(0, 14))

        self.turn_chip = tk.Label(
            sidebar,
            text="Turno: pendiente",
            font=("Segoe UI Semibold", 11),
            fg="#e0f2fe",
            bg="#0f766e",
            padx=12,
            pady=8,
        )
        self.turn_chip.pack(anchor="w", padx=18, pady=(0, 10))

        info_card = tk.Frame(sidebar, bg=CARD_BG, bd=0, highlightthickness=1, highlightbackground=CARD_EDGE)
        info_card.pack(fill="x", padx=18, pady=(0, 14))

        self.seat_text = tk.Label(
            info_card,
            text="Jugador: sin asignar",
            font=("Segoe UI", 11),
            fg=TEXT_MAIN,
            bg=CARD_BG,
            anchor="w",
        )
        self.seat_text.pack(fill="x", padx=14, pady=(14, 6))

        self.last_move_text = tk.Label(
            info_card,
            text="Último movimiento: ninguno",
            font=("Segoe UI", 11),
            fg=TEXT_DIM,
            bg=CARD_BG,
            anchor="w",
        )
        self.last_move_text.pack(fill="x", padx=14, pady=(0, 14))

        self.restart_button = tk.Button(
            sidebar,
            text="Nuevo tablero",
            font=("Segoe UI Semibold", 11),
            fg="#ecfeff",
            bg="#155e75",
            activebackground="#0f766e",
            activeforeground="#ecfeff",
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            command=self.request_restart,
        )
        self.restart_button.pack(fill="x", padx=18, pady=(0, 10))

        exit_button = tk.Button(
            sidebar,
            text="Salir",
            font=("Segoe UI Semibold", 11),
            fg="#f8fafc",
            bg="#1d4ed8",
            activebackground="#1e40af",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            command=self.exit_app,
        )
        exit_button.pack(fill="x", padx=18, pady=(0, 18))

        board_shell = tk.Frame(board_zone, bg=APP_BG)
        board_shell.pack(fill="both", expand=True)

        self.layer_cards = []
        for z in range(LAYER_COUNT):
            x_offset = z * BOARD_CARD_STEP
            y_offset = (LAYER_COUNT - 1 - z) * BOARD_CARD_STEP
            card = tk.Frame(
                board_shell,
                bg=CARD_BG,
                highlightthickness=1,
                highlightbackground=CARD_EDGE,
                bd=0,
                padx=BOARD_CARD_MARGIN,
                pady=BOARD_CARD_MARGIN,
            )
            card.place(x=x_offset, y=y_offset)

            tk.Label(
                card,
                text=f"Nivel {z + 1}",
                font=("Segoe UI Semibold", 12, "bold"),
                fg=TEXT_MAIN,
                bg=CARD_BG,
            ).pack(anchor="w", pady=(0, 10))

            grid = tk.Frame(card, bg=CARD_BG)
            grid.pack(expand=True)

            for y in range(BOARD_SIZE):
                for x in range(BOARD_SIZE):
                    index = z * 16 + y * 4 + x
                    button = tk.Button(
                        grid,
                        text="",
                        width=BOARD_CELL_WIDTH,
                        height=BOARD_CELL_HEIGHT,
                        font=("Segoe UI Semibold", BOARD_CELL_FONT_SIZE, "bold"),
                        fg=TEXT_MAIN,
                        bg=CELL_IDLE,
                        activebackground=CELL_IDLE_HOVER,
                        activeforeground=TEXT_MAIN,
                        relief="flat",
                        bd=0,
                        highlightthickness=1,
                        highlightbackground=CARD_EDGE,
                        highlightcolor=CARD_EDGE,
                        padx=0,
                        pady=0,
                        command=lambda cell=index: self.handle_cell_click(cell),
                    )
                    button.grid(row=y, column=x, padx=BOARD_CELL_GAP, pady=BOARD_CELL_GAP)
                    button.bind("<Enter>", lambda _event, widget=button: self._hover_cell(widget, True))
                    button.bind("<Leave>", lambda _event, widget=button: self._hover_cell(widget, False))
                    grid.grid_rowconfigure(y, weight=0)
                    grid.grid_columnconfigure(x, weight=0)
                    self.cell_buttons[index] = button

        footer = tk.Frame(self.root, bg=APP_BG)
        footer.pack(fill="x", padx=22, pady=(0, 18))

        tk.Label(
            footer,
            text="WebSockets + Tkinter | tablero 3D sincronizado entre dos equipos",
            font=("Segoe UI", 9),
            fg=TEXT_DIM,
            bg=APP_BG,
        ).pack(side="left")

    def _hover_cell(self, widget, is_entering):
        """Aplica un resaltado visual solo a celdas vacías."""
        current_text = widget.cget("text")
        if current_text:
            return
        widget.configure(bg=CELL_IDLE_HOVER if is_entering else CELL_IDLE)

    def _launch_network(self):
        """Arranca el bucle asíncrono de red en un hilo separado."""
        asyncio.run(self._network_main())

    async def _network_main(self):
        """Mantiene la conexión WebSocket y despacha mensajes entrantes."""
        try:
            async with websockets.connect(self.socket_url, ping_interval=20, ping_timeout=20) as socket:
                sender = asyncio.create_task(self._outbound_pump(socket))
                try:
                    async for raw_message in socket:
                        await self._process_server_message(raw_message)
                finally:
                    sender.cancel()
                    try:
                        await sender
                    except asyncio.CancelledError:
                        pass
        except Exception as error:
            self._ui(lambda: self._handle_connection_error(error))

    async def _outbound_pump(self, socket):
        """Envía al servidor los eventos acumulados en la cola de salida."""
        while not self.network_stop.is_set():
            try:
                payload = self.outbox.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.03)
                continue

            await socket.send(json.dumps(payload))

    async def _process_server_message(self, raw_message):
        """Interpreta los eventos enviados por el servidor y actualiza la UI."""
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            return

        event_name = message.get("event")

        if event_name == "seat":
            seat = int(message.get("seat", 0))
            self._ui(lambda: self._accept_seat(seat))
        elif event_name == "match_start":
            self._ui(self._mark_match_started)
        elif event_name == "move":
            cell_index = int(message.get("cell", -1))
            self._ui(lambda: self._apply_move(cell_index, remote=True))
        elif event_name == "restart":
            self._ui(lambda: self._reset_board(announce=False))
        elif event_name == "match_closed":
            self._ui(self._handle_remote_disconnect)

    def _handle_connection_error(self, error):
        """Informa al usuario cuando no se puede establecer la conexión."""
        messagebox.showerror("Conexión fallida", f"No fue posible conectar con el servidor:\n{error}")
        self.root.destroy()

    def _handle_remote_disconnect(self):
        """Cierra la partida cuando el oponente abandona la sala."""
        messagebox.showwarning("Partida interrumpida", "El otro jugador abandonó la sala.")
        self.root.destroy()

    def _ui(self, callback):
        """Programa una actualización segura de Tkinter desde el hilo de red."""
        try:
            self.root.after(0, callback)
        except tk.TclError:
            pass

    def _accept_seat(self, seat):
        """Registra el asiento asignado por el servidor y actualiza el estado."""
        self.seat = seat
        self.turn_owner = 0
        self.match_started = False
        self.match_over = False
        self.seat_text.configure(text=f"Jugador: {seat + 1}")
        self.connection_chip.configure(text=f"Conectado como Jugador {seat + 1}", bg="#1d4ed8")
        self._refresh_turn_chip()
        self.status_text.configure(text="Esperando a que se conecte el segundo jugador...")

    def _mark_match_started(self):
        """Marca el inicio de la partida cuando el servidor confirma dos jugadores."""
        self.match_started = True
        self.match_over = False
        self.turn_owner = 0
        self.status_text.configure(text="La partida ya comenzó. Juega el Jugador 1.")
        self._refresh_turn_chip()

    def _refresh_turn_chip(self):
        """Actualiza el indicador visual del turno según el estado actual."""
        if self.match_over:
            self.turn_chip.configure(text="Turno: partida cerrada", bg="#7c2d12")
            return

        if self.seat is None:
            self.turn_chip.configure(text="Turno: pendiente", bg="#14532d")
            return

        if self.turn_owner == self.seat:
            self.turn_chip.configure(text="Turno: te toca jugar", bg="#166534")
        else:
            self.turn_chip.configure(text="Turno: espera al rival", bg="#1e3a8a")

    def _index_to_coords(self, cell_index):
        """Convierte un índice lineal del tablero en coordenadas 3D."""
        z = cell_index // 16
        remainder = cell_index % 16
        y = remainder // 4
        x = remainder % 4
        return z, y, x

    def handle_cell_click(self, cell_index):
        """Procesa la jugada local si el turno y la celda son válidos."""
        if self.seat is None or not self.match_started or self.match_over:
            return

        if self.turn_owner != self.seat:
            self.status_text.configure(text="No es tu turno todavía.")
            return

        z, y, x = self._index_to_coords(cell_index)
        if self.board_state[z][y][x] != 0:
            return

        self.outbox.put({"event": "move", "cell": cell_index})
        self._apply_move(cell_index, remote=False)

    def request_restart(self):
        """Solicita al servidor un reinicio de la partida tras confirmación."""
        answer = messagebox.askyesno("Nuevo tablero", "¿Quieres reiniciar la partida completa?")
        if not answer:
            return

        self.outbox.put({"event": "restart"})
        self._reset_board(announce=True)

    def _reset_board(self, announce=True):
        """Limpia el tablero y reinicia el estado local de la partida."""
        self.board_state = [[[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)] for _ in range(LAYER_COUNT)]
        self.current_winner_line = []
        self.turn_owner = 0
        self.match_started = self.seat is not None
        self.match_over = False

        for button in self.cell_buttons:
            button.configure(text="", fg=TEXT_MAIN, bg=CELL_IDLE)

        if announce:
            self.status_text.configure(text="Tablero reiniciado. Esperando respuesta del servidor...")
        else:
            self.status_text.configure(text="El oponente pidió un reinicio. Preparando un nuevo tablero...")

        self.last_move_text.configure(text="Último movimiento: ninguno")
        self._refresh_turn_chip()

    def _apply_move(self, cell_index, remote=False):
        """Aplica una jugada al tablero, valida victoria y alterna el turno."""
        z, y, x = self._index_to_coords(cell_index)
        if self.board_state[z][y][x] != 0:
            return

        # Se usa 1 y -1 para que una línea ganadora sume +4 o -4 sin lógica adicional.
        mark_value = 1 if self.turn_owner == 0 else -1
        mark_label = "O" if mark_value == 1 else "X"
        mark_color = MOVE_O if mark_value == 1 else MOVE_X

        self.board_state[z][y][x] = mark_value
        button = self.cell_buttons[cell_index]
        button.configure(text=mark_label, fg=mark_color, bg="#172033")

        self.last_move_text.configure(text=f"Último movimiento: Nivel {z + 1}, fila {y + 1}, columna {x + 1}")

        winner_line = self._find_winner_line()
        if winner_line is not None:
            self.match_over = True
            self.current_winner_line = winner_line
            self._paint_win_line(winner_line)

            winner_name = "Jugador 1" if mark_value == 1 else "Jugador 2"
            self.status_text.configure(text=f"{winner_name} ganó la partida.")
            self.turn_chip.configure(text="Turno: partida cerrada", bg="#7c2d12")
            if not remote:
                messagebox.showinfo("Victoria", f"{winner_name} ganó la partida.")
            return

        if self._board_is_full():
            self.match_over = True
            self.status_text.configure(text="Empate. El tablero quedó lleno.")
            self.turn_chip.configure(text="Turno: empate", bg="#78350f")
            return

        self.turn_owner = 1 - self.turn_owner
        self._refresh_turn_chip()

        if remote:
            self.status_text.configure(text="El rival hizo su jugada. Es tu turno." if self.turn_owner == self.seat else "El rival movió la ficha.")
        else:
            self.status_text.configure(text="Movimiento enviado al servidor.")

    def _find_winner_line(self):
        """Busca si alguna de las líneas ganadoras precomputadas ya quedó completa."""
        for line in self.win_lines:
            total = 0
            for z, y, x in line:
                total += self.board_state[z][y][x]
            if abs(total) == BOARD_SIZE:
                return line
        return None

    def _paint_win_line(self, line):
        """Resalta en la interfaz las celdas que forman la línea vencedora."""
        for z, y, x in line:
            index = z * 16 + y * 4 + x
            self.cell_buttons[index].configure(bg=CELL_WIN, fg="#0f172a")

    def _board_is_full(self):
        """Comprueba si no quedan celdas vacías en ninguna capa."""
        for layer in self.board_state:
            for row in layer:
                for cell in row:
                    if cell == 0:
                        return False
        return True

    def _reset_board_visuals(self):
        """Deja la interfaz en un estado inicial mientras se establece la conexión."""
        self._reset_board(announce=False)
        self.status_text.configure(text="Conectando al servidor...")

    def exit_app(self):
        """Cierra la conexión en curso y destruye la ventana principal."""
        self.network_stop.set()
        self.root.destroy()


def main():
    """Punto de entrada del cliente de escritorio."""
    root = tk.Tk()
    app = SpatialTicTacToeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
