

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from LOGIC.pythonLexer.analizador import analizar_codigo
from LOGIC.pythonLexer.tabla_simbolos import VariableTableBuilder

class TextoConNumeros(tk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, bg="#171329")

        self.numeros = tk.Canvas(self, width=45, bg="#171329", highlightthickness=0)
        self.numeros.pack(side="left", fill="y")

        scrollbar = tk.Scrollbar(self, troughcolor="#171329", bg="#3b2e65")
        scrollbar.pack(side="right", fill="y")

        self.texto = tk.Text(
            self, wrap="none", yscrollcommand=self._on_scroll,
            bg="#171329", fg="#f4f0ff", insertbackground="#f48fb1",
            selectbackground="#704fc4", relief="flat", padx=12, pady=10,
            font=("DejaVu Sans Mono", 11), **kwargs
        )
        self.texto.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._on_scrollbar)
        self.texto.bind("<KeyRelease>", self._redibujar)
        self.texto.bind("<ButtonRelease>", self._redibujar)
        self.texto.bind("<Configure>", self._redibujar)
        self.texto.bind("<MouseWheel>", self._redibujar)
        self.texto.bind("<Button-4>", self._redibujar)
        self.texto.bind("<Button-5>", self._redibujar)

    def _on_scroll(self, *args):
        self._scrollbar_set(*args)
        self._redibujar()

    def _on_scrollbar(self, *args):
        self.texto.yview(*args)
        self._redibujar()

    def _scrollbar_set(self, *args):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Scrollbar):
                widget.set(*args)

    def _redibujar(self, event=None):
        self.numeros.delete("all")

        indice = self.texto.index("@0,0")
        while True:
            info_linea = self.texto.dlineinfo(indice)
            if info_linea is None:
                break

            y = info_linea[1]
            numero_linea = indice.split(".")[0]
            self.numeros.create_text(
                38, y, anchor="ne", text=numero_linea,
                fill="#7d70a6", font=("DejaVu Sans Mono", 10)
            )
            indice = self.texto.index(f"{indice}+1line")

    def get(self, *args, **kwargs):
        return self.texto.get(*args, **kwargs)

    def insert(self, *args, **kwargs):
        resultado = self.texto.insert(*args, **kwargs)
        self._redibujar()
        return resultado

    def delete(self, *args, **kwargs):
        resultado = self.texto.delete(*args, **kwargs)
        self._redibujar()
        return resultado
    
class VentanaALexico:

    COLORES = {"fondo": "#171329", "borde": "#3b2e65"}


    def __init__(self, root: tk.Tk):
        self.root = root
        self.win_tokens = None
        self.win_simbolos = None
        self.win_errores = None
        self.tree_tokens = None
        self.tree_simbolos = None
        self.tree_errores = None

    # ---- construccion de cada ventana ----

    def _preparar_ventana(self, titulo, geometry):
        win = tk.Toplevel(self.root)
        win.title(titulo)
        win.geometry(geometry)
        win.minsize(1000, 650)
        win.configure(bg=self.COLORES["fondo"])
        win.withdraw()
        win.protocol("WM_DELETE_WINDOW", win.withdraw)
        return win

    def _crear_ventana_tokens(self):
        win = self._preparar_ventana("Tira de tokens", "1400x820")

        columnas = ("linea", "columna", "tipo", "lexema")
        tree = ttk.Treeview(win, columns=columnas, show="headings", style="Resultados.Treeview")
        tree.heading("linea", text="Fila")
        tree.heading("columna", text="Columna")
        tree.heading("tipo", text="Token")
        tree.heading("lexema", text="Valor lexico (lexema)")
        tree.column("linea", width=90, anchor="center")
        tree.column("columna", width=100, anchor="center")
        tree.column("tipo", width=220)
        tree.column("lexema", width=360)
        tree.pack(fill="both", expand=True, padx=18, pady=18)

        win.protocol("WM_DELETE_WINDOW", win.withdraw)
        self.win_tokens = win
        self.tree_tokens = tree

    def _crear_ventana_simbolos(self):
        win = self._preparar_ventana("Tabla de simbolos", "920x720")

        columnas = ("linea", "nombre")
        tree = ttk.Treeview(win, columns=columnas, show="headings", style="Resultados.Treeview")
        tree.heading("linea", text="Fila")
        tree.heading("nombre", text="Identificador")
        tree.column("linea", width=120, anchor="center")
        tree.column("nombre", width=360)
        tree.pack(fill="both", expand=True, padx=18, pady=18)

        win.protocol("WM_DELETE_WINDOW", win.withdraw)
        self.win_simbolos = win
        self.tree_simbolos = tree

    def _crear_ventana_errores(self):
        win = self._preparar_ventana("Tabla de errores", "1240x720")

        columnas = ("linea", "columna", "descripcion")
        tree = ttk.Treeview(win, columns=columnas, show="headings", style="Errores.Treeview")
        tree.heading("linea", text="Linea")
        tree.heading("columna", text="Columna")
        tree.heading("descripcion", text="Descripcion")
        tree.column("linea", width=100, anchor="center")
        tree.column("columna", width=110, anchor="center")
        tree.column("descripcion", width=700)
        tree.pack(fill="both", expand=True, padx=18, pady=18)

        win.protocol("WM_DELETE_WINDOW", win.withdraw)
        self.win_errores = win
        self.tree_errores = tree


    def mostrar(self, tokens, simbolos, errores):
        # Vacia y vuelve a llenar las 3 tablas con los resultados del ultimo analisis
        self._mostrar_tokens(tokens)
        self._mostrar_simbolos(simbolos)
        self._mostrar_errores(errores)

    def _mostrar_tokens(self, tokens):
        if self.win_tokens is None or not self.win_tokens.winfo_exists():
            self._crear_ventana_tokens()

        self.tree_tokens.delete(*self.tree_tokens.get_children())
        for token in tokens:
            self.tree_tokens.insert(
                "", "end",
                values=(token.line, token.column, token.type.name, token.value)
            )

    def _mostrar_simbolos(self, simbolos):
        if self.win_simbolos is None or not self.win_simbolos.winfo_exists():
            self._crear_ventana_simbolos()

        self.tree_simbolos.delete(*self.tree_simbolos.get_children())
        for variable in simbolos.values():
            self.tree_simbolos.insert(
                "", "end", values=(variable.line, variable.name)
            )

    def _mostrar_errores(self, errores):
        if self.win_errores is None or not self.win_errores.winfo_exists():
            self._crear_ventana_errores()

        self.tree_errores.delete(*self.tree_errores.get_children())
        for error in errores:
            self.tree_errores.insert(
                "", "end", values=(
                    error["linea"], error.get("columna", "-"), error["descripcion"]
                )
            )

    def abrir(self, tipo):
        ventanas = {
            "tokens": self.win_tokens,
            "simbolos": self.win_simbolos,
            "errores": self.win_errores,
        }
        ventana = ventanas[tipo]
        if ventana is None or not ventana.winfo_exists():
            return
        ventana.deiconify()
        ventana.lift()
        try:
            ventana.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        self._desvanecer(ventana, 0.0)

    def _desvanecer(self, ventana, opacidad):
        if not ventana.winfo_exists():
            return
        try:
            ventana.attributes("-alpha", min(opacidad, 1.0))
        except tk.TclError:
            return
        if opacidad < 1.0:
            ventana.after(18, self._desvanecer, ventana, opacidad + 0.08)

    def limpiar(self):
        for tree in (self.tree_tokens, self.tree_simbolos, self.tree_errores):
            if tree is not None:
                tree.delete(*tree.get_children())


class VentanaPrincipal:
    COLORES = {
        "fondo": "#100d20", "panel": "#19142f", "editor": "#171329",
        "texto": "#f4f0ff", "muted": "#a99bcf", "rosa": "#f48fb1",
        "azul": "#7dd3fc", "morado": "#a78bfa", "verde": "#86efac",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Lumen Pascal - Analizador lexico")
        root.geometry("1380x900")
        root.minsize(1180, 760)
        root.configure(bg=self.COLORES["fondo"])
        self._establecer_maximizada(True)
        root.bind("<F11>", self._alternar_pantalla_completa)
        root.bind("<Escape>", self._salir_pantalla_completa)

        self.ventana_resultados = VentanaALexico(root)
        self.ruta_archivo = None

        self._configurar_estilos()
        self._construir_widgets()
        self.root.after(100, self._entrada_animada)

    def _establecer_maximizada(self, maximizada):
        try:
            self.root.state("zoomed" if maximizada else "normal")
        except tk.TclError:
            self.root.attributes("-zoomed", maximizada)

    def _alternar_pantalla_completa(self, event=None):
        try:
            esta_maximizada = self.root.state() == "zoomed"
        except tk.TclError:
            esta_maximizada = bool(self.root.attributes("-zoomed"))
        self._establecer_maximizada(not esta_maximizada)

    def _salir_pantalla_completa(self, event=None):
        self._establecer_maximizada(False)

    def _configurar_estilos(self):
        estilo = ttk.Style(self.root)
        estilo.theme_use("clam")
        estilo.configure(
            "Resultados.Treeview", background="#211a3d", foreground="#f4f0ff",
            fieldbackground="#211a3d", rowheight=36, borderwidth=0,
            font=("DejaVu Sans", 11)
        )
        estilo.configure(
            "Resultados.Treeview.Heading", background="#3b2e65",
            foreground="#f4f0ff", font=("DejaVu Sans", 11, "bold"), padding=10
        )
        estilo.map("Resultados.Treeview", background=[("selected", "#704fc4")])
        estilo.configure(
            "Errores.Treeview", background="#351b32", foreground="#ffe8ef",
            fieldbackground="#351b32", rowheight=38, borderwidth=0,
            font=("DejaVu Sans", 11)
        )
        estilo.configure(
            "Errores.Treeview.Heading", background="#a83d68",
            foreground="#ffffff", font=("DejaVu Sans", 11, "bold"), padding=10
        )
        estilo.map("Errores.Treeview", background=[("selected", "#d45a87")])

    def _construir_widgets(self):
        self.contenido = tk.Frame(self.root, bg=self.COLORES["fondo"])
        self.contenido.pack(fill="both", expand=True, padx=30, pady=24)
        cabecera = tk.Frame(self.contenido, bg=self.COLORES["fondo"])
        cabecera.pack(fill="x")
        tk.Label(cabecera, text="LUMEN / PASCAL", bg=self.COLORES["fondo"], fg=self.COLORES["azul"], font=("DejaVu Sans", 10, "bold")).pack(anchor="w")
        tk.Label(cabecera, text="Analizador lexico", bg=self.COLORES["fondo"], fg=self.COLORES["texto"], font=("DejaVu Sans", 27, "bold")).pack(anchor="w", pady=(3, 0))
        tk.Label(cabecera, text="Escribe, carga tu programa y explora cada resultado a tu ritmo.", bg=self.COLORES["fondo"], fg=self.COLORES["muted"], font=("DejaVu Sans", 11)).pack(anchor="w", pady=(2, 18))

        barra = tk.Frame(self.contenido, bg=self.COLORES["panel"], padx=12, pady=12)
        barra.pack(fill="x")
        self._boton(barra, "Abrir archivo", self.abrir_archivo, self.COLORES["azul"]).pack(side="left", padx=(0, 8))
        self._boton(barra, "Analizar codigo", self.analizar, self.COLORES["rosa"]).pack(side="left", padx=8)
        self._boton(barra, "Limpiar", self.limpiar, self.COLORES["muted"]).pack(side="left", padx=8)
        self.lbl_estado = tk.Label(barra, text="Listo para analizar", bg=self.COLORES["panel"], fg=self.COLORES["verde"], font=("DejaVu Sans", 10, "bold"))
        self.lbl_estado.pack(side="right", padx=8)

        self.lbl_archivo = tk.Label(self.contenido, text="  Ningun archivo cargado", anchor="w", bg=self.COLORES["fondo"], fg=self.COLORES["muted"], font=("DejaVu Sans", 10))
        self.lbl_archivo.pack(fill="x", pady=(16, 8))
        frame_texto = tk.Frame(self.contenido, bg=self.COLORES["editor"], highlightthickness=1, highlightbackground="#3b2e65")
        frame_texto.pack(fill="both", expand=True)

        self.texto_codigo = TextoConNumeros(frame_texto)
        self.texto_codigo.pack(fill="both", expand=True)

        pie = tk.Frame(self.contenido, bg=self.COLORES["fondo"])
        pie.pack(fill="x", pady=(14, 0))
        tk.Label(pie, text="RESULTADOS", bg=self.COLORES["fondo"], fg=self.COLORES["muted"], font=("DejaVu Sans", 9, "bold")).pack(side="left")
        self.botones_resultados = tk.Frame(pie, bg=self.COLORES["fondo"])
        self.botones_resultados.pack(side="right")
        self._boton_resultado("Tokens", "tokens", self.COLORES["azul"])
        self._boton_resultado("Simbolos", "simbolos", self.COLORES["morado"])
        self._boton_resultado("Errores", "errores", self.COLORES["rosa"])

    def _boton(self, parent, texto, comando, color):
        boton = tk.Button(parent, text=texto, command=comando, bg=color, fg="#160f2d", activebackground="#ffffff", activeforeground="#160f2d", relief="flat", cursor="hand2", padx=18, pady=10, font=("DejaVu Sans", 11, "bold"), borderwidth=0, highlightthickness=0)
        boton.bind("<Enter>", lambda event: boton.configure(bg="#ffffff"))
        boton.bind("<Leave>", lambda event: boton.configure(bg=color))
        return boton

    def _boton_resultado(self, texto, tipo, color):
        boton = tk.Button(self.botones_resultados, text=texto, command=lambda: self.ventana_resultados.abrir(tipo), bg=self.COLORES["panel"], fg=color, activebackground="#3b2e65", activeforeground="#ffffff", relief="flat", cursor="hand2", padx=16, pady=8, font=("DejaVu Sans", 10, "bold"), borderwidth=0, highlightthickness=1, highlightbackground="#3b2e65")
        boton.bind("<Enter>", lambda event: boton.configure(bg="#3b2e65"))
        boton.bind("<Leave>", lambda event: boton.configure(bg=self.COLORES["panel"]))
        boton.pack(side="left", padx=(8, 0))

    def _entrada_animada(self):
        self.contenido.pack_configure(pady=10)
        self.root.after(35, lambda: self.contenido.pack_configure(pady=24))

    # ---- acciones de los botones ----

    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Selecciona un programa Pascal",
            filetypes=[("Archivos Pascal", "*.pas"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
        except OSError as error:
            messagebox.showerror("Error al abrir archivo", str(error))
            return

        self.ruta_archivo = ruta
        self.texto_codigo.delete("1.0", "end")
        self.texto_codigo.insert("1.0", contenido)
        self.lbl_archivo.config(text=f"  {os.path.basename(ruta)}", fg=self.COLORES["azul"])
        self.lbl_estado.config(text="Archivo cargado", fg=self.COLORES["verde"])

    def analizar(self):
        codigo = self.texto_codigo.get("1.0", "end-1c")

        if not codigo.strip():
            messagebox.showwarning("Sin codigo", "Primero abre o escribe un programa fuente.")
            return

        resultado = analizar_codigo(codigo)

        constructor_simbolos = VariableTableBuilder(codigo)
        simbolos = constructor_simbolos.build_from_tokens(resultado["tokens"])

        self.ventana_resultados.mostrar(
            tokens=resultado["tokens"],
            simbolos=simbolos,
            errores=resultado["errores"],
        )
        self.lbl_estado.config(
            text=f"{len(resultado['tokens'])} tokens - {len(resultado['errores'])} errores",
            fg=self.COLORES["rosa"] if resultado["errores"] else self.COLORES["verde"],
        )

        if resultado["errores"]:
            messagebox.showinfo(
                "Analisis terminado",
                f"Se encontraron {len(resultado['errores'])} error(es) lexico(s)."
            )

    def limpiar(self):
        self.texto_codigo.delete("1.0", "end")
        self.lbl_archivo.config(text="  Ningun archivo cargado", fg=self.COLORES["muted"])
        self.lbl_estado.config(text="Listo para analizar", fg=self.COLORES["verde"])
        self.ruta_archivo = None
        self.ventana_resultados.limpiar()


def main():
    root = tk.Tk()
    VentanaPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    main()
