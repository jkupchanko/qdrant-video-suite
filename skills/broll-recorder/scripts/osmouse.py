"""osmouse.py: move the REAL Windows mouse pointer smoothly and click, so a screen recording shows a genuine cursor.

usage: python osmouse.py move X Y [seconds]      eased glide to screen coordinates
       python osmouse.py click [X Y [seconds]]   glide (optional) then left click
       python osmouse.py key F11                 press a key (F11, ESC, ENTER, TAB, ...)
       python osmouse.py pos                     print the current pointer position
"""
import ctypes, math, sys, time
from ctypes import wintypes

u = ctypes.windll.user32
u.SetProcessDPIAware()
VK = {"F11": 0x7A, "ESC": 0x1B, "ENTER": 0x0D, "TAB": 0x09, "SPACE": 0x20, "END": 0x23, "HOME": 0x24, "PGDN": 0x22, "PGUP": 0x21}

def pos():
    p = wintypes.POINT(); u.GetCursorPos(ctypes.byref(p)); return p.x, p.y

def move(x, y, secs=1.0):
    x0, y0 = pos(); t0 = time.time()
    while True:
        k = min(1.0, (time.time() - t0) / max(0.01, secs)); k = k * k * (3 - 2 * k)
        # a slight arc so the glide does not look robotic
        arc = math.sin(k * math.pi) * min(40, abs(x - x0) * 0.06)
        u.SetCursorPos(int(round(x0 + (x - x0) * k)), int(round(y0 + (y - y0) * k - arc)))
        if k >= 1: break
        time.sleep(1 / 120)
    u.SetCursorPos(int(x), int(y))

def click():
    u.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.06); u.mouse_event(0x0004, 0, 0, 0, 0)

def key(name):
    vk = VK.get(name.upper()) or (ord(name.upper()) if len(name) == 1 else None)
    if vk is None: raise SystemExit("unknown key " + name)
    u.keybd_event(vk, 0, 0, 0); time.sleep(0.05); u.keybd_event(vk, 0, 2, 0)

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "pos": print(pos())
    elif a[0] == "move": move(float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 1.0)
    elif a[0] == "click":
        if len(a) >= 3: move(float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 1.0); time.sleep(0.15)
        click()
    elif a[0] == "key": key(a[1])
