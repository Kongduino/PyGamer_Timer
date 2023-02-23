import time, board, sys, keypad, displayio, gc
import busio, analogio, neopixel
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_cursorcontrol.cursorcontrol import Cursor
from adafruit_cursorcontrol.cursorcontrol_cursormanager import CursorManager
from colorsys import hls_to_rgb # from the adafruit bundle

# this produces a list of colours in the rainbow gradient
def rainbow_color_stops(n=10, end=2/3):
  return [hls_to_rgb(end * i/(n-1), 0.5, 1) for i in range(n)]

stops = 100
rainbow = rainbow_color_stops(stops, 1.0)

i2c = board.I2C()
display = board.DISPLAY
NEO_BRIGHTNESS = 0.3 # no need to blind people...
OFF = (0, 0, 0)
ON = (255, 255, 255) # aka white
strip = neopixel.NeoPixel(board.NEOPIXEL, 5, brightness=NEO_BRIGHTNESS)
strip.fill(OFF)

# the group that will hold all the UI elements
group = displayio.Group()
Label = label.Label
ff = "fonts/GoMono-Bold-36.bdf" # produced with fontforge
# Use whatever font you want/need
GoMonoBold36 = bitmap_font.load_font(ff)
timer1_label = Label(GoMonoBold36, text="00", color=0xffffff)
timer1_label.x = 20
timer1_label.y = 60
group.append(timer1_label)

timer2_label = Label(GoMonoBold36, text="00", color=0xffffff)
timer2_label.x = 100
timer2_label.y = 60
group.append(timer2_label)

timer3_label = Label(GoMonoBold36, text=":", color=0xffffff)
timer3_label.x = 70
timer3_label.y = 60
group.append(timer3_label)

#to manage the joystick
mouse_cursor = Cursor(display, display_group=group)
cursor = CursorManager(mouse_cursor)
display.show(group)
mouse_cursor.hide() # we don't need to show the mouse cursor

# the currently selected, and thus blinking, label
selectedLabel = timer1_label
displayState = True
lastRefresh = time.monotonic()
# Prep the LEDs
strip[0] = rainbow[4]
strip[1] = rainbow[3]
strip[2] = rainbow[2]
strip[3] = rainbow[1]
strip[4] = rainbow[0]
rainbowIndex = 5 # first 5 values in the rainbow have been used
lastLEDrefresh = time.monotonic()

while True:
    if time.monotonic() - lastLEDrefresh > 0.15:
        # let's change the LEDs
        for ix in range (0, 5):
            strip[4-ix]=strip[4-ix-1]
        strip[0] = rainbow[rainbowIndex]
        rainbowIndex += 1
        if rainbowIndex > 99:
            rainbowIndex = 0
        lastLEDrefresh = time.monotonic()
    if time.monotonic() - lastRefresh > 0.5:
        # Let's blink the currently selected label, mn or sec
        displayState = not displayState
        if displayState:
            selectedLabel.color = 0xFFFFFF
        else:
            selectedLabel.color = 0x000000
        lastRefresh = time.monotonic()
    # read the X axis: switch between mn and sec
    px = int(cursor._read_joystick_x()/1000)-32
    if px<-10:
        while px<-10:
            px = int(cursor._read_joystick_x()/1000)-32
        print("LEFT")
        selectedLabel.color = 0xFFFFFF
        if selectedLabel == timer1_label:
            selectedLabel = timer2_label
        else:
            selectedLabel = timer1_label
        selectedLabel.color = 0x000000
        displayState = False
        lastRefresh = time.monotonic()
    if px>10:
        while px>10:
            px = int(cursor._read_joystick_x()/1000)-32
        print("RIGHT")
        selectedLabel.color = 0xFFFFFF
        if selectedLabel == timer1_label:
            selectedLabel = timer2_label
        else:
            selectedLabel = timer1_label
        selectedLabel.color = 0x000000
        displayState = False
        lastRefresh = time.monotonic()
    # read the Y axis: increase / decrease the value
    py = int(cursor._read_joystick_y()/1000)-31
    if py<-10:
        tt = time.monotonic()
        while py<-10:
            py = int(cursor._read_joystick_y()/1000)-31
            if time.monotonic()-tt > 0.8:
                break
        print("UP")
        v = int(selectedLabel.text)-1
        if v<0:
            v = 59 # rotate between 0 and 59
        selectedLabel.text = ("0"+str(v))[-2:]
        selectedLabel.color = 0xFFFFFF
        displayState = True
        lastRefresh = time.monotonic()
    if py>10:
        tt = time.monotonic()
        while py>10:
            py = int(cursor._read_joystick_y()/1000)-31
            if time.monotonic()-tt > 0.8:
                break
        print("DOWN")
        v = int(selectedLabel.text)+1
        if v == 59:
            v = 0 # rotate between 0 and 59
        selectedLabel.text = ("0"+str(v))[-2:]
        selectedLabel.color = 0xFFFFFF
        displayState = True
        lastRefresh = time.monotonic()
    cursor.update()
    if cursor.is_clicked is True:
        while cursor.is_clicked is True:
            cursor.update() # debounce
        mn = int(timer1_label.text)
        sc = int(timer2_label.text)
        if mn == 0 and sc == 0:
            pass # nothing to do
        else:
            print(f"launching timer for {mn} mn, {sc} secs")
            strip.fill(ON)
            timer1_label.color = 0xFFFFFF
            timer2_label.color = 0xFFFFFF
            timer_ref=time.monotonic()
            totalTime = mn*60 + sc
            currentTime = totalTime
            saveMN = timer1_label.text
            saveSC = timer2_label.text
            while (currentTime) > 0:
                if time.monotonic()-timer_ref >= 1.0:
                    currentTime -= 1
                    px = int((currentTime/totalTime)*255)
                    # percentage, whcih will determine the value
                    strip.fill((px, px, px))
                    sc -= 1
                    if sc == -1:
                        sc = 59
                        mn -= 1
                        if mn == -1:
                            sys.exit()
                    timer1_label.text = ("0"+str(mn))[-2:]
                    timer2_label.text = ("0"+str(sc))[-2:]
                    timer_ref=time.monotonic()
            strip.fill(OFF)
            timer1_label.text = "00"
            timer2_label.text = "00"
            for i in range(0, 5):
                timer1_label.color = 0xFFFFFF
                timer2_label.color = 0xFFFFFF
                time.sleep(0.5)
                timer1_label.color = 0x000000
                timer2_label.color = 0x000000
                time.sleep(0.5)
            timer1_label.color = 0xFFFFFF
            timer2_label.color = 0xFFFFFF
            timer1_label.text = saveMN
            timer2_label.text = saveSC
