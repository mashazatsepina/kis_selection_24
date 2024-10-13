import json
import os
from functools import partial

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QCalendarWidget, QTableWidget,
                             QLabel, QVBoxLayout, QTableWidgetItem, QSizePolicy,
                             QWidget, QDialog, QFormLayout, QLineEdit, QMessageBox, QHBoxLayout)
from PyQt6 import QtGui

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        """ Sets window parameters and launches the start menu """
        super().__init__()
        self.setWindowTitle("calorie counter")
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.h_layout = QHBoxLayout()

        self.button_calendar = QPushButton('calendar')
        self.button_calendar.clicked.connect(self.open_calendar)
        self.h_layout.addWidget(self.button_calendar, alignment=Qt.AlignmentFlag.AlignLeft)

        self.v_layout = QVBoxLayout()
        
        self.button_find_dish = QPushButton('find dish')
        self.button_find_dish.clicked.connect(self.open_list_dishes)
        self.button_find_dish.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred) 
        self.v_layout.addWidget(self.button_find_dish)

        self.button_add_dish = QPushButton('add new dish')
        self.button_add_dish.clicked.connect(partial(self.open_add_dish_dialog, dish_name=""))
        self.button_add_dish.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.v_layout.addWidget(self.button_add_dish)

        self.h_layout.addLayout(self.v_layout)
        self.layout.addLayout(self.h_layout)

        self.dish_table = QTableWidget(self)
        self.dish_table.setColumnCount(5)
        self.dish_table.setHorizontalHeaderLabels(['dish name', 'calories', 'proteins', 'fats', 'carbohydrates'])
        self.dish_table.setFixedSize(520, 400)
        self.layout.addWidget(self.dish_table, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.addStretch()

        self.label = QLabel('date: ', self)
        self.layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.set_date(QDate.currentDate().toString())

    def set_date(self, date: str) -> None:
        """ Sets the date and loads the data """
        self.date = date
        self.label.setText(f'date: {self.date}')
        self.load_dishes_for_date(self.date)

    def open_calendar(self) -> None:
        """ Opens the calendar and sets the date """
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setSelectedDate(QDate.fromString(self.date, "ddd MMM dd yyyy"))
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.setWindowTitle('select a date')
        self.calendar.setFixedSize(300, 200)
        self.calendar.show()

    def date_selected(self, date: QDate) -> None:
        """ Updates the data after the date change """
        self.set_date(date)
        self.calendar.close()

    def open_add_dish_dialog(self, dish_name: str) -> None:
        """ Opens a window for adding a new dish (or editing an existing one) """
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle('add dish')
        form_layout = QFormLayout(self.dialog)

        self.dish_name_input = QLineEdit(self.dialog)
        self.calories_input = QLineEdit(self.dialog)
        self.proteins_input = QLineEdit(self.dialog)
        self.fats_input = QLineEdit(self.dialog)
        self.carbohydrates_input = QLineEdit(self.dialog)
        self.gram_input = QLineEdit(self.dialog)

        form_layout.addRow('dish name:', self.dish_name_input)
        form_layout.addRow('calories per 100g:', self.calories_input)
        form_layout.addRow('proteins:', self.proteins_input)
        form_layout.addRow('fats:', self.fats_input)
        form_layout.addRow('carbohydrates:', self.carbohydrates_input)
        form_layout.addRow('gram:', self.gram_input)

        if dish_name != "":
            dishes = self.load_dishes_from_json()
            found_dish = next((dish for dish in dishes if dish['name'].lower() == dish_name.lower()), None)
            self.dish_name_input.setText(dish_name)
            self.calories_input.setText(str(found_dish['calories']))
            self.proteins_input.setText(str(found_dish['proteins']))
            self.fats_input.setText(str(found_dish['fats']))
            self.carbohydrates_input.setText(str(found_dish['carbohydrates']))

        add_button = QPushButton('add', self.dialog)
        add_button.clicked.connect(self.add_dish)
        form_layout.addWidget(add_button)

        self.dialog.setLayout(form_layout)
        self.dialog.exec()

    def add_dish(self) -> None:
        """ Calculates the grams of the dish and adds it to the current day """
        dish_name = self.dish_name_input.text()
        calories = self.calories_input.text()
        proteins = self.proteins_input.text()
        fats = self.fats_input.text()
        carbohydrates = self.carbohydrates_input.text()
        gram = self.gram_input.text()

        if not dish_name or not calories:
            QMessageBox.warning(self, 'Input Error', 'Please enter both dish name and calories.')
            return

        try:
            calories = float(calories)
            proteins = float(proteins)
            fats = float(fats)
            carbohydrates = float(carbohydrates)
            gram = float(gram)
            self.dish_table.insertRow(self.dish_table.rowCount())
            row_position = self.dish_table.rowCount() - 1
            self.dish_table.setItem(row_position, 0, QTableWidgetItem(dish_name))
            self.dish_table.setItem(row_position, 1, QTableWidgetItem(f'{calories/100*gram:.2f} kcal'))
            self.dish_table.setItem(row_position, 2, QTableWidgetItem(f'{proteins/100*gram:.2f}g'))
            self.dish_table.setItem(row_position, 3, QTableWidgetItem(f'{fats/100*gram:.2f}g'))
            self.dish_table.setItem(row_position, 4, QTableWidgetItem(f'{carbohydrates/100*gram:.2f}g'))
            
            self.clear_inputs()
            self.save_dish(dish_name, calories, proteins, fats, carbohydrates)
            self.save_meal(dish_name, calories, proteins, fats, carbohydrates, self.date)
            self.dialog.close()

        except ValueError:
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid number for calories.')

    def clear_inputs(self) -> None:
        """ Clears input fields """
        self.dish_name_input.clear()
        self.calories_input.clear()
        self.proteins_input.clear()
        self.fats_input.clear()
        self.carbohydrates_input.clear()
        self.gram_input.clear()

    def open_list_dishes(self) -> None:
        """ Opens the dish search window """
        self.dialog_search = QDialog(self)
        self.dialog_search.setWindowTitle('find dish')
        form_layout = QFormLayout(self.dialog_search)

        self.name_search = QLineEdit(self.dialog_search)
        form_layout.addRow('dish name:', self.name_search)

        find_button = QPushButton('find', self.dialog_search)
        form_layout.addWidget(find_button)

        find_button.clicked.connect(self.find_and_display_dish)
        
        self.dialog_search.setLayout(form_layout)
        self.dialog_search.exec()

    def find_and_display_dish(self) -> None:
        """ Displays the results of the dish search """
        dish_name = self.name_search.text().strip()
        dialog = self.dialog_search
        dish = self.find_dish_by_name(dish_name)
        if dish:
            self.open_add_dish_dialog(dish_name)
        else:
            QMessageBox.warning(self, 'Not Found', 'Dish not found.')
        dialog.close()

    def find_dish_by_name(self, name) -> dict:
        """ Looking for a dish among the saved ones """
        dishes = self.load_dishes_from_json()
        return next((dish for dish in dishes if dish['name'].lower() == name.lower()), None)

    def load_dishes_from_json(self) -> list[dict]:
        file_path = os.path.join('data', 'dishes.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        return []

    def save_dish(self, dish_name: str, calories: float, proteins: float, fats: float, carbohydrates: float) -> None:
        """ Saves information about the dish in json """
        dish_data = {
            "name": dish_name,
            "calories": calories,
            "proteins": proteins,
            "fats": fats,
            "carbohydrates": carbohydrates
        }
        file_path = os.path.join('data', 'dishes.json')
        
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump([], file, ensure_ascii=False)

        with open(file_path, 'r') as file:
            try:
                dishes = json.load(file)
            except json.JSONDecodeError:
                dishes = []

        for i, dish in enumerate(dishes):
            if dish['name'].lower() == dish_name.lower():
                dishes[i] = dish_data
                break
        else:
            dishes.append(dish_data)

        with open(file_path, 'w') as file:
            json.dump(dishes, file, indent=4, ensure_ascii=False)


    def save_meal(self, dish_name: str, calories: float, proteins: float, fats: float, carbohydrates: float, date: str) -> None:
        """ Saves data about meals on the current date """
        file_path = os.path.join('data', 'daily_calories.json')

        dish_data = {
            "date": date,
            "name": dish_name,
            "calories": calories,
            "proteins": proteins,
            "fats": fats,
            "carbohydrates": carbohydrates
        }

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    dishes = json.load(file)
                except json.JSONDecodeError:
                    dishes = []
        else:
            dishes = []

        dishes.append(dish_data)

        with open(file_path, 'w') as file:
            json.dump(dishes, file, indent=4, ensure_ascii=False)

    def load_dishes_for_date(self, date: str) -> None:
        """ Uploads information about all meals on the current day and calculates the amount """
        file_path = os.path.join('data', 'daily_calories.json')

        self.dish_table.setRowCount(0)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as file:
                dishes = json.load(file)
                total_calories = 0
                total_proteins = 0
                total_fats = 0
                total_carbohydrates = 0
                for dish in dishes:
                    if dish['date'] == date:
                        row_position = self.dish_table.rowCount()
                        self.dish_table.insertRow(row_position)
                        self.dish_table.setItem(row_position, 0, QTableWidgetItem(dish['name']))
                        self.dish_table.setItem(row_position, 1, QTableWidgetItem(f"{dish['calories']:.2f} kcal"))
                        self.dish_table.setItem(row_position, 2, QTableWidgetItem(f"{dish['proteins']:.2f}g"))
                        self.dish_table.setItem(row_position, 3, QTableWidgetItem(f"{dish['fats']:.2f}g"))
                        self.dish_table.setItem(row_position, 4, QTableWidgetItem(f"{dish['carbohydrates']:.2f}g"))
                    total_calories += dish['calories']
                    total_proteins += dish['proteins']
                    total_fats += dish['fats']
                    total_carbohydrates += dish['carbohydrates']

            total_row_position = self.dish_table.rowCount()
            self.dish_table.insertRow(total_row_position)
            self.dish_table.setItem(total_row_position, 0, QTableWidgetItem("Total"))
            self.dish_table.setItem(total_row_position, 1, QTableWidgetItem(f"{total_calories:.2f} kcal"))
            self.dish_table.setItem(total_row_position, 2, QTableWidgetItem(f"{total_proteins:.2f}g"))
            self.dish_table.setItem(total_row_position, 3, QTableWidgetItem(f"{total_fats:.2f}g"))
            self.dish_table.setItem(total_row_position, 4, QTableWidgetItem(f"{total_carbohydrates:.2f}g"))
            for column in range(5):
                item = self.dish_table.item(total_row_position, column)
                item.setBackground(QtGui.QBrush(QtGui.QColor(200, 200, 255)))
                item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))

