# -*-coding:Utf-8 -*

# ===========================================================

#              - Harfang - www.harfang3d.com

#                       - Python -

#       Basic initialisations and use of main devices

# ===========================================================

import gs

# ------------ Display object and Output screen:

renderer = gs.EglRenderer()
renderer.Open(640, 480)

# ------------ Check devices:

print("Installed devices:")
devices = gs.GetInputSystem().GetDevices()
for device in devices:
    print("Id: " + str(device.GetId()) + " - Name : " + device.GetName())

# ------------ Get devices:

keyboard_device = gs.GetInputSystem().GetDevice("keyboard")
mouse_device = gs.GetInputSystem().GetDevice("mouse")

# ------------ Main loop:

while renderer.GetDefaultOutputWindow():

    gs.GetInputSystem().Update()

    # --- Keyboard controls:

    if keyboard_device.WasPressed(gs.InputDevice.KeyEscape):
        break

    elif keyboard_device.WasPressed(gs.InputDevice.KeyA):
        print("A")

    elif keyboard_device.IsDown(gs.InputDevice.KeyZ):
        print("Z")

    elif keyboard_device.WasDown(gs.InputDevice.KeyE):
        print("E")

    # --- Keyboard key code:
    for key in range(0, gs.InputDevice.KeyLast):
        if keyboard_device.WasPressed(key):
            print("Key code: %d" % key)

    # --- Mouse controls:

    if mouse_device.WasButtonPressed(gs.InputDevice.Button0):
        print("Mouse position: %d,%d" % (
            mouse_device.GetValue(gs.InputDevice.InputAxisX), mouse_device.GetValue(gs.InputDevice.InputAxisY)))

    if mouse_device.IsButtonDown(gs.InputDevice.Button1):
        print("Mouse position: %d,%d" % (
            mouse_device.GetValue(gs.InputDevice.InputAxisX), mouse_device.GetValue(gs.InputDevice.InputAxisY)))

    if mouse_device.WasButtonReleased(gs.InputDevice.Button2):
        print("mouse position: %d,%d" % (
            mouse_device.GetValue(gs.InputDevice.InputAxisX), mouse_device.GetValue(gs.InputDevice.InputAxisY)))

    # --- End of frame:

    renderer.DrawFrame()
    renderer.ShowFrame()
    renderer.UpdateOutputWindow()
