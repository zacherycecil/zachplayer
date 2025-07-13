from evdev import InputDevice, categorize, ecodes
from selectors import DefaultSelector, EVENT_READ

class EventHandler:
    def __init__(self, app_state, controller):
        self.app_state = app_state
        self.controller = controller
        self.selector = DefaultSelector()

        with open('input_devices.txt') as f:
            for line in f:
                device = InputDevice(line.strip())
                self.selector.register(device, EVENT_READ)

    def handle_events(self):
        for key, mask in self.selector.select():
            device = key.fileobj
            for event in device.read():
                self.handle_event(event)

    def handle_event(self, event):
        if event.type == ecodes.EV_KEY:
            if event.value == 1:  # key down only
                if event.code in [ecodes.BTN_LEFT]:
                    self.controller.left_click()
                elif event.code in [ecodes.BTN_RIGHT]:
                    self.controller.right_click()
                elif event.code in [ecodes.BTN_MIDDLE]:
                    self.controller.middle_click()

        elif event.type == ecodes.EV_REL:
            if event.code == ecodes.REL_WHEEL:
                if event.value > 0:
                    self.controller.scroll_up()
                elif event.value < 0:
                    self.controller.scroll_down()
