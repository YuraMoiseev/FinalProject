from PyQt5.QtWidgets import *
from PyQt5.QtCore import  Qt, QPoint
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

