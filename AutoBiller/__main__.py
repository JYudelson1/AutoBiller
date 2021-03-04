# -*- coding: utf-8 -*-

from AutoBiller.uiComponents import *
from AutoBiller.clientLogic import *
from AutoBiller.calendarLogic import *
from AutoBiller.utils import *

# TODO: change to AutoBiller.* for distribution

def main():
    autobiller = QApplication([])

    # Give the app a color palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#FCF8E9"))
    palette.setColor(QPalette.Button, QColor("#FFFBF3"))
    autobiller.setPalette(palette)

    # Init the main scene
    calendar_manager = CalendarManager()
    client_directory = ClientDirectory()
    main_scene = MainScene(client_directory, calendar_manager)
    calendar_manager.parent = main_scene

    # Set opening scene and show
    login_widget = LoginWidget(parent=main_scene)
    main_scene.setCentralWidget(login_widget)
    main_scene.show()

    # main_scene.go_to_main()
    # main_scene.toolbar.show()
    # a = CalendarEvent({"title":"test", "duration":45, "localStartDate":[0, 2021, 2, 3, 12, 0]})
    # b = CalendarEvent({"title":"test2", "duration":45, "localStartDate":[0, 2021, 2, 3, 12, 0]})
    # d = main_scene.new_display_query_by_day_widget("TEST", [a,b])

    autobiller.exec_()

if __name__ == '__main__':
    main()
