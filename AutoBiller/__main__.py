# -*- coding: utf-8 -*-

from uiComponents import *
from clientLogic import *
from calendarLogic import *
from utils import *

# TODO: change to AutoBiller.* for distribution

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

    main_scene.go_to_main()
    main_scene.toolbar.show()
    d = main_scene.new_display_query_widget("TEST", [])
    sleep(2)
    d.rename("second test")


    app.exec_()

if __name__ == '__main__':
    main()
