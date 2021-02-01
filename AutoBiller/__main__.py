# -*- coding: utf-8 -*-

from AutoBiller.uiComponents import *
from AutoBiller.clientLogic import *
from AutoBiller.calendarLogic import *
from AutoBiller.utils import *

def main():
    app = QApplication([])

    # Init the main scene
    calendar_manager = CalendarManager()
    client_directory = ClientDirectory()
    main_scene = MainScene(client_directory, calendar_manager)
    calendar_manager.parent = main_scene

    # Set opening scene and show
    login_widget = LoginWidget(parent=main_scene)
    main_scene.setCentralWidget(login_widget)
    main_scene.show()

    app.exec_()

if __name__ == '__main__':
    main()
