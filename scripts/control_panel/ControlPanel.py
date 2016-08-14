'''
based on przemoli-pygametutorial-540433c50ffc
'''
import drive
import util
import serial
import os
import time
import math
import pygame
from pygame.locals import *
import cevent
from numpy import random
import time
import records
import datetime

MAX_PRESSURE = 200 ### shutoff above this pressure
MIN_PRESSURE =  35

clock = pygame.time.Clock()
COLORKEY = (1, 128, 1)
cursor = ((16, 16),
          (0, 0),
          (0, 0, 64, 0, 96, 0, 112, 0, 120, 0, 124, 0, 126, 0, 127, 0,
           127, 128, 124, 0, 108, 0, 70, 0, 6, 0, 3, 0, 3, 0, 0, 0),
          (192, 0, 224, 0, 240, 0, 248, 0, 252, 0, 254, 0, 255, 0,
           255, 128, 255, 192, 255, 224, 254, 0, 239, 0, 207, 0, 135,
           128, 7, 128, 3, 0))
cursor = ((8, 8),
          (0, 0),
          (255, 255, 255, 255, 255, 255, 255, 255),
          (0, 0, 0, 0, 0, 0, 0, 0))
import time
from numpy import diff, median, nan, array

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

mmm_data = dict(init=False,
                interval=1,
                pump_rate=0,
                valve=0, ## for valve0 and valve1 control
                pump_state=True,
                amb_pressure=True,
                amb_temp=True,
                valve_state=True, ## for valve status request
)
def mmm_update():
    for k in mmm_data:
        mmm_data[k] = int(mmm_data[k])
    drive.send_cmd(**mmm_data)

def mmm_new_status(packet):
    ### update leds
    if packet.name == 'Pump':
        if packet.value:
            theApp.pump_led.on()
        else:
            theApp.pump_led.off()
    if packet.name == 'Valve':
        if packet.value & 0b01:
            theApp.valve0_led.on()
        else:
            theApp.valve0_led.off()
        if packet.value & 0b10:
            theApp.valve1_led.on()
        else:
            theApp.valve1_led.off()
            
class Buff:
    def __init__(self, max_size=10):
        self.data = []
        self.max_size = max_size

    def append(self, item):
        self.data.append(item)
	self.data = self.data[-self.max_size:]

    def get(self):
        out = self.data[:]
        return out

DEG = math.pi / 180.
WIDTH = 800
HEIGHT = 480
WIDTH = 480
HEIGHT = 272

UNITS = {'MIN': 60,
         'HOUR': 3600,
         'SEC': 1}
MIN = UNITS['MIN']
SEC = UNITS['SEC']
HOUR = UNITS['HOUR']

def html2rgb(s):
    rr = int(s[1:3], 16)
    gg = int(s[3:5], 16)
    bb = int(s[5:7], 16)
    return [rr, gg, bb, 255]
    
class Widget:
    def __init__(self, parent, rect, colorkey=None, background_color=(0, 0, 0),
                 alpha=255, static=False):
        '''
        rect is where current widget live on parent
        rect[0] -- xleft
        rect[1] -- ytop
        rect[2] -- width
        rect[3] -- height
        '''
        self.background_color=background_color
        self.surf = pygame.Surface((rect[2], rect[3]))
        self.text_surf = None

        self.surf.set_alpha(alpha)
        if colorkey is not None:
            self.colorkey = colorkey
            self.surf.set_colorkey(self.colorkey)
        if self.surf.fill is not None:
            self.surf.fill(background_color)
        self.rect = rect
        self.Rect = Rect(rect)
        self.parent = parent
        self.parent.widgets.append(self)
        self.static=static
        self.changed = True

        self.text = None
        self.fontsize = None
        self.color = None

    def render(self, surf):
        rect = surf.blit(self.surf, (self.rect[0], self.rect[1]))
        self.changed = False
        return rect

    def add_text(self, text, fontsize, color=(0, 0, 255)):
        self.changed = True
        if self.text_surf is None:
            self.text_surf = pygame.Surface((self.rect[2], self.rect[3]))

        font = pygame.font.Font(None, fontsize)
        text = font.render(text, 1, color)
        textpos = text.get_rect()
        location = self.surf.get_rect().center
        textpos.center = location
        self.surf.fill(self.background_color)
        self.surf.blit(text, textpos)
        # self.text_surf.blit(text, (0, 0))

        self.text = text
        self.fontsize = fontsize
        self.color = color

    def on_lbutton_down(self, event):
        pass
    def on_lbutton_up(self, event):
        pass
    def on_mbutton_down(self, event):
        pass
    def on_mbutton_up(self, event):
        pass
    def on_rbutton_down(self, event):
        pass
    def on_rbutton_up(self, event):
        pass
    
class Button(Widget):
    def __init__(self, parent, text, color, fontsize, command, *args, **kw):
        Widget.__init__(self, parent, *args, **kw)
        self.command = command
        self.add_text(text, fontsize, color)
        
    def on_mbutton_up(self, event):
        self.command()
        
    def config(self, **kw):
        text = self.text
        color = self.color
        fontsize = self.fontsize
        for k in kw:
            if k == 'color':
                color = kw[k]
            elif k == 'text':
                text = kw[k]
            elif k == 'fontsize':
                fontsize=kw[k]
        self.add_text(text, fontsize, color)

    
class LED(Widget):
    def __init__(self, parent, color, position, radius, status,
                 *args, **kw):
        rect = (position[0] - radius, position[1] - radius,
                2 * radius, 2 * radius)
        Widget.__init__(self, parent, rect, static=False
                        *args, **kw)

        self.color = color
        self.radius = radius
        self.status = not status ## insure update
        if status:
            self.on()
        else:
            self.off()
        
    def on(self, color=None):
        if color is None:
            color = self.color
        if not self.status:
            pygame.draw.circle(self.surf, color,
                               (self.radius, self.radius), self.radius)
            self.status = True
            self.changed = True
    def off(self):
        if self.status:
            pygame.draw.circle(self.surf, (0, 0, 0),
                               (self.radius, self.radius), self.radius-1,
            )
            pygame.draw.circle(self.surf, self.color,
                               (self.radius, self.radius), self.radius,
                               1)
            self.status = False
            self.changed = True
        
class Chart(Widget):
    def __init__(self, parent, rect, xmin, xmax, ymin, ymax, *args, **kw):
        Widget.__init__(self, parent, rect, *args, **kw)
        self.mx = float(rect[2] - rect[0]) / (xmax - xmin)
        self.bx = rect[0]
        self.my = float(rect[3]) / (ymax - ymin)
        self.by = rect[1]
        self.width = xmax - xmin
        self.height = ymax - ymin
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.bars = []

    def addline(self, color, xstart, ystart, xstop, ystop, thickness=1):
        px = (xstart - self.xmin) * float(self.rect[2]) / self.width
        py = (ystart - self.ymin) * float(self.rect[3]) / self.height
        qx = (xstop - self.xmin) * float(self.rect[2]) / self.width
        qy = (ystop - self.ymin) * float(self.rect[3]) / self.height
        start = (px, self.rect[3] - py)
        stop = (qx, self.rect[3] - qy)
        pygame.draw.line(self.surf, color, start, stop, thickness)
        self.changed = True

    def addbar(self, bar):
        self.bars.append(bar)
        color, bar = bar
        rect = self.transform(bar)
        if rect:
            self.surf.fill(color, rect)

    def transform(self, xywh):
        x, y, w, h = xywh
        my = -self.rect[3] / float(self.ymax - self.ymin)
        top = my * (y - self.ymax)
        bottom = my * (y + h - self.ymax)
        bottom = float(h) / (self.ymax - self.ymin)

        # (x, y) = upper left
        # (x + w, y + h) = lower right
        out = [x * self.rect[2] / (self.xmax - self.xmin),
               top,
               w * self.rect[2] / float(self.xmax - self.xmin),
               h * self.rect[3] / float(self.ymax - self.ymin)]
        if out[3] < 1:
            out[3] = 1
        if out[-2] < 1:
            out[-2] = 1
        def intround(v):
            return int(round(v))
        out = map(intround, out)
        # print xywh, out, self.rect
        return out

def readline():
    return ser.read(100)

def fast_readline():
    out = []
    c = 0
    while c and c != '\r':
        c = ser.read(1)
        out.append(c)
    return ''.join(out)

class ExpFilterDeco:
    '''
    An exponential filter decorator for the getSpeed and getCadence functions.
    
    return alpha * f + (1 - alpha) * last_f
    '''
    def __init__(self, alpha):
        self.alpha = alpha
        self.last = [None]
    def __call__(self, f):
        def out():
            out = f()
            if self.last[0] is not None:
                out = out * self.alpha + self.last[0] * (1 - self.alpha)
            self.last[0] = out
            return out
        return out
class FreshFish:
    '''
    Keep result around for specified time.  Refresh when fish goes bad
    '''
    def __init__(self, shelf_life=1):
        self.shelf = shelf_life
        self.last_time = 0
        self.last_result = None

    def __call__(self, f):
        def out():
            if time.time() - self.last_time < self.shelf:
                res = self.last_result
            else:
                res = f()
                self.last_time = time.time()
                self.last_result = res
            return res
        return out

######################### mmM interaction

last_cuff_pressure = 123
hirate = []
recording = False
MAX_HIRATE_N = 200 * 60 * 2
def start_recording():
    global recording
    del hirate[:]
    recording = True

def stop_recording():
    global recording
    recording = False
def mpid_cb(pkt):
    global last_cuff_pressure
    last_cuff_pressure = last_cuff_pressure * .90 + pkt.cuff * .10
    # print last_cuff_pressure
    if recording:
        hirate.append([pkt.millis, pkt.cuff, pkt.flow, pkt.pulse])
        if len(hirate) > MAX_HIRATE_N:
            del MAX_HIRATE[-MAX_HIRATE_N:]
drive.subscribe(drive.MPID.PID, mpid_cb)
drive.subscribe(drive.StatusPID.PID, mmm_new_status)
######################### END mmM interaction


@ExpFilterDeco(.01)
@FreshFish(2)
def getHR():
    out = 100

    return out

class Gauge(Widget):
    def __init__(self, parent, center, radius, angles, min_max_values, value=None,
                 dial_width=10, dial_color=(0, 0, 255),
                 inner_radius=30, colorkey=COLORKEY, *args, **kw):
        rect = (center[0] - radius, center[1] - radius, 2 * radius, 2 * radius)
        Widget.__init__(self, parent, rect, colorkey=colorkey, background_color=colorkey, *args, **kw)
        self.center = center
        self.radius = radius
        self.angles = angles
        self.values = min_max_values
        self.dial_width = dial_width
        self.inner_radius = inner_radius
        if value is not None:
            self.update(value)
        self.dial_color = dial_color
        self.value = self.values[0]
        
    def val2angle(self, value):
        frac = float(value - self.values[0]) / (self.values[1] - self.values[0])
        if frac > 1.05:
            frac = 1.05
        if frac < -.05:
            frac = -.05
        angle = (self.angles[0] + frac * (self.angles[1] - self.angles[0])) * math.pi / 180
        return angle
    
    def update(self, value):
        if value != self.value:
            angle = self.val2angle(value)
            points = [(self.radius - self.dial_width/2 * math.sin(angle),
                       self.radius + self.dial_width/2 * math.cos(angle)),
                      (self.radius + self.radius*math.cos(angle),
                       self.radius + self.radius*math.sin(angle)),
                      (self.radius + self.dial_width/2 * math.sin(angle),
                       self.radius - self.dial_width/2 * math.cos(angle))]

            self.surf.fill(self.colorkey)
            pygame.draw.polygon(self.surf, self.dial_color, points , 0)
            self.value = value
            self.changed = True

            if self.inner_radius > 0:
                pygame.draw.circle(self.surf, (0, 0, 0),
                                   [self.radius, self.radius],
                                   self.inner_radius)

                font = pygame.font.Font(None, 30)
                hi = font.render(str(self.value), True, self.dial_color)
                hi_x = self.radius - hi.get_width() / 2
                hi_y = self.radius - hi.get_height() / 2
            self.surf.blit(hi, (hi_x, hi_y))
            
        else:
            self.changed = False

    def arc(self, minval, maxval, radius, thickness, color):
        '''
        draw a wedge behind the gauge
        '''
        pygame.draw.arc(self.surf, color, (self.radius - radius, self.radius-radius, 2 * radius, 2 * radius),
                        -self.val2angle(maxval) - 1 * DEG, -self.val2angle(minval) + 1 * DEG, thickness)


screen_touched = False
abort_test = False
class Mode:
    instruction = ''
    color = BLUE
    def __init__(self, tester):
        self.tester = tester

    def start(self):
        global screen_touched, abort_test
        screen_touched = False
        abort_test = False
        self.tester.instruction.add_text(self.instruction, 30, self.color)
        self.start_time = time.time()

    def is_complete(self):
        return True
class Abort(Mode):
    instruction = 'Test Aborted!'
    color = RED
    def start(self):
        Mode.start(self)
        self.tester.open_valves()
        stop_recording()

    def is_complete(self):
        return (last_cuff_pressure < 5 and
                time.time() - self.start_time > 5)
class Start(Mode):
    instruction = 'Starting...'

class Ready(Mode):
    instruction = 'Touch to begin'
    def start(self):
        Mode.start(self)
        self.tester.open_valves()
        stop_recording()

    def is_complete(self):
        global screen_touched
        out = screen_touched
        screen_touched = False
        return out

class Inflate(Mode):
    instruction = 'Touch to abort'
    max_inflate_start_time = 5 
    def start(self):
        Mode.start(self)
        self.tester.inflate(MAX_PRESSURE)
        stop_recording()
        self.start_cuff_pressure = last_cuff_pressure
        self.tester.results.add_text("SYS/DIA", 30, BLUE)

    def is_complete(self):
        global abort_test
        complete = last_cuff_pressure > MAX_PRESSURE or abort_test
        if screen_touched:
            abort_test = True
            self.tester.turn_pump_off()

        elif (time.time() - self.start_time > self.max_inflate_start_time and
              last_cuff_pressure - self.start_cuff_pressure < 10):
            abort_test = True
            self.tester.turn_pump_off()
        else:
            if complete:
                self.tester.turn_pump_off()
        return complete
class Deflate(Mode):
    instruction = 'Remain still'
    def start(self):
        Mode.start(self)
        self.tester.deflate_slow(10)
        start_recording()

    def is_complete(self):
        complete = last_cuff_pressure < MIN_PRESSURE
        if complete:
            self.tester.open_valves()
            stop_recording()
        return complete

class Compute(Mode):
    instruction = 'Computing BP'
    def start(self):
        Mode.start(self)
        self.tester.on_render()

    def is_complete(self):
        Mode.start(self)
        data = array(hirate)
        raw = data[:,1]
        if len(raw) < 5 * 200: # 5 seconds of data
            error = True
            color = RED
            results = 'Data Error'
        else:
            try:
                sys, dia, mad_failed = util.blood_pressure(raw)
                error = False
            except IndexError, e:
                print 'Error', e
                error = True
            except ValueError, e:
                print 'Error:', e
                error = True
            if mad_failed:
                results = 'Mad Failed!'
                color = RED
            elif error:
                results = 'ERROR' 
            else:
                records.add_result(self.tester.user,
                                   sys, dia, datetime.datetime.now())
                results = '%d/%d' % (sys, dia)
                color = BLUE
        self.tester.results.add_text(results, 30, color)
        return True

def collidepoint(rect, point):
    inx = rect[0] <= point[0] <= rect[0] + rect[2]
    iny = rect[1] <= point[1] <= rect[1] + rect[3]
    return inx and iny

def userscreen():
    surf = pygame.display.get_surface()
    surf.fill(BLACK)
    users = records.get_users()

    font = pygame.font.Font(None, 30)
    for i, user in enumerate(users):
        text = font.render(user[1], 1, BLUE)
        textpos = (10, i * 20 + 10)
        surf.blit(text, textpos)
    i = len(users)
    textpos = (10, i * 20 + 10)
    text = font.render("add", 1, RED)
    surf.blit(text, textpos)
    
    pygame.display.flip()
    done = False
    out = None
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONUP:
                idx = (event.pos[1] - 10) / 20
                if idx < len(users):
                    out = users[idx][1]
                    done = True
                elif idx == len(users):
                    def new_user():
                        print 'TODO: Make this a pygame GUI'

                        try:
                            name = raw_input('username:')
                            sex = raw_input('sex: (M/F/O)')
                            if sex not in 'MFO':
                                raise ValueError("Sex not understood: %s" % sex)
                            else:
                                sex = {'M':'male','F':'female','O':'other'}[sex]
                            year = int(raw_input("birth year (YYYY):"))
                            month = int(raw_input("birth month (MM):"))
                            day = int(raw_input("birth day (DD):"))
                            birth = datetime.datetime(year, month, day)
                            records.add_user(sex, name, birth)
                            out = name.lower()

                        except Exception, e:
                            print e
                            out = None
                        return out
                    out = new_user()
                    if out is not None:
                        done = True
                        
    return out
class Tester(cevent.CEvent):
    def __init__(self):
        self._running = True
        self._display_surf = None
        self._image_surf = None
        self.widgets = []
        self.last_loop_time = None
        self.mode = 0
        self.modes = [Start(self),
                      Ready(self),
                      Inflate(self),
                      Deflate(self),
                      Compute(self),
                      Abort(self)]
        self.user = 'anon'
        self.normal_transition = [1, 2, 3, 4, 1, 1]
        self.abort_transition  = [5, 5, 5, 5, 5, 5]
        
    def turn_pump_on(self):
        mmm_data['pump_rate'] = 1
        mmm_update()
        
    def turn_pump_off(self):
        mmm_data['pump_rate'] = 0
        mmm_update()

    def close_valve0(self):
        mmm_data['valve'] &= 01
        mmm_update()
        
    def open_valve0(self):
        mmm_data['valve'] |= 10
        mmm_update()

    def close_valve1(self):
        mmm_data['valve'] &= 0b10
        mmm_update()

    def open_valve1(self):
        mmm_data['valve'] |= 0b01
        print mmm_data['valve']
        mmm_update()

    def open_valves(self):
        mmm_data['valve'] = 0b11
        mmm_update()

    def close_valves(self):
        print 'open_valves'
        mmm_data['valve'] = 0b00
        mmm_update()

    def inflate(self, mmhg):
        self.close_valves()
        if last_cuff_pressure < mmhg:
            self.turn_pump_on()

    def deflate_slow(self, mmhg):
        self.turn_pump_off()
        if last_cuff_pressure > mmhg:
            self.open_valve1()
            
    def on_mbutton_up(self, event):
        global screen_touched
        if collidepoint(self.user_wid.rect, event.pos):
            self.user = userscreen()
            self.user_wid.add_text(self.user, 30, BLUE)
            self.initialize()
            self.cuff_pressure.update(-1) # insure pressure gets updated.
        else:
            screen_touched = True
    
    def initialize(self):
        # pygame.init()
        pygame.display.init()
        pygame.font.init()
        # print pygame.display.Info()
        pygame.mouse.set_cursor(*cursor)
        
        ## create widgets.
        # self.text = Widget(self, (60, HEIGHT - 40, 60, 30),
        #                    background_color=(0, 0, 0))
        # self.cuff_pressure = Gauge(self, (WIDTH / 2, HEIGHT / 2), 100, [120, 420],
        #                    [0, 300],
        #                    dial_color=(255, 0, 0),
        #                    inner_radius=20)
        self.cuff_pressure = Gauge(self, (130, 133), 100, [117.5, 422.5],
                           [0, 300],
                           dial_color=(255, 0, 0),
                           inner_radius=20)
        self.pump_led   = LED(self, (0, 0, 255), (10, 10), 6, False)
        self.valve0_led = LED(self, (0, 0, 255), (10, 30), 6, False)
        self.valve1_led = LED(self, (0, 0, 255), (10, 50), 6, False)
        def start_bp():
            pass
        
        self.instruction = Widget(self, rect=(WIDTH - 200, 0, 200, 50),
                                  background_color=(0, 0, 0))
        self.results = Widget(self, rect=(WIDTH - 150, 50, 200, 50),
                              background_color=(0, 0, 0))
        self.results.add_text("SYS/DIA", 30, BLUE)
        self.user_wid = Widget(self, rect=(WIDTH - 150, HEIGHT-50, 200, 50),
                              background_color=(0, 0, 0))
        self.user_wid.add_text(self.user, 30, BLUE)
        self._display_surf = pygame.display.set_mode((WIDTH,HEIGHT),
                                                     pygame.HWSURFACE)
        self._running = True
        # self._image_surf = pygame.image.load("WyoLum_racing.png").convert()
        # self._image_surf = pygame.image.load("images/background.png").convert()
        background = os.path.join(os.path.split(__file__)[0], 'images/background_480_272.png')
        self._image_surf = pygame.image.load(background).convert()

        ### put all static widgets on image surf
        for wid in self.widgets:
            if wid.static:
                pass
            #   wid.render(self._image_surf)
        
        self.start = time.time()
        self.interval_start = 0
        self.interval_num = 0
        self._display_surf.blit(self._image_surf,(0,0))

    def on_loop(self):
        if self.modes[self.mode].is_complete():
            if abort_test:
                self.mode = self.abort_transition[self.mode]
            else:
                self.mode = self.normal_transition[self.mode]
            self.modes[self.mode].start()
        ## update values
        rect = self._display_surf.get_rect()
        now = time.time() - self.start
        duration = 300

        ## update widgets
        drive.serial_interact(1)
        cuff_pressure = last_cuff_pressure
        self.cuff_pressure.update(int(cuff_pressure))
        # self.text.add_text('%3d' % cuff_pressure, 30)

        self.last_loop_time = time.time()

    def on_render(self):
        ## render children
        for wid in self.widgets:
            if not wid.static:
                if wid.changed:
                    self._display_surf.blit(self._image_surf, wid.rect[:2],
                                            (wid.rect))
                    rect = wid.render(self._display_surf)
                    pygame.display.update(rect)
        pygame.display.flip()
    def on_exit(self):
        self._running = False

    def on_cleanup(self):
        pygame.quit()

    def on_key_down(self, event):
        if event.key == K_ESCAPE or event.key == K_LEFT:
            self._running = False
        
    def mainloop(self):
        if self.initialize() == False:
            self._running = False
        count = 0
        while(self._running):
            self.on_render() 
            self.on_loop()
            drive.serial_interact()
            # clock.tick(100)

            for event in pygame.event.get():
                self.on_event(event)
            count += 1
if __name__ == "__main__" :
    theApp = Tester()
    theApp.open_valves()
    theApp.mainloop()
