# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDateTime, QSize, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QMovie, QPixmap, QPalette, QColor

from pyicloud import PyiCloudService
from time import sleep

from AutoBiller.clientLogic import *
from AutoBiller.calendarLogic import *
from AutoBiller.utils import *
# TODO: change to AutoBiller.* for distribution

class MainScene(QMainWindow):
    """The main scene of the AutoBiller app"""

    def __init__(self, client_directory, calendar_manager, parent=None):
        super().__init__(parent)

        self._createMenu()
        self._createToolBar()
        self._createStatusBar()

        self.setWindowIcon(QIcon('icon.png'))
        self.setMinimumSize(500, 300)
        self.setWindowTitle("AutoBiller")

        self.icloud = None
        self.client_directory = client_directory
        self.calendar_manager = calendar_manager

        nq = NewQueryWidget(parent=self)
        self.navigable_pages = [nq]

        # Init the QStackedWidget that will hold the various scenes (except for login)
        self.stacked_widget = QStackedWidget(parent=self)
        self.stacked_widget.addWidget(nq)


    def _createMenu(self):
        menubar = QMenuBar()
        self.menubar = menubar
        self.setMenuBar(menubar)

        new_actions = menubar.addMenu("Settings")
        new_actions.addAction("Change Fees", self.change_fees)

        new_actions = menubar.addMenu("New")
        new_actions.addAction("New Query", lambda: self.nav(0))

        nav_actions = menubar.addMenu("Navigate")
        nav_actions.addAction("Show Navigation Bar", lambda: self.toolbar.show())
        nav_actions.addAction("Hide Navigation Bar", lambda: self.toolbar.hide())


    def _createToolBar(self):
        tools = QToolBar()
        self.addToolBar(Qt.LeftToolBarArea, tools)
        self.toolbar = tools

        tools.setOrientation(Qt.Vertical)
        tools.setMovable(False)
        tools.setFloatable(False)
        tools.setToolButtonStyle(Qt.ToolButtonTextOnly)

        tools.addAction("Pages:")
        tools.addAction("New Query", lambda: self.nav(0))

        tools.hide()

    def closeEvent(self, event):
        """Confirm the user wishes to exit the AutoBiller"""
        reply = QMessageBox.question(self,
                                    'Confirm Exit',
                                    "Are you sure to quit? You may have unsaved work.",
                                    QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def _createStatusBar(self):
        self.status = QStatusBar()
        self.status.showMessage("Developed by Joseph Yudelson")
        self.setStatusBar(self.status)

    def nav(self, nav_request):
        """Navigate to a given page attached to the main scene"""
        page = self.navigable_pages[nav_request]
        self.stacked_widget.setCurrentWidget(page)
        # Return Status Bar to default
        self.status.showMessage("Developed by Joseph Yudelson")
        # Resize window
        self.resize(QSize(500, 300))

    def go_to_main(self):
        """Sets the QStackedWidget as the central widget"""
        self.setCentralWidget(self.stacked_widget)

    def rename_page_in_toolbar(self, page_num, new_name):
        action = self.toolbar.findChildren(QAction)[page_num+2]
        action.setText(new_name)

    def new_bill_by_day(self, date):
        """Asks the attached calendar manager to bill one day"""
        assert type(date) == datetime

        return self.calendar_manager.add_one_day(date)

    def new_display_query_by_day_widget(self, name, events):
        """Create a new DisplayQueryByDayWidget, then add it to pages and go there"""
        display = DisplayQueryByDayWidget(name=name, events=events, parent=self)
        self.add_page(display)
        self.stacked_widget.setCurrentWidget(display)
        return display

    def new_display_query_by_client_widget(self, name, events):
        """Create a new DisplayQueryByClientWidget, then add it to pages and go there"""
        display = DisplayQueryByClientWidget(name=name, events=events, parent=self)
        self.add_page(display)
        self.stacked_widget.setCurrentWidget(display)
        return display

    def add_page(self, finished_query_widget):
        """Add a new DisplayQueryWidget to the list of navigable pages"""

        index = len(self.navigable_pages)
        self.navigable_pages.append(finished_query_widget)
        self.stacked_widget.addWidget(finished_query_widget)

        title = finished_query_widget.name
        self.toolbar.addAction(title, lambda: self.nav(index))

    def change_fees(self):
        """Open a popup to change the saved fees.json file"""
        fee_popup = ChangeFeesPopup(self)
        fee_popup.exec_()

class ChangeFeesPopup(QDialog):
    """The popup used to change stored fees"""

    types_in_order = ["90791", "96152", "90832", "90834", "90837", "90853", "90847", "90839"]

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up layout
        layout = QVBoxLayout()

        fees = QFormLayout()
        self.form = fees
        fees.addRow("First Session (90791):", QLineEdit())
        fees.addRow("15min Session (96152):", QLineEdit())
        fees.addRow("30min Session (90832):", QLineEdit())
        fees.addRow("45min Session (90834):", QLineEdit())
        fees.addRow("1hr Session (90837):", QLineEdit())
        fees.addRow("Group Session (90853):", QLineEdit())
        fees.addRow("Couples Session (90847):", QLineEdit())
        fees.addRow("Crisis (90839):", QLineEdit())

        # Add placeholder fees for each field
        for i in range(8):
            field = fees.itemAt(2*i + 1).widget()
            type = ChangeFeesPopup.types_in_order[i]
            field.setPlaceholderText(str(fee_by_cpt_code[type]))

        layout.addLayout(fees)

        buttons = QDialogButtonBox()
        buttons.setStandardButtons(
            QDialogButtonBox.Close | QDialogButtonBox.Save)
        buttons.accepted.connect(self.save_fees)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        # Layout finished

    def save_fees(self):
        """Save and store the updated fees"""

        new_fees = self.get_fees_from_form()

        if new_fees:
            # Update the fees in all relevant places
            write_fees(new_fees)
            for k in fee_by_cpt_code.keys():
                fee_by_cpt_code[k] = new_fees[k]

            confirm = QMessageBox.information(self,
                                    'Fee Change',
                                    "Your fees have been updated!")

            self.close()

    def get_fees_from_form(self):
        """Extract new fee data from the form"""
        new_fees = {}
        for i, type in enumerate(ChangeFeesPopup.types_in_order):
            field = self.form.itemAt(2*i + 1).widget()
            if field.text():
                try:
                    new_fees[type] = int(field.text())
                except ValueError:
                    # If a value is not an int:
                    warning = QMessageBox.warning(self,
                                            'Invalid Fee',
                                            "At least one of your fees is not a number!")
                    return False
            else:
                new_fees[type] = fee_by_cpt_code[type]

        return new_fees

class LoginConfirmationPopup(QDialog):
    """The popup used to confirm login information for 2-factor authentification"""

    def __init__(self, icloud_acct, parent=None):
        super().__init__(parent)
        self.icloud_acct = icloud_acct

        # Set up layout
        confirmation_layout = QVBoxLayout()

        label1 = QLabel("<p>Login requires two-factor authentification. Please select a device to receive your confirmation code.</p>")
        confirmation_layout.addWidget(label1, alignment=Qt.AlignCenter)

        devices = icloud_acct.trusted_devices
        devices_list = QListWidget()
        for d in devices:
            QListWidgetItem("SMS to %s" % d.get('phoneNumber'), parent=devices_list)
        devices_list.setCurrentRow(0)
        confirmation_layout.addWidget(devices_list, alignment=Qt.AlignCenter)

        code_button = QPushButton("Send Code")
        code_button.clicked.connect(lambda x: self.send_code(devices[devices_list.currentRow()]))
        confirmation_layout.addWidget(code_button, alignment=Qt.AlignCenter)

        self.setLayout(confirmation_layout)
        # Layout finished


    def send_code(self, device):
        """Send verification code to trusted device for 2FA"""
        if not self.icloud_acct.send_verification_code(device):
            warning = QMessageBox.warning(self,
                                    'Failed to send code',
                                    "Failed to send verification code. Please try again.")
            self.close()

        form = QFormLayout()
        form.addRow('Confirmation code:', QLineEdit())
        self.layout().addLayout(form)

        confirmation_button = QPushButton("Confirm Code")
        confirmation_button.clicked.connect(lambda: self.verify_code(device,
                                                                        form.itemAt(1).widget().text()
                                                                        )
                                            )
        confirmation_button.setDefault(True)
        self.layout().addWidget(confirmation_button, alignment=Qt.AlignCenter)



    def verify_code(self, device, code):
        """Verify confirmation code for 2FA"""
        if not self.icloud_acct.validate_verification_code(device, code):
            warning = QMessageBox.warning(self,
                                    'Invalid Code',
                                    "The verification code you entered was not valid! Try logging in again!")
        self.close()

class LoginWidget(QWidget):
    """The opening scene, for logging in to iCloud."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up layout
        v_layout = QVBoxLayout()

        label1 = QLabel("<h1>Welcome!</h1>")
        v_layout.addWidget(label1, alignment=Qt.AlignCenter)

        label2 = QLabel("<p>Login to your iCloud account to continue:<p>")
        v_layout.addWidget(label2, alignment=Qt.AlignCenter)

        # Username & Password info
        form = QFormLayout()
        password_field = QLineEdit()
        form.addRow('Username:', QLineEdit())
        form.addRow('Password:', password_field)
        password_field.returnPressed.connect(lambda: self.login(
                                                    form.itemAt(1).widget().text(),
                                                    form.itemAt(3).widget().text(),
                                                    )
                                            )
        v_layout.addLayout(form)

        # Login Button (inside a HiddenLoaderStackedWidget)
        login_button = QPushButton("Login")
        hidden_loader_with_login_button = HiddenLoaderStackedWidget(login_button)
        self.loader = hidden_loader_with_login_button
        login_button.clicked.connect(lambda: self.login(
                                                    form.itemAt(1).widget().text(),
                                                    form.itemAt(3).widget().text(),
                                                    )
                                    )
        login_button.clicked.connect(self.loader.start_loading)
        password_field.returnPressed.connect(self.loader.start_loading)
        v_layout.addWidget(hidden_loader_with_login_button, alignment=Qt.AlignCenter)

        self.setLayout(v_layout)
        # Layout finished

    def login(self, username, password):
        """Log the user into their iCloud account."""

        #Handle the login in a worker QThread
        target_fn = self.login_target_fn
        args = (username, password)
        on_close_fn = self.finished
        gui_fn = self.start_confirmation_popup

        self.login_thread = ThreadedTask(target_fn, args, on_close_fn, gui_fn)
        self.login_thread.start()

    def login_target_fn(self, username, password):
        """
        Attempts to log in to the icloud acct matching the username and password.
        Returns True if the acct requires 2FA, False otherwise.
        """
        me = PyiCloudService(username, password)
        self.parent().icloud = me
        if me.requires_2fa:
            return True
        return False

    def finished(self):
        """When finished, navigate away from login scene."""
        self.loader.stop_loading()
        self.parent().go_to_main()

    def start_confirmation_popup(self):
        """Open a LoginConfirmationPopup for 2FA"""
        icloud = self.parent().icloud
        confirmation_dialog = LoginConfirmationPopup(icloud_acct=icloud)
        confirmation_dialog.exec_()

class NewQueryWidget(QWidget):
    """The scene where a user decides whether to bill by client or by day."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up layout
        v_layout = QVBoxLayout()

        label1 = QLabel("<h2>New Bill</h2>")
        v_layout.addWidget(label1, alignment=Qt.AlignCenter)

        label2 = QLabel("<center><p>Would you like to make a new bill by client or by date?</p><p>(Note: a billing session may include both.)</p></center>")
        v_layout.addWidget(label2, alignment=Qt.AlignCenter)

        buttons = QDialogButtonBox()

        bill_by_client_button = QPushButton("Bill by Client")
        bill_by_client_button.clicked.connect(self.init_bill_by_client)

        bill_by_day_button = QPushButton("Bill by Day")
        bill_by_day_button.clicked.connect(self.init_bill_by_day)

        buttons.addButton(bill_by_client_button, 0)
        buttons.addButton(bill_by_day_button, 0)

        v_layout.addWidget(buttons, alignment=Qt.AlignCenter)

        self.setLayout(v_layout)
        # Layout finished

    def init_bill_by_day(self):
        """Open a DayQueryPopup and get the day to be billed."""

        day_query = DayQueryPopup(parent=self)
        day_query.exec_()

    def bill_by_day(self, date):
        """Ask the main scene to bill the given day."""
        assert type(date) == datetime
        return self.parent().parent().new_bill_by_day(date)

    def init_bill_by_client(self):
        """Open a ClientQueryPopup and get the client to be billed."""
        # TODO: Implement bill by client
        pass

class BillableConfirmationPopup(QDialog):
    """docstring for BillableConfirmationPopup."""

    def __init__(self, client, calendar_event, parent=None):
        super().__init__(parent)

        # ERROR HANDLING
        assert type(client) == Client
        assert type(calendar_event) == CalendarEvent

        self.client = client
        self.calendar_event = calendar_event

        confirmation_layout = QVBoxLayout()

        label1 = QLabel("<p>Is the following event billable for the client \"{}\"?</p>".format(client.name))
        confirmation_layout.addWidget(label1, alignment=Qt.AlignCenter)

        label2 = QLabel("<h4>\"{}\"</h4>".format(calendar_event.title))
        confirmation_layout.addWidget(label2, alignment=Qt.AlignCenter)

        buttons = QDialogButtonBox()
        buttons.setStandardButtons(
            QDialogButtonBox.No | QDialogButtonBox.Yes)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        confirmation_layout.addWidget(buttons, alignment=Qt.AlignCenter)

        self.setLayout(confirmation_layout)

    def accept(self):
        self.client.add_billable_event(self.calendar_event)
        self.close()

    def reject(self):
        self.client.add_unbillable_event(self.calendar_event)
        self.close()

class DayQueryPopup(QDialog):
    """The popup for choosing a day to bill."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up layout
        layout = QVBoxLayout()

        label1 = QLabel("<p>Please choose the day you'd like to bill for:</p>")
        layout.addWidget(label1, alignment=Qt.AlignCenter)

        date_picker = QDateEdit(calendarPopup=True)
        date_picker.setDateTime(QDateTime.currentDateTime())
        self.date_picker = date_picker
        layout.addWidget(date_picker, alignment=Qt.AlignCenter)

        confirm_button = QPushButton("Bill")
        hidden_loader_with_confirm_button = HiddenLoaderStackedWidget(confirm_button, size=.6)
        self.loader = hidden_loader_with_confirm_button
        confirm_button.clicked.connect(self.confirm_date)
        confirm_button.clicked.connect(self.loader.start_loading)
        layout.addWidget(hidden_loader_with_confirm_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        # Layout finished

    def confirm_date(self):
        """
        A function that confirms the selected date
        and begins downloading calendar data.
        """

        # Handle the login in a worker QThread
        date = self.date_picker.date()
        self.date = datetime(date.year(), date.month(), date.day())

        target_fn = self.bill_by_day_target_fn
        args = (self.date,)
        on_close_fn = self.finished


        self.login_thread = ThreadedTask(target_fn, args, on_close_fn, self.gui_fn)
        self.login_thread.start()

    def bill_by_day_target_fn(self, date):
        """Tell the NewQueryWindow to bill one day"""
        self.events_of_day = self.parent().bill_by_day(date)
        return True

    def finished(self):
        """Stop the loading gif before closing."""
        self.loader.stop_loading()
        self.close()

    def gui_fn(self):
        """Tell the main scene to make a DisplayQueryByDayWidget based on the events_of_day data."""
        self.parent().parent().parent().new_display_query_by_day_widget(
                                            self.date.strftime("%m/%d/%Y"),
                                            self.events_of_day
                                            )

class HiddenLoaderStackedWidget(QStackedWidget):
    """A QStackedWidget that always contains a loading .gif underneath."""

    def __init__(self, widget_on_top, parent=None, size=None):
        super().__init__(parent)
        self.widget_on_top = widget_on_top

        # Initialize the loader gif
        self.gif = QMovie("resources/loading.gif")
        if size:
            self.gif.setScaledSize(QSize(int(414*size), int(233*size)))
        self.label = QLabel()
        self.label.setMovie(self.gif)

        self.addWidget(self.label)
        self.addWidget(self.widget_on_top)
        self.setCurrentWidget(self.widget_on_top)

    def start_loading(self):
        self.setCurrentWidget(self.label)
        self.label.show()
        self.gif.start()

    def stop_loading(self):
        self.gif.stop()
        self.setCurrentWidget(self.widget_on_top)

class ThreadedTask(QObject):
    """A signle class for singular threaded tasks."""
    finished = pyqtSignal()
    update = pyqtSignal()

    def __init__(self, target_fn, args, on_close_fn, gui_fn=None):
        super().__init__()
        self.target_fn = target_fn
        self.args = args
        self.on_close_fn = on_close_fn
        self.gui_fn = gui_fn

        self.thread = QThread()
        self.moveToThread(self.thread)

        # Connect signals and slot
        self.thread.started.connect(self.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.on_close_fn)
        self.finished.connect(self.thread.quit)
        self.finished.connect(self.deleteLater)

        if self.gui_fn:
            self.update.connect(self.gui_fn)

    def run(self):
        # Do what you came to do
        if self.target_fn(*self.args):
            # Id the target_fn ever returns yes,
            self.update.emit()
        self.finished.emit()

    def start(self):
        self.thread.start()

class DisplayQueryWidget(QWidget):
    """A generic scene to display a finished iCloud query"""

    def __init__(self, name=None, events=None, data=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.events = events
        self.data = data
        self.header = None
        self.types_in_order = ["90791", "96152", "90832", "90834", "90837", "90853", "90847", "90839"]

        # Get page number
        self.page_num = None
        if self.parent():
            self.page_num = len(self.parent().navigable_pages)

        # Set up layout
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>Bill: {}</h2>".format(self.name))
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)

        self.table = QTableWidget()
        self.table.setRowCount(len(events))
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents)
        self.layout.addWidget(self.table, alignment=Qt.AlignCenter)

        self.export_as_csv_btn = QPushButton("Export as .csv")
        self.export_as_csv_btn.clicked.connect(self.export_as_csv)
        self.layout.addWidget(self.export_as_csv_btn, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)
        # Layout finished

    def rename(self, new_name):
        """Rename this page to new_name."""
        self.name = new_name
        self.title.setText("<h2>Bill: {}</h2>".format(self.name))
        self.parent().parent().rename_page_in_toolbar(self.page_num, self.name)

    def export_as_csv(self):
        """Export the information contained in the checked elements of this page to a .csv"""
        filename = "BillingReport: " + self.name.replace("/","-") + "({})".format(datetime.today().strftime("%m.%d.%Y"))
        fieldnames = self.header[1:]
        checked_rows = []
        for i in range(self.table.rowCount()):
            checked = self.table.cellWidget(i, 0).findChildren(QCheckBox)[0].checkState()
            if checked == Qt.Checked:
                row_dict = {}
                for j, field in enumerate(fieldnames):
                    widget = self.table.cellWidget(i,j+1)
                    if widget:
                        row_dict[field] = widget.findChild(QComboBox).currentText()
                    else:
                        row_dict[field] = self.table.item(i, j+1).text()
                checked_rows.append(row_dict)
        self.parent().parent().status.showMessage("File Saved to Downloads!")
        download_csv_file(filename, fieldnames, checked_rows)

class DisplayQueryByDayWidget(DisplayQueryWidget):
    """A scene to display a finished iCloud query of a particular day."""

    def __init__(self, name=None, events=None, data=None, parent=None):
        super().__init__(name, events, data, parent)

        # Set up table
        self.header = ["Billable?","Event / Client","CPT","Insurance","Payment","Billing Fee"]
        self.table.setColumnCount(len(self.header))
        self.table.setHorizontalHeaderLabels(self.header)
        self.is_event_billable = self.parent().client_directory.is_event_billable
        self.client_by_row = {}

        for i, event in enumerate(self.events):
            # Add the evnts to the table, then check if they are events.
            self.add_to_table(i, event)

            session_data = self.is_event_billable(event)
            if session_data:
                self.table.cellWidget(i, 0).findChild(QCheckBox).setCheckState(2)
                self.set_row_info(i, **session_data)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.parent().resize(self.table.sizeHint() + QSize(100, 190))

    def add_to_table(self, i, event):
        """Add the given non-session event to row i"""
        checkbox_item = QWidget()
        checkbox = QCheckBox()
        c_layout = QHBoxLayout(checkbox_item)
        c_layout.addWidget(checkbox, alignment=Qt.AlignCenter)
        checkbox_item.setLayout(c_layout)
        self.table.setCellWidget(i, 0, checkbox_item)
        checkbox.stateChanged.connect(lambda state: self.checkbox_toggled(state, i))

        title = QTableWidgetItem(event.title)
        title.setTextAlignment(Qt.AlignCenter)
        self.table.removeCellWidget(i, 1)
        self.table.setItem(i, 1, title)
        title.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        cpt = QTableWidgetItem("---")
        cpt.setTextAlignment(Qt.AlignCenter)
        self.table.removeCellWidget(i, 2)
        self.table.setItem(i, 2, cpt)
        cpt.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        insurance = QTableWidgetItem("---")
        insurance.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(i, 3, insurance)
        insurance.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        copay = QTableWidgetItem("---")
        copay.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(i, 4, copay)
        copay.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        fee = QTableWidgetItem("---")
        fee.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(i, 5, fee)
        fee.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def set_row_info(self, row, name, cpt="", insurance="", fee=""):
        """Set the information at a given row to the new session info"""
        name_box = self.table.cellWidget(row, 1).findChild(QComboBox)
        name_box.addItem(name)
        name_box.setCurrentIndex(name_box.count() - 1)
        if cpt:
            # Set the cpt to the appropriate value
            index = self.types_in_order.index(cpt)
            self.table.cellWidget(row, 2).findChild(QComboBox).setCurrentIndex(index)
        self.table.item(row, 3).setText(insurance)


    def checkbox_toggled(self, new_state, i):
        """
        Activates when the check mark at row i is toggled.
        A new_state of 2 means the mark is checked, 0 for unchecked.
        This transforms the event row into the editable version if checked, or vice versa.

        RETURNS: none
        """
        if new_state: # The checkbox was toggled on

            title = QWidget()
            title_dropdown = QComboBox()
            d_layout = QHBoxLayout(title)
            d_layout.addWidget(title_dropdown, alignment=Qt.AlignCenter)
            title.setLayout(d_layout)
            self.table.setCellWidget(i, 1, title)

            title_dropdown.setEditable(True)
            title_dropdown.setInsertPolicy(QComboBox.InsertAtBottom)
            title_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToContents)


            title_dropdown.addItem("Group")
            title_dropdown.insertSeparator(1)

            title_dropdown.setCurrentIndex(-1)
            title_dropdown.setCurrentText("Client")
            # TODO: implement defaults from the ClientDirectory
            #title_dropdown.currentTextChanged.connect() # TODO

            cpt = QWidget()
            cpt_dropdown = QComboBox()
            d_layout = QHBoxLayout(cpt)
            d_layout.addWidget(cpt_dropdown, alignment=Qt.AlignCenter)
            cpt.setLayout(d_layout)
            self.table.setCellWidget(i, 2, cpt)

            cpt_dropdown.addItem("90791")
            cpt_dropdown.addItem("96152")
            cpt_dropdown.addItem("90832")
            cpt_dropdown.addItem("90834")
            cpt_dropdown.addItem("90837")
            cpt_dropdown.addItem("90853")
            cpt_dropdown.addItem("90847")
            cpt_dropdown.addItem("90839")

            # When the cpt code is changed, change the corresponding fee
            cpt_dropdown.currentIndexChanged.connect(lambda index: self.table.item(i, 5).setText(str(fee_by_cpt_code[self.types_in_order[index]])))
            cpt_dropdown.setCurrentIndex(3)
            self.table.item(i, 5).setText(str(fee_by_cpt_code[self.types_in_order[3]]))

            # Allow user to edit insurance & Payment
            self.table.item(i, 3).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.item(i, 4).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.item(i, 3).setText("")
            self.table.item(i, 4).setText("")

        else: # The checkbox was toggled off
            self.add_to_table(i, self.events[i])

        # Resize table and window:
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.parent().parent().resize(self.table.sizeHint() + QSize(100, 190))
