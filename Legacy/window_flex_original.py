import csv
import io
import subprocess
import sys
import unicodedata
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


ESTILO_APLICACION = """
QMainWindow, QWidget {
    background-color: #f4f7fb;
    color: #172033;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 14px;
}

QFrame#encabezado {
    background-color: #173b65;
    border-radius: 12px;
}

QLabel#titulo {
    background-color: transparent;
    color: white;
    font-size: 26px;
    font-weight: 700;
}

QLabel#subtitulo {
    background-color: transparent;
    color: #d9e8f7;
    font-size: 13px;
}

QFrame#tarjeta {
    background-color: white;
    border: 1px solid #d9e2ec;
    border-radius: 10px;
}

QLabel#tituloSeccion {
    color: #173b65;
    font-size: 15px;
    font-weight: 700;
}

QPlainTextEdit {
    background-color: #fbfdff;
    border: 1px solid #c8d4e3;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #80bfff;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 13px;
}

QPlainTextEdit:focus, QComboBox:focus {
    border: 2px solid #2b78c5;
}

QPushButton {
    background-color: #2b78c5;
    color: white;
    border: none;
    border-radius: 7px;
    padding: 9px 16px;
    font-weight: 600;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #2367aa;
}

QPushButton:pressed {
    background-color: #194f84;
}

QPushButton:disabled {
    background-color: #aebdca;
    color: #edf2f7;
}

QPushButton#botonEjecutar {
    background-color: #138a61;
}

QPushButton#botonEjecutar:hover {
    background-color: #0f7351;
}

QPushButton#botonResultado {
    background-color: #7b4cc2;
}

QPushButton#botonResultado:hover {
    background-color: #653ca5;
}

QComboBox {
    background-color: white;
    border: 1px solid #c8d4e3;
    border-radius: 7px;
    padding: 8px 10px;
    min-width: 210px;
}

QLabel#estado {
    background-color: #e8f1fb;
    color: #234a70;
    border-radius: 6px;
    padding: 7px 10px;
}

QTableWidget {
    background-color: white;
    alternate-background-color: #eef4fa;
    border: 1px solid #c8d4e3;
    border-radius: 7px;
    gridline-color: #d9e2ec;
    selection-background-color: #cfe7ff;
    selection-color: #172033;
}

QHeaderView::section {
    background-color: #173b65;
    color: white;
    border: none;
    border-right: 1px solid #31577f;
    padding: 8px;
    font-weight: 700;
}
"""


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ruta_flex = None
        self.ruta_fuente = None
        self.ruta_ejecutable = None
        self.resultados = {}
        self.ventanas_resultados = []

        self.setWindowTitle("Analizador léxico Flex")
        self.resize(1250, 820)
        self.setMinimumSize(980, 680)

        self.editor_flex = QPlainTextEdit()
        self.editor_flex.setPlaceholderText(
            "Abre un archivo .l para mostrar aquí el código Flex."
        )

        self.editor_fuente = QPlainTextEdit()
        self.editor_fuente.setPlaceholderText(
            "Abre un archivo .pas para mostrar aquí el programa Pascal."
        )

        self.salida_compilacion = QPlainTextEdit()
        self.salida_compilacion.setReadOnly(True)
        self.salida_compilacion.setMaximumHeight(190)
        self.salida_compilacion.setPlaceholderText(
            "Aquí aparecerán los mensajes producidos por Flex y GCC."
        )

        self.boton_abrir_flex = QPushButton("Abrir archivo Flex")
        self.boton_compilar = QPushButton("Compilar")
        self.boton_abrir_fuente = QPushButton("Abrir archivo fuente")
        self.boton_ejecutar = QPushButton("Ejecutar analizador léxico")
        self.boton_ejecutar.setObjectName("botonEjecutar")

        self.selector_resultado = QComboBox()
        self.selector_resultado.addItems(
            ["Tira de tokens", "Tabla de símbolos", "Tabla de errores"]
        )
        self.selector_resultado.setEnabled(False)

        self.boton_abrir_resultado = QPushButton("Abrir resultado")
        self.boton_abrir_resultado.setObjectName("botonResultado")
        self.boton_abrir_resultado.setEnabled(False)

        self.etiqueta_estado = QLabel(
            "Abre un archivo Flex para comenzar."
        )
        self.etiqueta_estado.setObjectName("estado")

        self.boton_abrir_flex.clicked.connect(self.abrir_flex)
        self.boton_compilar.clicked.connect(self.compilar)
        self.boton_abrir_fuente.clicked.connect(self.abrir_fuente)
        self.boton_ejecutar.clicked.connect(self.ejecutar)
        self.boton_abrir_resultado.clicked.connect(
            self.abrir_resultado_seleccionado
        )

        contenedor = QWidget()
        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(12)

        encabezado = QFrame()
        encabezado.setObjectName("encabezado")
        layout_encabezado = QVBoxLayout(encabezado)
        layout_encabezado.setContentsMargins(20, 14, 20, 14)

        titulo = QLabel("Analizador léxico")
        titulo.setObjectName("titulo")
        subtitulo = QLabel(
            "Analizador léxico construido con Flex y GCC"
        )
        subtitulo.setObjectName("subtitulo")
        layout_encabezado.addWidget(titulo)
        layout_encabezado.addWidget(subtitulo)
        layout_principal.addWidget(encabezado)

        barra = QHBoxLayout()
        barra.setSpacing(8)
        barra.addWidget(self.boton_abrir_flex)
        barra.addWidget(self.boton_compilar)
        barra.addSpacing(14)
        barra.addWidget(self.boton_abrir_fuente)
        barra.addWidget(self.boton_ejecutar)
        barra.addStretch()
        layout_principal.addLayout(barra)

        tarjeta_editores = QFrame()
        tarjeta_editores.setObjectName("tarjeta")
        editores = QGridLayout(tarjeta_editores)
        editores.setContentsMargins(12, 12, 12, 12)
        editores.setHorizontalSpacing(12)

        etiqueta_flex = QLabel("Código del analizador Flex")
        etiqueta_flex.setObjectName("tituloSeccion")
        etiqueta_fuente = QLabel("Programa fuente Pascal")
        etiqueta_fuente.setObjectName("tituloSeccion")

        editores.addWidget(etiqueta_flex, 0, 0)
        editores.addWidget(etiqueta_fuente, 0, 1)
        editores.addWidget(self.editor_flex, 1, 0)
        editores.addWidget(self.editor_fuente, 1, 1)
        editores.setColumnStretch(0, 1)
        editores.setColumnStretch(1, 1)
        editores.setRowStretch(1, 1)
        layout_principal.addWidget(tarjeta_editores, 1)

        tarjeta_salida = QFrame()
        tarjeta_salida.setObjectName("tarjeta")
        layout_salida = QVBoxLayout(tarjeta_salida)
        layout_salida.setContentsMargins(12, 10, 12, 12)
        etiqueta_salida = QLabel("Salida de compilación")
        etiqueta_salida.setObjectName("tituloSeccion")
        layout_salida.addWidget(etiqueta_salida)
        layout_salida.addWidget(self.salida_compilacion)
        layout_principal.addWidget(tarjeta_salida)

        barra_resultados = QHBoxLayout()
        barra_resultados.addWidget(self.etiqueta_estado, 1)
        barra_resultados.addWidget(QLabel("Resultado:"))
        barra_resultados.addWidget(self.selector_resultado)
        barra_resultados.addWidget(self.boton_abrir_resultado)
        layout_principal.addLayout(barra_resultados)

        self.setCentralWidget(contenedor)

    def actualizar_estado(self, mensaje, tipo="informacion"):
        colores = {
            "informacion": ("#e8f1fb", "#234a70"),
            "exito": ("#def7ec", "#116149"),
            "error": ("#fde8e8", "#9b1c1c"),
        }
        fondo, texto = colores.get(tipo, colores["informacion"])
        self.etiqueta_estado.setText(mensaje)
        self.etiqueta_estado.setStyleSheet(
            f"background-color: {fondo}; color: {texto}; "
            "border-radius: 6px; padding: 7px 10px;"
        )

    def limpiar_resultados(self):
        self.resultados.clear()
        self.selector_resultado.setEnabled(False)
        self.boton_abrir_resultado.setEnabled(False)

    def abrir_flex(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Flex",
            "",
            "Archivos Flex (*.l);;Todos los archivos (*)",
        )

        if not ruta:
            return

        try:
            contenido, codificacion = self.leer_archivo_normalizado(ruta)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el archivo Flex:\n{error}",
            )
            return

        self.ruta_flex = Path(ruta)
        self.ruta_ejecutable = None
        self.editor_flex.setPlainText(contenido)
        self.limpiar_resultados()
        self.actualizar_estado(
            f"Archivo Flex cargado ({codificacion}). Ahora puedes compilar.",
            "informacion",
        )

    def guardar_flex(self):
        if self.ruta_flex is None:
            return False

        try:
            self.ruta_flex.write_text(
                self.editor_flex.toPlainText(),
                encoding="utf-8",
            )
            return True
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el archivo Flex:\n{error}",
            )
            return False

    def compilar(self):
        if self.ruta_flex is None:
            QMessageBox.warning(
                self,
                "Falta archivo",
                "Primero abre un archivo Flex.",
            )
            return

        if not self.guardar_flex():
            return

        self.ruta_ejecutable = None
        self.limpiar_resultados()
        carpeta = self.ruta_flex.parent
        archivo_c = carpeta / "lex.yy.c"
        ejecutable = carpeta / "analizador"

        try:
            resultado_flex = subprocess.run(
                ["flex", "-o", str(archivo_c), str(self.ruta_flex)],
                cwd=carpeta,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            self.actualizar_estado("Flex no está instalado.", "error")
            QMessageBox.critical(
                self,
                "Flex no encontrado",
                "No se encontró Flex. Instálalo con:\n"
                "sudo apt install flex libfl-dev",
            )
            return
        except OSError as error:
            self.actualizar_estado("No fue posible ejecutar Flex.", "error")
            QMessageBox.critical(
                self,
                "Error al ejecutar Flex",
                str(error),
            )
            return

        salida = resultado_flex.stdout + resultado_flex.stderr

        if resultado_flex.returncode != 0:
            self.salida_compilacion.setPlainText(salida)
            self.actualizar_estado("Flex encontró errores.", "error")
            QMessageBox.critical(
                self,
                "Error de Flex",
                salida or "Flex no pudo generar lex.yy.c.",
            )
            return

        try:
            resultado_gcc = subprocess.run(
                [
                    "gcc",
                    "-Wall",
                    "-Wextra",
                    str(archivo_c),
                    "-o",
                    str(ejecutable),
                    "-lfl",
                ],
                cwd=carpeta,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            self.salida_compilacion.setPlainText(salida)
            self.actualizar_estado("GCC no está instalado.", "error")
            QMessageBox.critical(
                self,
                "GCC no encontrado",
                "No se encontró GCC. Instálalo con:\n"
                "sudo apt install gcc",
            )
            return
        except OSError as error:
            self.actualizar_estado("No fue posible ejecutar GCC.", "error")
            QMessageBox.critical(
                self,
                "Error al ejecutar GCC",
                str(error),
            )
            return

        salida += resultado_gcc.stdout + resultado_gcc.stderr
        self.salida_compilacion.setPlainText(
            salida if salida.strip() else "Compilación finalizada sin mensajes."
        )

        if resultado_gcc.returncode != 0:
            self.actualizar_estado("GCC encontró errores.", "error")
            QMessageBox.critical(
                self,
                "Error de compilación",
                salida or "GCC no pudo generar el ejecutable.",
            )
            return

        self.ruta_ejecutable = ejecutable
        self.actualizar_estado(
            "Compilación exitosa. Abre un archivo Pascal y ejecuta el analizador.",
            "exito",
        )
        QMessageBox.information(
            self,
            "Compilación exitosa",
            "El analizador léxico se compiló correctamente.",
        )

    def leer_archivo_normalizado(self, ruta):
        datos = Path(ruta).read_bytes()

        for codificacion in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                texto = datos.decode(codificacion)
            except UnicodeDecodeError:
                continue

            texto = unicodedata.normalize("NFC", texto)
            texto = texto.replace("\r\n", "\n").replace("\r", "\n")
            return texto, codificacion

        raise UnicodeError(
            "No se pudo determinar la codificación del archivo."
        )

    def abrir_fuente(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar programa Pascal",
            "",
            "Archivos Pascal (*.pas);;Todos los archivos (*)",
        )

        if not ruta:
            return

        try:
            contenido, codificacion = self.leer_archivo_normalizado(ruta)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el programa:\n{error}",
            )
            return

        self.ruta_fuente = Path(ruta)
        self.editor_fuente.setPlainText(contenido)
        self.limpiar_resultados()
        self.actualizar_estado(
            f"Programa Pascal cargado ({codificacion}).",
            "informacion",
        )

    def guardar_fuente(self):
        if self.ruta_fuente is None:
            return False

        try:
            self.ruta_fuente.write_text(
                self.editor_fuente.toPlainText(),
                encoding="utf-8",
            )
            return True
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el programa Pascal:\n{error}",
            )
            return False

    def ejecutar(self):
        if self.ruta_ejecutable is None or not self.ruta_ejecutable.exists():
            QMessageBox.warning(
                self,
                "Analizador no compilado",
                "Primero compila el archivo Flex.",
            )
            return

        if self.ruta_fuente is None:
            QMessageBox.warning(
                self,
                "Falta archivo fuente",
                "Primero abre un programa Pascal.",
            )
            return

        if not self.guardar_fuente():
            return

        self.limpiar_resultados()
        carpeta = self.ruta_ejecutable.parent

        try:
            resultado = subprocess.run(
                [str(self.ruta_ejecutable), str(self.ruta_fuente)],
                cwd=carpeta,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            self.actualizar_estado("El analizador no pudo ejecutarse.", "error")
            QMessageBox.critical(
                self,
                "Error de ejecución",
                f"No fue posible ejecutar el analizador:\n{error}",
            )
            return

        if resultado.returncode != 0:
            self.actualizar_estado("El analizador terminó con errores.", "error")
            QMessageBox.critical(
                self,
                "Error de ejecución",
                resultado.stderr
                or resultado.stdout
                or "El analizador terminó con un código de error.",
            )
            return

        try:
            self.resultados = {
                "Tira de tokens": self.leer_tsv(carpeta / "tiraTokens.tsv"),
                "Tabla de símbolos": self.leer_tsv(carpeta / "simbolos.tsv"),
                "Tabla de errores": self.leer_tsv(carpeta / "errores.tsv"),
            }
        except (OSError, csv.Error, UnicodeError) as error:
            self.limpiar_resultados()
            self.actualizar_estado(
                "No fue posible leer los archivos de resultados.",
                "error",
            )
            QMessageBox.critical(
                self,
                "Error de resultados",
                f"No fue posible leer los resultados:\n{error}",
            )
            return

        self.selector_resultado.setEnabled(True)
        self.boton_abrir_resultado.setEnabled(True)
        self.actualizar_estado(
            "Análisis finalizado. Selecciona el resultado que deseas abrir.",
            "exito",
        )
        QMessageBox.information(
            self,
            "Análisis finalizado",
            "Los resultados se generaron correctamente.\n\n"
            "Selecciona una tabla en la parte inferior y presiona "
            "“Abrir resultado”.",
        )

    def leer_tsv(self, ruta):
        texto, _ = self.leer_archivo_normalizado(ruta)
        lector = csv.reader(io.StringIO(texto), delimiter="\t")
        return list(lector)

    def abrir_resultado_seleccionado(self):
        titulo = self.selector_resultado.currentText()
        datos = self.resultados.get(titulo)

        if datos is None:
            QMessageBox.warning(
                self,
                "Resultado no disponible",
                "Ejecuta primero el analizador léxico.",
            )
            return

        self.mostrar_tabla(titulo, datos)

    def mostrar_tabla(self, titulo, datos):
        ventana = QWidget()
        ventana.setWindowTitle(f"Lumen Pascal | {titulo}")
        ventana.resize(780, 520)
        ventana.setMinimumSize(560, 360)

        layout = QVBoxLayout(ventana)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        encabezado = QLabel(titulo)
        encabezado.setObjectName("tituloSeccion")
        layout.addWidget(encabezado)

        tabla = QTableWidget()
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        if datos:
            encabezados = datos[0]
            filas = datos[1:]

            tabla.setColumnCount(len(encabezados))
            tabla.setHorizontalHeaderLabels(encabezados)
            tabla.setRowCount(len(filas))

            for fila_indice, fila in enumerate(filas):
                for columna_indice in range(len(encabezados)):
                    valor = fila[columna_indice] if columna_indice < len(fila) else ""
                    elemento = QTableWidgetItem(valor)
                    if fila_indice % 2 == 0:
                        elemento.setBackground(QColor("#f8fbff"))
                    tabla.setItem(fila_indice, columna_indice, elemento)

            tabla.resizeColumnsToContents()
            tabla.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
        else:
            tabla.setColumnCount(1)
            tabla.setHorizontalHeaderLabels(["Resultado"])
            tabla.setRowCount(1)
            tabla.setItem(0, 0, QTableWidgetItem("No hay datos para mostrar."))

        layout.addWidget(tabla)

        ventana.tabla = tabla
        ventana.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        ventana.show()
        self.ventanas_resultados.append(ventana)

        ventana.destroyed.connect(
            lambda _objeto=None, referencia=ventana: (
                self.eliminar_ventana_resultado(referencia)
            )
        )

    def eliminar_ventana_resultado(self, ventana):
        if ventana in self.ventanas_resultados:
            self.ventanas_resultados.remove(ventana)


def main():
    aplicacion = QApplication(sys.argv)
    aplicacion.setStyle("Fusion")
    aplicacion.setStyleSheet(ESTILO_APLICACION)

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(aplicacion.exec())


if __name__ == "__main__":
    main()