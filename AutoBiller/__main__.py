# -*- coding: utf-8 -*-

from uiComponents import *
from clientLogic import *
from calendarLogic import *
from utils import *

# TODO: change to AutoBiller.* for distribution

def main():
    app = QApplication([])

    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#FCF8E9"))
    pal.setColor(QPalette.Button, QColor("#FFFBF3"))
    app.setPalette(pal)

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

    app.exec_()

if __name__ == '__main__':
    main()
