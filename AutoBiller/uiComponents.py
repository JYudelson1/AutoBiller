# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDateTime, QSize, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QMovie

from pyicloud import PyiCloudService
from time import sleep

from clientLogic import *
from calendarLogic import *
from utils import *
# TODO: change to AutoBiller.* for distribution

class MainScene(QMainWindow):
    """docstring for MainScene."""

    def __init__(self, client_directory, calendar_manager, parent=None):
        super().__init__(parent)

        self._createMenu()
        self._createToolBar()
        self._createStatusBar()

        self.setWindowIcon(QIcon('resources/icon.png'))
        self.setMinimumSize(500, 300)
        self.setWindowTitle("AutoBiller")

        self.icloud = None
        self.client_directory = client_directory
        self.calendar_manager = calendar_manager

        nq = NewQueryWidget(parent=self)
        self.navigable_pages = [nq]

        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.addWidget(nq)


    def _createMenu(self):
        menubar = QMenuBar()
        self.menubar = menubar
        self.setMenuBar(menubar)

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
        # Confirm the user wishes to exit the AutoBiller
        reply = QMessageBox.question(self,
                                    'Confirm Exit',
                                    "Are you sure to quit? You may have unsaved work.",
                                    QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def _createStatusBar(self):
        status = QStatusBar()
        status.showMessage("Developed by Joseph Yudelson")
        self.setStatusBar(status)

    def nav(self, nav_request):
        page = self.navigable_pages[nav_request]
        self.stacked_widget.setCurrentWidget(page)

    def go_to_main(self):
        self.setCentralWidget(self.stacked_widget)

    def rename_page_in_toolbar(self, page_num, new_name):
        action = self.toolbar.findChildren(QAction)[page_num+2]
        action.setText(new_name)

    def new_bill_by_day(self, date):
        assert type(date) == datetime

        return self.calendar_manager.add_one_day(date)

    def new_display_query_by_day_widget(self, name, events):
        # Create a new DisplayQueryByDayWidget, then add it to pages and go there
        display = DisplayQueryByDayWidget(name=name, events=events, parent=self)
        self.add_page(display)
        self.stacked_widget.setCurrentWidget(display)
        return display

    def new_display_query_by_client_widget(self, name, events):
        # Create a new DisplayQueryByClientWidget, then add it to pages and go there
        display = DisplayQueryByClientWidget(name=name, events=events, parent=self)
        self.add_page(display)
        self.stacked_widget.setCurrentWidget(display)
        return display

    def add_page(self, finished_query_widget):
        # Add a new DisplayQueryWidget to the list of navigable pages

        index = len(self.navigable_pages)
        self.navigable_pages.append(finished_query_widget)
        self.stacked_widget.addWidget(finished_query_widget)

        title = finished_query_widget.get_name()
        self.toolbar.addAction(title, lambda: self.nav(index))

class LoginConfirmationPopup(QDialog):
    """docstring for LoginConfirmationPopup."""

    def __init__(self, icloud_acct, parent=None):
        super().__init__(parent)
        self.icloud_acct = icloud_acct

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


    def send_code(self, device):
        if not self.icloud_acct.send_verification_code(device):
            print("Failed to send verification code")
            self.close()

        form = QFormLayout()
        form.addRow('Confirmation code:', QLineEdit())
        self.layout().addLayout(form)

        confirmation_button = QPushButton("Confirm Code")
        confirmation_button.clicked.connect(lambda: self.verify_code(device,
                                                                        form.itemAt(1).widget().text()
                                                                        )
                                            )
        self.layout().addWidget(confirmation_button, alignment=Qt.AlignCenter)



    def verify_code(self, device, code):
        if not self.icloud_acct.validate_verification_code(device, code):
            print("Failed to verify verification code")
        self.close()

class LoginWidget(QWidget):
    """docstring for LoginWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)

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

    def login(self, username, password):

        #Handle the login in a worker QThread
        target_fn = self.login_target_fn
        args = (username, password)
        on_close_fn = self.finished
        gui_fn = self.start_confirmation_popup

        self.login_thread = ThreadedTask(target_fn, args, on_close_fn)
        self.login_thread.update.connect(gui_fn)
        self.login_thread.start()

    def login_target_fn(self, username, password):
        me = PyiCloudService(username, password)
        self.parent().icloud = me
        if me.requires_2fa:
            return True
        return False

    def finished(self):
        self.loader.stop_loading()
        self.parent().go_to_main()

    def start_confirmation_popup(self):
        icloud = self.parent().icloud
        confirmation_dialog = LoginConfirmationPopup(icloud_acct=icloud)
        confirmation_dialog.exec_()

class NewQueryWidget(QWidget):
    """docstring for NewQueryWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)

        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        label1 = QLabel("<h2>New Bill</h2>")
        v_layout.addWidget(label1, alignment=Qt.AlignCenter)

        label2 = QLabel("<center><p>Would you like to make a new bill by client or by date?</p><p>(Note: a billing session may include both.)</p></center>")
        v_layout.addWidget(label2, alignment=Qt.AlignCenter)

        buttons = QDialogButtonBox()
        bill_by_client_button = QPushButton("Bill by Client")
        bill_by_day_button = QPushButton("Bill by Day")

        bill_by_day_button.clicked.connect(self.init_bill_by_day)
        bill_by_client_button.clicked.connect(self.init_bill_by_client)

        buttons.addButton(bill_by_client_button, 0)
        buttons.addButton(bill_by_day_button, 0)

        v_layout.addWidget(buttons, alignment=Qt.AlignCenter)

    def init_bill_by_day(self):

        day_query = DayQueryPopup(parent=self)
        day_query.exec_()
        # Implement logic of throwing info back up to main scene?

    def bill_by_day(self, date):
        assert type(date) == datetime
        return self.parent().parent().new_bill_by_day(date)

    def init_bill_by_client(self):
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
    """docstring for DayQueryPopup."""

    def __init__(self, parent=None):
        super().__init__(parent)

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

    def confirm_date(self):
        # Handle the login in a worker QThread
        date = self.date_picker.date()
        self.date = datetime(date.year(), date.month(), date.day())

        target_fn = self.bill_by_day_target_fn
        args = (self.date,)
        on_close_fn = self.finished


        self.login_thread = ThreadedTask(target_fn, args, on_close_fn)
        self.login_thread.update.connect(self.gui_fn)
        self.login_thread.start()

    def bill_by_day_target_fn(self, date):
        # Tell the NewQueryWindow to bill one day
        self.events_of_day = self.parent().bill_by_day(date)
        return True

    def finished(self):
        self.loader.stop_loading()
        self.close()

    def set_events(self, events_of_day):
        self.events_of_day = events_of_day

    def gui_fn(self):
        self.parent().parent().parent().new_display_query_by_day_widget(self.date.strftime("%m/%d/%Y"), self.events_of_day)

class HiddenLoaderStackedWidget(QStackedWidget):
    """docstring for HiddenLoaderStackedWidget."""

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
    """docstring for ThreadedTask."""
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

    def run(self):
        # Do what you came to do
        if self.target_fn(*self.args):
            self.update.emit()
        self.finished.emit()

    def start(self):
        self.thread.start()

class DisplayQueryWidget(QWidget):
    """docstring for DisplayQueryWindow."""

    def __init__(self, name=None, events=None, data=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.events = events
        self.data = data
        self.header = None

        self.page_num = None
        if self.parent():
            self.page_num = len(self.parent().navigable_pages)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title = QLabel("<h2>Bill: {}</h2>".format(self.name))
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)

        self.table = QTableWidget()
        self.table.setRowCount(len(events))
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents)
        self.layout.addWidget(self.table, alignment=Qt.AlignCenter)

        export_as_csv_btn = QPushButton("Export as .csv")
        export_as_csv_btn.clicked.connect(self.export_as_csv)
        self.layout.addWidget(export_as_csv_btn, alignment=Qt.AlignCenter)

    def get_name(self):
        return self.name

    def rename(self, new_name):
        self.name = new_name
        self.title.setText("<h2>Bill: {}</h2>".format(self.name))
        self.parent().parent().rename_page_in_toolbar(self.page_num, self.name)

    def export_as_csv(self):
        filename = "BillingReport: " + self.name.replace("/","-") + "({})".format(datetime.today().strftime("%m.%d.%Y"))
        fieldnames = self.header[1:]
        checked_rows = []
        for i in range(self.table.rowCount()):
            checked = self.table.cellWidget(i, 0).findChildren(QCheckBox)[0].checkState()
            if checked == Qt.Checked:
                row_dict = {}
                for j, field in enumerate(fieldnames):
                    row_dict[field] = self.table.item(i, j+1).text()
                checked_rows.append(row_dict)

        download_csv_file(filename, fieldnames, checked_rows)

class DisplayQueryByDayWidget(DisplayQueryWidget):
    """docstring for DisplayQueryByDayWidget."""

    def __init__(self, name=None, events=None, data=None, parent=None):
        super().__init__(name, events, data, parent)
        self.header = ["Billable?","Event","CPT","Insurance","Payment","Billing Fee"]
        self.table.setColumnCount(len(self.header))
        self.table.setHorizontalHeaderLabels(self.header)

        for i, event in enumerate(self.events):
            self.add_to_table(i, event)

        self.table.resizeColumnsToContents()

    def add_to_table(self, i, event):
        # Add the given event to row i
        checkbox_item = QWidget()
        checkbox = QCheckBox()
        c_layout = QHBoxLayout(checkbox_item)
        c_layout.addWidget(checkbox, alignment=Qt.AlignCenter)
        checkbox_item.setLayout(c_layout)
        self.table.setCellWidget(i, 0, checkbox_item)
        checkbox.stateChanged.connect(lambda state: self.checkbox_toggled(state, i))

        title = QTableWidgetItem(event.title)
        title.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(i, 1, title)
        title.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        cpt = QTableWidgetItem("---")
        cpt.setTextAlignment(Qt.AlignCenter)
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

    def checkbox_toggled(self, i, new_state):
        # TODO: Implement
        pass
