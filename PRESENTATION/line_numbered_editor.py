from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QTextFormat, QTextOption,
)
from PyQt6.QtWidgets import QPlainTextEdit, QWidget


class _LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class LineNumberedEditor(QPlainTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = _LineNumberArea(self)
        self.setFont(QFont("Monospace", 11))
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

    # Cálculo de ancho -------------------------------------------------

    def line_number_area_width(self) -> int:
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        space = 12 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(),
                self.line_number_area.width(), rect.height(),
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(
                cr.left(), cr.top(),
                self.line_number_area_width(), cr.height(),
            )
        )

    # Pintado ----------------------------------------------------------

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#eef3fb"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#8a9bb5"))
                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1