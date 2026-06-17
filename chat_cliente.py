# Pérez Hernández Ricardo — Práctica 8: Contenedores y Microservicios
# ─────────────────────────────────────────────────────────────────────────────
# chat_cliente.py  —  Cliente de Chat Distribuido (Tkinter)
# Integración con 6 Microservicios (Chat, Notas, Auth, Media, Geo, Logger)
# ─────────────────────────────────────────────────────────────────────────────
import requests
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog
import queue
import os

# ── Endpoints Locales (Docker Desktop) ───────────────────────────────────────
URL_CHAT   = "http://localhost:9000"
URL_NOTAS  = "http://localhost:8000"
URL_AUTH   = "http://localhost:8001"
URL_MEDIA  = "http://localhost:8002"
URL_GEO    = "http://localhost:8003"
URL_LOGGER = "http://localhost:7000"

POLL_INTERVAL      = 1.0
HEARTBEAT_INTERVAL = 5.0

# ── Funciones Globales de Telemetría ─────────────────────────────────────────
def registrar_log(servicio: str, nivel: str, mensaje: str):
    """Envía un registro al sumidero central (Logger API)"""
    try:
        requests.post(f"{URL_LOGGER}/log", json={
            "service": servicio, "level": nivel, "message": mensaje
        }, timeout=2)
    except:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# CLASES DE CONEXIÓN A MICROSERVICIOS
# ─────────────────────────────────────────────────────────────────────────────
class ChatCliente:
    def __init__(self, usuario: str):
        self.usuario   = usuario
        self.ultimo_id = 0

    def unirse(self) -> bool:
        try:
            r = requests.post(f"{URL_CHAT}/unirse", json={'usuario': self.usuario}, timeout=5)
            if r.ok: registrar_log("chat-client", "INFO", f"{self.usuario} conectó al servidor de chat.")
            return r.ok
        except Exception:
            return False

    def salir(self):
        try:
            requests.delete(f"{URL_CHAT}/salir", json={'usuario': self.usuario}, timeout=3)
        except:
            pass

    def enviar(self, texto: str) -> bool:
        try:
            r = requests.post(f"{URL_CHAT}/mensajes", json={'usuario': self.usuario, 'texto': texto}, timeout=5)
            return r.ok
        except Exception:
            return False

    def obtener_nuevos(self) -> list:
        try:
            r = requests.get(f"{URL_CHAT}/mensajes", params={'desde': self.ultimo_id}, timeout=5)
            if not r.ok: return []
            nuevos = r.json().get('mensajes', [])
            if nuevos: self.ultimo_id = nuevos[-1]['id']
            return nuevos
        except:
            return []

    def obtener_usuarios(self) -> list:
        try:
            r = requests.get(f"{URL_CHAT}/usuarios", timeout=5)
            return r.json().get('usuarios', []) if r.ok else []
        except:
            return []

    def heartbeat(self):
        try:
            requests.post(f"{URL_CHAT}/heartbeat", json={'usuario': self.usuario}, timeout=3)
        except:
            pass

class NotasCliente:
    def __init__(self, usuario: str):
        self.usuario = usuario

    def agregar(self, titulo: str, nota: str) -> bool:
        try:
            r = requests.post(f"{URL_NOTAS}/{self.usuario}", json={"title": titulo, "note": nota}, timeout=5)
            if r.status_code == 201:
                registrar_log("notes-api", "INFO", f"{self.usuario} creó la nota: {titulo}")
                return True
            return False
        except:
            return False

    def listar(self) -> list:
        try:
            r = requests.get(f"{URL_NOTAS}/{self.usuario}", timeout=5)
            return r.json() if r.status_code == 200 else []
        except:
            return []

# ─────────────────────────────────────────────────────────────────────────────
# GUI TKINTER
# ─────────────────────────────────────────────────────────────────────────────
class ChatGUI:
    def __init__(self, root: tk.Tk, cliente_chat: ChatCliente, cliente_notas: NotasCliente):
        self.root = root
        self.cliente = cliente_chat
        self.notas = cliente_notas
        self.cola = queue.Queue()

        self._construir_ui()
        self._iniciar_hilos()
        self.root.after(200, self._procesar_cola)

    def _construir_ui(self):
        self.root.title(f"Sistema Distribuido — {self.cliente.usuario}")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)

        barra = tk.Frame(self.root, bg='#16213e', pady=6)
        barra.pack(fill='x')

        tk.Label(barra, text="💬 ECOSISTEMA MICROSERVICIOS", font=("Consolas", 11, "bold"),
                 bg='#16213e', fg='#00d4ff').pack(side='left', padx=12)
        self.lbl_usuario = tk.Label(barra, text=f"● {self.cliente.usuario}",
                                    font=("Consolas", 9), bg='#16213e', fg='#00ff88')
        self.lbl_usuario.pack(side='right', padx=12)

        contenido = tk.Frame(self.root, bg='#1a1a2e')
        contenido.pack(fill='both', expand=True, padx=8, pady=(6, 0))

        frame_msgs = tk.Frame(contenido, bg='#1a1a2e')
        frame_msgs.pack(side='left', fill='both', expand=True)

        tk.Label(frame_msgs, text="COMANDOS: /nota add  |  /nota list  |  /media  |  /geo  |  /alerta",
                 font=("Consolas", 8, "bold"), bg='#1a1a2e', fg='#d2a8ff').pack(anchor='w')

        self.txt_mensajes = scrolledtext.ScrolledText(
            frame_msgs, width=65, height=22, font=("Consolas", 9),
            bg='#0d1117', fg='#c9d1d9', insertbackground='white',
            relief='flat', bd=0, state='disabled'
        )
        self.txt_mensajes.pack(fill='both', expand=True)
        self.txt_mensajes.tag_config('sistema', foreground='#555577')
        self.txt_mensajes.tag_config('notas',   foreground='#d2a8ff')
        self.txt_mensajes.tag_config('alerta',  foreground='#ff4d4d', font=("Consolas", 9, "bold"))
        self.txt_mensajes.tag_config('propio',  foreground='#79c0ff')
        self.txt_mensajes.tag_config('otro',    foreground='#56d364')
        self.txt_mensajes.tag_config('hora',    foreground='#444466')

        frame_lat = tk.Frame(contenido, bg='#16213e', width=160, padx=8)
        frame_lat.pack(side='right', fill='y', padx=(8, 0))
        frame_lat.pack_propagate(False)

        tk.Label(frame_lat, text="CONECTADOS", font=("Consolas", 8, "bold"),
                 bg='#16213e', fg='#00d4ff').pack(anchor='w', pady=(6, 2))
        self.lst_usuarios = tk.Listbox(frame_lat, font=("Consolas", 9), bg='#0d1117',
                                       fg='#00ff88', selectbackground='#21262d',
                                       relief='flat', bd=0, activestyle='none')
        self.lst_usuarios.pack(fill='both', expand=True)

        tk.Label(self.root, text="PETICIONES HTTP", font=("Consolas", 7),
                 bg='#1a1a2e', fg='#555577').pack(anchor='w', padx=8)
        self.txt_http = tk.Text(self.root, height=4, width=80, font=("Consolas", 7),
                                bg='#0d1117', fg='#6e7681', relief='flat', bd=0, state='disabled')
        self.txt_http.pack(fill='x', padx=8, pady=(0, 4))

        frame_entrada = tk.Frame(self.root, bg='#21262d', pady=6)
        frame_entrada.pack(fill='x', padx=8, pady=(0, 8))

        self.entrada = tk.Entry(frame_entrada, font=("Consolas", 10), bg='#21262d',
                                fg='white', insertbackground='white', relief='flat', bd=4)
        self.entrada.pack(side='left', fill='x', expand=True, ipady=4)
        self.entrada.bind('<Return>', self._procesar_entrada)
        self.entrada.focus()

    def _iniciar_hilos(self):
        threading.Thread(target=self._hilo_polling,   daemon=True).start()
        threading.Thread(target=self._hilo_heartbeat, daemon=True).start()

    def _hilo_polling(self):
        while True:
            nuevos = self.cliente.obtener_nuevos()
            for msg in nuevos:
                self.cola.put(('mensaje', msg))
            
            if int(time.time()) % 3 == 0:
                usuarios = self.cliente.obtener_usuarios()
                self.cola.put(('usuarios', usuarios))

            time.sleep(POLL_INTERVAL)

    def _hilo_heartbeat(self):
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            self.cliente.heartbeat()

    def _procesar_cola(self):
        try:
            while not self.cola.empty():
                tipo, datos = self.cola.get_nowait()
                if tipo == 'mensaje':  self._mostrar_mensaje(datos)
                elif tipo == 'usuarios': self._actualizar_usuarios(datos)
        except queue.Empty:
            pass
        self.root.after(200, self._procesar_cola)

    def _mostrar_mensaje(self, msg: dict):
        self.txt_mensajes.config(state='normal')
        hora = msg.get('timestamp', time.strftime('%H:%M:%S'))
        usr  = msg.get('usuario', '')
        txt  = msg.get('texto', '')

        if usr == 'SISTEMA':
            self.txt_mensajes.insert('end', f"  {txt}\n", 'sistema')
        elif usr == 'API_NOTAS':
            self.txt_mensajes.insert('end', f"[{hora}] 📝 {txt}\n", 'notas')
        elif '🚨' in txt or '📍' in txt:
            self.txt_mensajes.insert('end', f"[{hora}] {usr}: {txt}\n", 'alerta')
        elif usr == self.cliente.usuario:
            self.txt_mensajes.insert('end', f"[{hora}] Tú: {txt}\n", 'propio')
        else:
            self.txt_mensajes.insert('end', f"[{hora}] {usr}: {txt}\n", 'otro')

        self.txt_mensajes.config(state='disabled')
        self.txt_mensajes.see('end')

    def _actualizar_usuarios(self, usuarios: list):
        self.lst_usuarios.delete(0, 'end')
        for u in usuarios:
            prefijo = "► " if u == self.cliente.usuario else "  "
            self.lst_usuarios.insert('end', f"{prefijo}{u}")

    def _log_http(self, texto: str):
        self.txt_http.config(state='normal')
        self.txt_http.insert('end', f"{time.strftime('%H:%M:%S')} {texto}\n")
        self.txt_http.config(state='disabled')
        self.txt_http.see('end')

    def _procesar_entrada(self, event=None):
        texto = self.entrada.get().strip()
        if not texto: return
        self.entrada.delete(0, 'end')

        if texto.startswith('/nota'):
            self._manejar_api_notas(texto)
        elif texto.startswith('/media'):
            self._manejar_media()
        elif texto.startswith('/geo'):
            self._manejar_geo()
        elif texto.startswith('/alerta'):
            self._manejar_alerta()
        else:
            if self.cliente.enviar(texto):
                self._log_http(f"POST Chat /mensajes → 200 OK")

    def _manejar_media(self):
        filepath = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not filepath: return
        
        self._log_http(f"POST Media /upload/image → Subiendo {os.path.basename(filepath)}")
        try:
            with open(filepath, 'rb') as f:
                r = requests.post(f"{URL_MEDIA}/upload/image", files={'file': f}, timeout=10)
            
            if r.ok:
                url_storage = r.json().get('storage_url', '')
                self.cliente.enviar(f"🖼️ [IMAGEN SUPABASE] {url_storage}")
                registrar_log("media-api", "INFO", f"Blob persistido en Supabase para {self.cliente.usuario}")
        except Exception as e:
            self._log_http(f"ERROR MEDIA API: {e}")

    def _manejar_geo(self):
        payload = {"usuario": self.cliente.usuario, "lat": 19.362, "lng": -99.294} # Coordenadas Cuajimalpa
        self._log_http(f"POST Geo /location → {payload}")
        try:
            r = requests.post(f"{URL_GEO}/location", json=payload, timeout=5)
            if r.ok:
                self.cliente.enviar("📍 Se ha actualizado mi ubicación en el mapa (Cuajimalpa CDMX).")
                registrar_log("geo-api", "INFO", f"Coordenadas actualizadas para {self.cliente.usuario}")
        except Exception as e:
            self._log_http(f"ERROR GEO API: {e}")

    def _manejar_alerta(self):
        payload = {"usuario": self.cliente.usuario, "tipo_alerta": "PÁNICO", "audio_stream_url": "wss://stream.audio.local/live"}
        self._log_http(f"POST Geo /emergency → {payload}")
        try:
            r = requests.post(f"{URL_GEO}/emergency", json=payload, timeout=5)
            if r.ok:
                self.cliente.enviar("🚨 ¡ALERTA DE EMERGENCIA DETONADA! Iniciando streaming de audio.")
                registrar_log("geo-api", "WARNING", f"Alerta de pánico disparada por {self.cliente.usuario}")
        except Exception as e:
            self._log_http(f"ERROR GEO API: {e}")

    def _manejar_api_notas(self, texto: str):
        partes = texto.split(' ', 2)
        comando = partes[1] if len(partes) > 1 else ''

        if comando == 'add' and len(partes) > 2:
            datos = partes[2].split('|', 1)
            titulo = datos[0].strip()
            contenido = datos[1].strip() if len(datos) > 1 else "Sin descripción"
            if self.notas.agregar(titulo, contenido):
                self._log_http(f"POST Notas /{self.cliente.usuario} → 201 Created")
        elif comando == 'list':
            notas = self.notas.listar()
            if notas:
                for n in notas:
                    self.cola.put(('mensaje', {'usuario': 'API_NOTAS', 'texto': f"ID {n['id']}: {n['title']}"}))
            self._log_http(f"GET Notas /{self.cliente.usuario} → 200 OK")

def main():
    root_login = tk.Tk()
    root_login.withdraw()
    usuario = simpledialog.askstring("Sistema Distribuido", "Ingresa tu usuario (Ej. Ricardo):", parent=root_login)
    root_login.destroy()

    if not usuario or not usuario.strip(): return
    usuario = usuario.strip()

    # Intento de Auth
    try:
        r = requests.post(f"{URL_AUTH}/login", json={"usuario": "Ricardo", "password": "123"}, timeout=3)
        registrar_log("auth-api", "INFO", f"Intento de inicio de sesión de {usuario}")
    except: pass

    cliente_chat  = ChatCliente(usuario)
    cliente_notas = NotasCliente(usuario)

    if not cliente_chat.unirse():
        messagebox.showerror("Error", "No se pudo contactar al servidor de chat local.\nVerifica Docker Compose.")
        return

    root = tk.Tk()
    app  = ChatGUI(root, cliente_chat, cliente_notas)
    root.protocol("WM_DELETE_WINDOW", lambda: (cliente_chat.salir(), root.destroy()))
    root.mainloop()

if __name__ == '__main__':
    main()