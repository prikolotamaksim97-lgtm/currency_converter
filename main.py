from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QVBoxLayout)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from requests import get
import json
import os
from datetime import datetime

CACHE = "currency_cache.json"

def load_cache():
    """Возвращает данные из CACHE"""
    if os.path.exists(CACHE):
        with open(CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Сохраняет данные в CACHE"""
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)


class CurrencyConverter(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Конвертер валют")
        self.resize(600, 250)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Конвертер валют")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        self.sell = QComboBox()
        self.sell.addItems(["USD", "EUR", "RUB"])

        self.buy = QComboBox()
        self.buy.addItems(["USD", "EUR", "RUB"])

        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Введите сумму")

        self.button_convert = QPushButton("Конвертировать")
        self.button_convert.clicked.connect(self.convert)

        self.button_reverse = QPushButton("↑↓")
        self.button_reverse.clicked.connect(self.reverse_currency)

        self.result = QLabel("")
        self.result.setFont(QFont("Segoe UI", 20))
        self.result.setStyleSheet("color: #27ae60; font-weight: bold;")

        self.date = QLabel("")
        self.date.setFont(QFont("Segoe UI", 6))

        layout.addWidget(QLabel("Продаю"))
        layout.addWidget(self.sell)

        layout.addWidget(QLabel("Покупаю"))
        layout.addWidget(self.buy)

        layout.addWidget(self.amount)
        layout.addWidget(self.button_convert)
        layout.addWidget(self.button_reverse)
        layout.addWidget(self.result)
        layout.addWidget(self.date)

        self.setLayout(layout)
        

    def get_coef(self):
        """Возвращает коэффициент по API или из CACHE, актуальные дату и время"""
        sell = self.sell.currentText()
        buy = self.buy.currentText()
        cache = load_cache()
        key = f"{sell}_{buy}"

        try:

            response = get(
                f"https://api.frankfurter.dev/v2/rate/{sell}/{buy}", timeout=5)
                        
            coef = response.json()['rate']
            
            updated = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            cache[key] = {
                "rate": coef,
                "updated": updated}

            save_cache(cache)

        except Exception:
            if key in cache:
                coef = cache[key]["rate"]
                updated = cache[key]["updated"]
            else:
                coef = None
                updated = None
            
        return coef, updated

    def convert(self):
        """Конвертирует сумму"""
        sell = self.sell.currentText()
        buy = self.buy.currentText()

        try:
            amount = self.amount.text().strip().replace(',', '.')
            coef = None
            updated = None

            if sell == buy:
                coef = 1
                updated = None

            else: 
                coef, updated = self.get_coef()

            if coef is None:
                self.result.setText("😿 Нет интернета и отсутствует сохраненный курс")
                return
            
            amount = float(Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            res = Decimal(str(amount * coef)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if updated:
                self.result.setText(f"{amount} {sell} ➜ {res} {buy}")
                self.date.setText(f"на {updated}")
            else:
                self.result.setText(f"{amount} {sell} ➜ {res} {buy}")


        except (ValueError, InvalidOperation):
            self.result.setText("😿 Извините, могу конвертировать только числа")
            self.date.setText("")


    def reverse_currency(self):
        """Меняет местами валюты и конвертирует"""
        sell = self.sell.currentText()
        buy = self.buy.currentText()
        self.sell.setCurrentText(buy)
        self.buy.setCurrentText(sell)
        self.convert()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CurrencyConverter()
    window.show()
    sys.exit(app.exec())