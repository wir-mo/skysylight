import clr

clr.AddReference("Microsoft.Lync.Model")
from Microsoft.Lync.Model import *  # type: ignore
from Microsoft.Lync.Model.Conversation import (  # type: ignore
    ModalityTypes,
    ModalityState,
    ModalityAction,
)

import os
import sys
import threading

import struct
import serial
import serial.tools.list_ports
import pystray
from pystray import Menu, MenuItem as Item
from PIL import Image
import time
from loguru import logger
import statemachine

# Define paths to colored icon images
ICON_AVAILABLE = "green.png"
ICON_BUSY = "red.png"
ICON_AWAY = "yellow.png"
ICON_DND = "red.png"
ICON_OFFLINE = "gray.png"

presence_map = {
    0: "Offline",  # None: A flag indicating that the contact state is to be reset to the default availability that is calculated by Lync and based on current user activity and calendar state.
    18500: "Offline",  # Offline: A flag indicating that the contact is not available.
    3500: "Available",  # Free: A flag indicating that the contact is available.
    6500: "Busy",  # Busy: A flag indicating that the contact is busy and inactive.
    7500: "Busy",  # BusyIdle: Idle states are machine state and can not be published as user state.
    1250: "Not at work",
    15500: "Not at work",  # Away: A flag indicating that the contact cannot be alerted.
    6000: "Do Not Disturb",
    9500: "Do Not Disturb",  # DoNotDisturb: A flag indicating that the contact does not want to be disturbed.
    12500: "Back again soon",  # TemporarilyAway: A flag indicating that the contact is temporarily un-alertable.
    5000: "Inactive",  # FreeIdle: idle states are machine state and can not be published as user state.
}

icon_map = {
    0: ICON_OFFLINE,
    18500: ICON_OFFLINE,
    3500: ICON_AVAILABLE,
    6500: ICON_BUSY,
    7500: ICON_BUSY,
    1250: ICON_AWAY,
    15500: ICON_AWAY,
    6000: ICON_DND,
    9500: ICON_DND,
    12500: ICON_AWAY,
    5000: ICON_AWAY,
}

presence = 0
incoming_call = False
ser: serial.Serial | None = None


def dump(obj):
    for attr in dir(obj):
        try:
            logger.debug("obj.%s = %r" % (attr, getattr(obj, attr)))
        except:
            logger.debug("obj.%s = ?" % (attr))


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def map_presence(presence_value):
    presence = presence_map.get(presence_value, f"Unknown ({presence_value})")
    logger.info(f"Presence status: {presence} ({presence_value})")
    return presence


def get_icon_path(presence_value):
    return resource_path(icon_map.get(presence_value, ICON_OFFLINE))


def send_command(ser, *args) -> bool:
    command = struct.pack("B" * len(args), *args)
    ser.write(command)
    response = ser.read(1)
    # logger.info(f'cmd {command}: {response}')
    return response == b"\x00"


def ping_light(ser) -> bool:
    command = struct.pack("B", 0x01)
    ser.write(command)
    response = ser.read(1)
    return response == b"\x42"


def find_device_port(ports: list[any]) -> any:
    for port in ports:
        # logger.info(f'Port: {port.hwid}, {port.name}, {port.vid}, {port.pid}, {port.manufacturer}')
        if "CH340" in port.description:
            try:
                ser = serial.Serial(port.device, 115200, timeout=1)
                if ping_light(ser):
                    ser.close()
                    return port
                ser.close()
            except:
                pass
    return None


def on_exit(tray: pystray.Icon, exit_event):
    tray.stop()
    exit_event.set()


def get_contact_information(client):
    while client.Self.Contact is None:
        time.sleep(10)

    # Attempt to get contact information
    return client.Self.Contact.GetContactInformation(
        ContactInformationType.Availability  # type: ignore
    )


# Function to update the icon with the colored presence status
def update_icon(tray: pystray.Icon, presence: int):
    tray.icon = Image.open(get_icon_path(presence))
    tray.title = f"Presence: {map_presence(presence)}"


def update_light(ser: serial.Serial, presence: int, incoming_call: bool):
    if incoming_call:
        send_command(ser, 0x03, 0xFF, 0x00, 0x00)
        return

    if presence == 0 or presence == 18500:
        # Offline
        send_command(ser, 0x02, 0x00, 0x00, 0x00)

    elif presence == 3500:
        # Available
        send_command(ser, 0x02, 0x00, 0xFF, 0x00)

    elif presence == 6500 or presence == 7500:
        # Busy
        send_command(ser, 0x02, 0xFF, 0x00, 0x00)

    elif presence == 1250 or presence == 5000 or presence == 15500:
        # Not at work
        send_command(ser, 0x02, 0xFF, 0xFF, 0x00)

    elif presence == 6000 or presence == 9500:
        # Do not disturb
        send_command(ser, 0x02, 0xFF, 0x00, 0x00)

    elif presence == 12500:
        # Back again soon
        send_command(ser, 0x02, 0x00, 0x00, 0xFF)


def update_light1():
    # global ser, presence, incoming_call
    if ser.is_open:
        update_light(ser, presence, incoming_call)


# Function to handle changed contact information
def on_contact_information_changed(tray: pystray.Icon, source, e):
    global presence
    try:
        if e.ChangedContactInformation.Contains(ContactInformationType.Availability):  # type: ignore
            presence = source.GetContactInformation(ContactInformationType.Availability)  # type: ignore
            update_icon(tray, presence)
            update_light1()
    except NotSignedInException:  # type: ignore
        presence = 0
        update_icon(tray, presence)
        update_light1()
        lyncStateMachine.process_event("NotSignedInException")
    except Exception as e:
        logger.exception(f"on_contact_information_changed exception: {e}")


def on_conversation_added(source, e):
    try:
        conversation = e.Conversation
        audioVideo = conversation.Modalities[ModalityTypes.AudioVideo]
        audioVideo.ModalityStateChanged += on_modality_state_changed
        audioVideo.ActionAvailabilityChanged += on_action_availability_changed
    except Exception as e:
        logger.exception(f"on_conversation_added exception: {e}")


def on_modality_state_changed(source, e):
    global incoming_call
    try:
        if e.NewState == ModalityState.Notified:
            incoming_call = True
            update_light1()
            logger.info("Incoming call")

    except Exception as e:
        logger.exception(f"on_modality_state_changed exception: {e}")


def on_action_availability_changed(source, e):
    global incoming_call
    try:
        if e.Action == ModalityAction.Accept and not e.IsAvailable:
            incoming_call = False
            logger.info("Call disconnected")

    except Exception as e:
        logger.exception(f"on_action_availability_changed exception: {e}")


def main():
    # logger.add("skysy.log")

    exit_event = threading.Event()

    # Create main menu with submenu
    global tray
    tray = pystray.Icon(
        name="Skype for Business Presence",
        icon=Image.open(get_icon_path(0)),
        menu=Menu(
            Item("Exit", lambda icon: on_exit(icon, exit_event)),
        ),
    )

    # Keep the program running detached until the tray icon is stopped
    tray.run_detached()

    # global skysyStatemachine
    skysyStatemachine = statemachine.StateMachine()
    skysyStatemachine.transition_to(FindSkysyLight(skysyStatemachine))

    global lyncStateMachine
    lyncStateMachine = statemachine.StateMachine()
    lyncStateMachine.transition_to(GetLyncClient(lyncStateMachine))

    while not exit_event.is_set():
        skysyStatemachine.update()
        lyncStateMachine.update()
        time.sleep(2)


class GetLyncClient(statemachine.State):
    def __init__(self, stateMachine):
        self.name = "GetLyncClient"
        self.stateMachine = stateMachine

    def on_enter(self):
        logger.info(self.name)

    def on_update(self):
        try:
            client = LyncClient.GetClient()  # type: ignore
            if client.State == ClientState.Invalid:  # type: ignore
                logger.info("Lync client invalid. Retrying...")
                return
            global lyncClient
            lyncClient = client
            self.transition_to(SignInLyncClient(self.stateMachine))
        except ClientNotFoundException:  # type: ignore
            pass


class SignInLyncClient(statemachine.State):
    def __init__(self, stateMachine):
        self.name = "SignInLyncClient"
        self.stateMachine = stateMachine

    def on_enter(self):
        logger.info(self.name)

    def on_update(self):
        global lyncClient
        if lyncClient.State != ClientState.SignedIn:  # type: ignore
            logger.info("Waiting for sign in...")
            return
        logger.info("Lync client signed in successfully.")
        self.transition_to(LyncConnected(self.stateMachine))


class LyncConnected(statemachine.State):
    def __init__(self, stateMachine):
        self.name = "LyncConnected"
        self.stateMachine = stateMachine

    def on_enter(self):
        logger.info(self.name)
        global presence, lyncClient, tray
        # Fetch the initial presence state
        presence = get_contact_information(lyncClient)

        # Subscribe to the SelfContact's PresenceChanged event
        lyncClient.Self.Contact.ContactInformationChanged += (
            lambda source, e: on_contact_information_changed(tray, source, e)
        )

        # Subscribe to call events
        lyncClient.ConversationManager.ConversationAdded += on_conversation_added

        update_icon(tray, presence)

    def on_event(self, event):
        if event == "NotSignedInException":
            self.transition_to(GetLyncClient(self.stateMachine))


class FindSkysyLight(statemachine.State):
    def __init__(self, stateMachine):
        self.name = "FindSkysyLight"
        self.stateMachine = stateMachine

    def on_enter(self):
        logger.info(self.name)

    def on_update(self):
        global ser
        ports = serial.tools.list_ports.comports()
        port = find_device_port(ports)
        if port:
            ser = serial.Serial(port.device, 115200, timeout=1)
            self.transition_to(SkysyLightConnected(self.stateMachine))
        else:
            time.sleep(4)


class SkysyLightConnected(statemachine.State):
    def __init__(self, stateMachine):
        self.name = "SkysyLightConnected"
        self.stateMachine = stateMachine

    def on_enter(self):
        logger.info(self.name)

    def on_update(self):
        global ser
        try:
            update_light(ser, presence, incoming_call)
        except:
            if not ser.is_open:
                self.transition_to(SkysyLightDisconnected(self.stateMachine))
            else:
                self.transition_to(FindSkysyLight(self.stateMachine))


class SkysyLightDisconnected(statemachine.State):
    def __init__(self, stateMachine):
        self.name = "SkysyLightDisconnected"
        self.stateMachine = stateMachine

    def on_enter(self):
        logger.info(self.name)

    def on_update(self):
        global ser
        try:
            if not ser.is_open:
                ser.open()
            self.transition_to(SkysyLightConnected(self.stateMachine))
        except Exception as e:
            logger.exception(f"Could not open port: {e}")
            self.transition_to(FindSkysyLight(self.stateMachine))


if __name__ == "__main__":
    main()
