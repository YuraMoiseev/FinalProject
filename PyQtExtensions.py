from PyQt5.QtWidgets import *
from PyQt5.QtCore import  Qt, QPoint
from DBProtocol import fetch_requests, fetch_users
from ConstantsAndLogging import *


class QFileDropWidget(QWidget):
    """
    A custom PyQt widget class that enables drag-and-drop functionality for files and displays the path of the chosen file
    Also implements local directory browsing for files
    Inherited from QWidget
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # Enable drag-and-drop
        self.chosen_file_path = None # Save the chosen file_path
        self.delete_button = None
        self.file_drop_label = None
        self.layout = None
        self.hover_message = None
        self.create_ui()

    def text(self):
        """ Retrieve the text from the label """
        return self.label.text()

    def create_ui(self):
        """ Sets up the ui of the widget """
        # Create layout
        self.layout = QHBoxLayout(self)

        # Create the file drop label
        self.file_drop_label = QLabel("Drag and drop your file here")
        self.file_drop_label.setStyleSheet(DROP_FILE_STYLE_SHEET)

        # Create a QLabel to display the hover message
        self.hover_message = QLabel("Browse local directories for more files", self)
        self.hover_message.setStyleSheet(
            'font: 14pt "Arial"; border-radius: 15px; color: #00ff00; background-color: transparent;')
        self.hover_message.setWindowFlags(Qt.ToolTip)  # Make it look like a tooltip

        # Create the delete button
        self.delete_button = QPushButton("X")
        self.delete_button.setFixedSize(20, 20)  # Make the button small
        self.delete_button.setStyleSheet("background-color: red; color: white; border-radius: 10px;")
        self.delete_button.setToolTip("Remove file")
        self.delete_button.hide()

        # Add widgets to layout
        self.layout.addWidget(self.file_drop_label, stretch=9)
        self.layout.addWidget(self.delete_button, alignment=Qt.AlignRight)

        # Connect the delete button signal
        self.delete_button.clicked.connect(self.handle_delete)

    def handle_delete(self):
        """ Handle the file delete action """
        self.file_drop_label.setText("Drag and drop your file here")  # Reset the label
        self.delete_button.hide()  # Hide the delete button
        self.chosen_file_path = None # Delete the file path
        self.hover_message.hide() # Hide the hover message

    def dragEnterEvent(self, event):
        """ Handle the drag enter event (dragging the file to the widget) """
        if event.mimeData().hasUrls():
            event.accept()  # Accept drag event
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Handle the drop event (dropping the file onto the widget) """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.file_drop_label.setText(file_path)  # Show the dropped file path
        self.chosen_file_path = self.file_drop_label.text() # Save the file path
        self.delete_button.show() # Provide the option to delete the file path when necessary


    def enterEvent(self, event):
        """ Function triggered by enter event (moving the mouse onto the widget) """
        # Change the text when the mouse enters the widget
        if self.chosen_file_path is None:
            self.file_drop_label.setText("Browse local directories for files")
        else:
            # Position the hover message near the widget now that the widget geometry is certainly defined
            widget_pos = self.mapToGlobal(QPoint(0, 0))
            self.hover_message.move(widget_pos.x() + self.width() // 2 + 10, widget_pos.y()-10)
            self.hover_message.show()

    def leaveEvent(self, event):
        """ Function triggered by leave event (moving the mouse away from the widget) """
        # Restore the original text when the mouse leaves the widget
        if self.chosen_file_path is None:
            self.file_drop_label.setText("Drag and drop your file here")
        else:
            self.hover_message.hide()


    def mousePressEvent(self, event):
        # Change the text or perform an action when the label is clicked (pressed)
        self.file_drop_label.setText("Browsing...")
        chosen_file = self.showDialog() # Get the file path
        if chosen_file:
            self.file_drop_label.setText(chosen_file)
            self.chosen_file_path = chosen_file # Save the file path
            self.delete_button.show() # Provide the option to delete the file path when necessary
        elif self.chosen_file_path is not None:
            self.file_drop_label.setText(self.chosen_file_path) # Restore the saved file path to the label
        else:
            self.file_drop_label.setText("Drag and drop your file here") # Bring back the default message to the label

    def showDialog(self):
        # Open the file dialog to select files
        file, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'All Files (*)')
        if file:
            return file  # Return the selected file path
        else:
            return None # In case of cancel event, return None


class QPopUpWidget(QDialog):
    def __init__(self, labeltext1="This is a pop-up dialog", labeltext2="Choose one of the options!",  parent=None, buttons=(2, ["Yes", "No"])):
        super().__init__(parent)

        self.can_close = False

        self.setStyleSheet("""background-color:black;""")

        self.setWindowTitle("Pop-Up")
        self.setFixedSize(350, 300)


        self.layout = QVBoxLayout()
        self.label_info = QLabel(labeltext1)
        self.label_info.setStyleSheet(LABEL_STYLE_SHEET)
        self.label_info.setWordWrap(True)
        self.layout.addWidget(self.label_info)

        self.label_error = QLabel(labeltext2)
        self.label_error.setStyleSheet(ERROR_LABEL_STYLE_SHEET)
        self.layout.addWidget(self.label_error)
        self.label_error.hide()

        self.button_1 = QPushButton(buttons[1][0])
        self.button_1.setStyleSheet(BUTTON_STYLE_SHEET)
        self.button_1.clicked.connect(self.on_click_positive)

        self.layout.addWidget(self.button_1)

        if buttons[0] == 2:
            self.button_2 = QPushButton(buttons[1][1])
            self.button_2.setStyleSheet(BUTTON_STYLE_SHEET)
            self.button_2.clicked.connect(self.on_click_negative)
            self.layout.addWidget(self.button_2)

        self.setLayout(self.layout)

    # override if needed
    def on_click_positive(self):
        self.can_close = True
        self.accept()

    def on_click_negative(self):
        self.can_close = True
        self.reject()


    def closeEvent(self, event):
        if self.can_close:
            event.accept()
        else:
            event.ignore()
            self.label_error.show()


# TODO: create file downloading (file send request by clicking the corresponding button)
class QRequestsTable(QWidget):
    def __init__(self, column_names_and_callbacks, fetch_rows_callback, field_callbacks=None, limit=10):
        super().__init__()
        self.offset = 0
        self.limit = limit
        self.column_names_and_callbacks = column_names_and_callbacks
        self.table = None
        self.load_more_button = None
        self.fetch_rows_callback = fetch_rows_callback
        self.create_ui()

    def create_ui(self):
        self.setWindowTitle('Requests Table')
        self.setFixedSize(250 + len(self.column_names_and_callbacks)*150, 450)
        self.setStyleSheet(LABEL_STYLE_SHEET)

        # Create a table widget
        self.table = ClickableTableWidget(self)
        self.table.setColumnCount(len(self.column_names_and_callbacks))
        self.table.setHorizontalHeaderLabels(self.column_names_and_callbacks.keys())
        self.table.setStyleSheet(TABLE_STYLE_SHEET)
        self.table.setFixedSize(len(self.column_names_and_callbacks)*140, 450)

        # Create a "Load More" button
        self.load_more_button = QPushButton('Load More', self)
        self.load_more_button.setStyleSheet(BUTTON_STYLE_SHEET)
        self.load_more_button.setFixedSize(250, 40)
        self.load_more_button.clicked.connect(self.load_data)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.load_more_button)
        self.setLayout(layout)

        # Load initial data
        self.load_data()

    def load_data(self):
        # Fetch data from the database
        data = self.fetch_rows_callback(self.offset, self.limit)

        # Extend the table
        self.table.setRowCount(self.offset + len(data))
        # Loop through the dictionaries and load the data into the table
        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(row_data.keys()):
                value = row_data[col_name]
                # Get the processing function for this column
                processing_function = list(self.column_names_and_callbacks.values())[col_idx]
                field = QCallableTableWidgetItem(str(value), processing_function)
                self.table.setItem(row_idx + self.offset, col_idx, field)
                field.setBackground(Qt.black)

            for col_idx in range(len(row_data), len(self.column_names_and_callbacks)):
                value = ""
                processing_function = list(self.column_names_and_callbacks.values())[col_idx]
                # Get the processing function for this column
                field = QCallableTableWidgetItem(str(value), processing_function)
                self.table.setItem(row_idx + self.offset, col_idx, field)
                field.setBackground(Qt.black)


        # Update the offset for the next load
        self.offset += len(data)

    def removeRow(self, row):
        self.table.removeRow(row)

    def getRowData(self, row):
        row_data = [self.table.item(row, column).data for column in range(len(self.column_names_and_callbacks))]
        return row_data

    def updateRowData(self, row, updated_data):
        for item_idx, item in enumerate(updated_data):
            self.setItemValue(row, item_idx, item)


    def item(self, x, y):
        return self.table.item(x, y).data

    def setItemValue(self, x, y, val):
        table_item = self.table.item(x, y)
        table_item.set_data(str(val))


class ClickableTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is not None and isinstance(item, QCallableTableWidgetItem):
            write_to_log(f"Triggered mouse press event on item {item.row()}, {item.column()}")
            if callable(item.callback):
                item.callback(item.row(), item.column())
        super().mousePressEvent(event)


class QCallableTableWidgetItem(QTableWidgetItem):
    def __init__(self, data: str, callback=None):
        super().__init__(data)
        self.data = data
        self.callback = callback

    def set_data(self, data):
        self.data = data
        self.setText(self.data)


if __name__ == "__main__":
    app = QApplication([])
    # window = QPopUpWidget()
    window = QRequestsTable(USERS_COLUMNS, fetch_users)
    window.show()
    app.exec()
