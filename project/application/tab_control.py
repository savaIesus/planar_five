from project.application.layers.camera import calibration_thread_init
from project.station.modules.camera import thread_init


def tab_control(index):
    selected_index = index.control.selected_index
    thread_init(selected_index)
    calibration_thread_init(selected_index)
