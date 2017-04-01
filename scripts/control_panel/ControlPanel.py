'''
based on przemoli-pygametutorial-540433c50ffc
'''
import sys
sys.path.append("../../python")
import re
import os
import time
import math
import datetime
from numpy import array
import pickle
import glob

import pygame
import util
import records
import eztext
import cevent
import drive


MAX_PRESSURE = 300 ### shutoff above this pressure
MIN_PRESSURE = 35

COLORKEY = (1, 128, 1)
CURSOR = ((16, 16),
          (0, 0),
          (0, 0, 64, 0, 96, 0, 112, 0, 120, 0, 124, 0, 126, 0, 127, 0,
           127, 128, 124, 0, 108, 0, 70, 0, 6, 0, 3, 0, 3, 0, 0, 0),
          (192, 0, 224, 0, 240, 0, 248, 0, 252, 0, 254, 0, 255, 0,
           255, 128, 255, 192, 255, 224, 254, 0, 239, 0, 207, 0, 135,
           128, 7, 128, 3, 0))
#cursor = ((8, 8),
#          (0, 0),
#          (255, 255, 255, 255, 255, 255, 255, 255),
#          (0, 0, 0, 0, 0, 0, 0, 0))

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

MMM_DATA = dict(init=False,
                interval=1,
                pump_rate=0,
                valve=0, ## for valve0 and valve1 control
                pump_state=True,
                amb_pressure=True,
                amb_temp=True,
                valve_state=True, ## for valve status request
               )
def mmm_update():
    '''
    Send commands to mmm board
    '''
    for k in MMM_DATA:
        MMM_DATA[k] = int(MMM_DATA[k])
    drive.send_cmd(**MMM_DATA)

def mmm_new_status(packet):
    '''
    Update leds when new status arrives.
    '''
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

class Widget:
    '''
    Pygame GUI Widget baseclass
    '''
    def __init__(self, parent, rect, colorkey=None, background_color=(0, 0, 0),
                 alpha=255, static=False):
        '''
        rect is where current widget live on parent
        rect[0] -- xleft
        rect[1] -- ytop
        rect[2] -- width
        rect[3] -- height
        '''
        self.background_color = background_color
        self.surf = pygame.Surface((rect[2], rect[3]))
        self.text_surf = None

        self.surf.set_alpha(alpha)
        if colorkey is not None:
            self.colorkey = colorkey
            self.surf.set_colorkey(self.colorkey)
        if self.surf.fill is not None:
            self.surf.fill(background_color)
        self.rect = rect
        self.parent = parent
        self.parent.widgets.append(self)
        self.static = static
        self.changed = True

        self.text = None
        self.fontsize = None
        self.color = None

    def render(self, surf):
        '''
        Update GUI image of self.
        '''
        rect = surf.blit(self.surf, (self.rect[0], self.rect[1]))
        self.changed = False
        return rect

    def set_text(self, text, fontsize, color=(0, 0, 255), align="l"):
        '''
        Set text
        '''
        self.changed = True
        if self.text_surf is None:
            self.text_surf = pygame.Surface((self.rect[2], self.rect[3]))

        font = pygame.font.Font(None, fontsize)
        text = font.render(text, 1, color)
        textpos = text.get_rect()
        location = self.surf.get_rect()
        if align == 'c':
            textoffset = ((location.width - textpos.width) / 2,
                          (location.height - textpos.height) / 2)
        elif align == 'l':
            textoffset = (0,
                          (location.height - textpos.height) / 2)
        elif align == 'r':
            textoffset = (location.width - textpos.width,
                          (location.height - textpos.height) / 2)
        self.surf.fill(self.background_color)
        self.surf.blit(text, textoffset)

        self.text = text
        self.fontsize = fontsize
        self.color = color

    def on_lbutton_down(self, event):
        'abstract'
        pass
    def on_lbutton_up(self, event):
        'abstract'
        pass
    def on_mbutton_down(self, event):
        'abstract'
        pass
    def on_mbutton_up(self, event):
        'abstract'
        pass
    def on_rbutton_down(self, event):
        'abstract'
        pass
    def on_rbutton_up(self, event):
        'abstract'
        pass

class Button(Widget):
    def __init__(self, parent, text, color, fontsize, command, *args, **kw):
        Widget.__init__(self, parent, *args, **kw)
        self.command = command
        self.set_text(text, fontsize, color)

    def on_mbutton_up(self, event):
        self.command()

    def config(self, **kw):
        '''
        Update widget with keywords
        '''
        text = self.text
        color = self.color
        fontsize = self.fontsize
        for k in kw:
            if k == 'color':
                color = kw[k]
                del kw['color']
            elif k == 'text':
                text = kw[k]
                del kw['text']
            elif k == 'fontsize':
                fontsize = kw[k]
                del kw['fontsize']
        self.set_text(text, fontsize, color, **kw)

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
                               (self.radius, self.radius), self.radius-1)
            pygame.draw.circle(self.surf, self.color,
                               (self.radius, self.radius), self.radius, 1)
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
        out = [intround(x) for x in out]
        # print xywh, out, self.rect
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
    last_cuff_pressure = last_cuff_pressure * .50 + pkt.cuff * .50
    # print last_cuff_pressure
    if recording:
        hirate.append([pkt.millis, pkt.cuff, pkt.flow, pkt.pulse])
        if len(hirate) > MAX_HIRATE_N:
            del MAX_HIRATE[-MAX_HIRATE_N:]
drive.subscribe(drive.MPID.PID, mpid_cb)
drive.subscribe(drive.StatusPID.PID, mmm_new_status)

######################### END mmM interaction

class Gauge(Widget):
    def __init__(self, parent, center, radius, angles, min_max_values, value=None,
                 dial_width=10, dial_color=(0, 0, 255),
                 inner_radius=30, colorkey=COLORKEY, *args, **kw):
        rect = (center[0] - radius, center[1] - radius, 2 * radius, 2 * radius)
        Widget.__init__(self, parent, rect, colorkey=colorkey, background_color=colorkey,
                        *args, **kw)
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
            pygame.draw.polygon(self.surf, self.dial_color, points, 0)
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
        pygame.draw.arc(self.surf, color,
                        (self.radius - radius, self.radius-radius, 2 * radius, 2 * radius),
                        -self.val2angle(maxval) - 1 * DEG,
                        -self.val2angle(minval) + 1 * DEG, thickness)


screen_touched = False
abort_test = False
class Mode:
    instruction = ''
    color = BLUE
    def __init__(self, tester):
        self.tester = tester
        self.start_time = None
        self.start_cuff_pressure = None

    def start(self):
        global screen_touched, abort_test
        screen_touched = False
        abort_test = False
        self.tester.instruction.set_text(self.instruction, 30, self.color)
        self.start_time = time.time()

    @staticmethod
    def is_complete():
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
        self.tester.bp_result.set_text("BP:", 30, BLUE)
        self.tester.map_result.set_text("MP:", 30, BLUE)
        self.tester.hr_result.set_text("HR:", 30, BLUE)

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
        path = os.path.join('../../data/', self.tester.user)
        if not os.path.exists(path):
            os.mkdir(path)
        n = len(glob.glob(os.path.join(path, '*.dat')))
        fn = os.path.join(path, str(n) + '.dat')
        pickle.dump(data, open(fn, 'wb'))
        print 'wrote', fn
        raw = data[:, 1]

        bp_result = 'BP:'
        map_result = 'MAP:'
        hr_result = 'HR:'
        error = True

        if len(raw) < 5 * 200: # 5 seconds of data
            bp_result = 'Data QTY Error'
        else:
            try:
                sys, dia, map, hr = util.blood_pressure(raw)
                error = False
            except IndexError, e:
                bp_result = 'Insuficient Data'
            except ValueError, e:
                bp_result = str(e)
            else:
                records.add_result(self.tester.user,
                                   sys, dia, map, hr, datetime.datetime.now())
                bp_result = 'BP: %d/%d' % (sys, dia)
                map_result = 'MP: %3d' % map
                hr_result = 'HR: %3d' % hr
        if error:
            color = RED
        else:
            color = BLUE
        self.tester.bp_result.set_text(bp_result, 30, color)
        self.tester.map_result.set_text(map_result, 30, color)
        self.tester.hr_result.set_text(hr_result, 30, color)
        return True

def collidepoint(rect, point):
    inx = rect[0] <= point[0] <= rect[0] + rect[2]
    iny = rect[1] <= point[1] <= rect[1] + rect[3]
    return inx and iny

def ask_radio(surf, prompt, options, txt_color=BLACK, default=None):
    nu_surf = pygame.Surface((WIDTH, 100))
    nu_surf.fill(WHITE)
    font = pygame.font.Font(None, 30)
    m_width = font.render('M', 1, txt_color).get_width()
    text = font.render(prompt, 1, txt_color)
    textpos = (10, 10)
    nu_surf.blit(text, textpos)
    x = 10 + text.get_width() + m_width

    rects = []
    for i, option in enumerate(options):
        text = font.render(option, 1, txt_color)
        textpos = (x, 10)
        nu_surf.blit(text, textpos)
        rect = text.get_rect()
        rect[0] = x
        rects.append(rect)
        x += text.get_width() + m_width

    done = False
    value = ''
    while not done:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.locals.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONUP:
                for i, rect in enumerate(rects):
                    if collidepoint(rect, event.pos):
                        value = options[i]
                        done = True
        surf.blit(nu_surf, (0, 0))
        pygame.display.flip()
    return value
def ask_string(surf, prompt, txt_color=BLACK):
    nu_surf = pygame.Surface((WIDTH, 100))
    nu_surf.fill(WHITE)
    txtbx = eztext.Input(maxlength=45, color=txt_color, prompt=prompt)
    done = False
    while not txtbx.done:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.locals.QUIT:
                txtbx.value = ''
                txtbx.done = True
        nu_surf.fill(WHITE)
        txtbx.update(events)
        txtbx.draw(nu_surf)
        surf.blit(nu_surf, (0, 0))
        pygame.display.flip()
    return txtbx.value

def new_user(surf):
    name = ask_string(surf, 'username:').lower()
    email = None
    while email is None:
        email = ask_string(surf, 'email:')
        if '@' not in email:
            email = None
    sex = ask_radio(surf, 'select gender:', ['female', 'male', 'other'])
    birth = None
    regexp = re.compile('[12][0-9]{3}-[0-9]{1,2}-[0-9]{1,2}')
    assert regexp.match('1970-03-10')
    while birth is None:
        birth = ask_string(surf, 'DOB(YYYY-MM-DD):')
        if not regexp.match(birth):
            birth = None
    
    try:
        records.add_user(sex, name, birth, email)
        out = name.lower()
    except Exception, e:
        print 'ERROR:', e
        out = None
        done = False
    return out

def prompt_user():
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
                if idx == len(users):
                    out = new_user(surf)
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
        self.user = records.get_lastuser()
        self.normal_transition = [1, 2, 3, 4, 1, 1]
        self.abort_transition  = [5, 5, 5, 5, 5, 5]
        self.interval_start = None
        self.interval_num = None

        self.cuff_pressure = None
        self.pump_led   = None
        self.valve0_led = None
        self.valve1_led = None

        self.instruction = None
        self.bp_result = None
        self.map_result = None
        self.hr_result = None
        self.user_wid = None
        self._display_surf = None
        self._running = False
        self.start = None

    @staticmethod
    def turn_pump_on():
        MMM_DATA['pump_rate'] = 1
        mmm_update()

    @staticmethod
    def turn_pump_off():
        MMM_DATA['pump_rate'] = 0
        mmm_update()

    @staticmethod
    def close_valve0():
        MMM_DATA['valve'] &= 01
        mmm_update()

    @staticmethod
    def open_valve0():
        MMM_DATA['valve'] |= 10
        mmm_update()

    @staticmethod
    def close_valve1():
        MMM_DATA['valve'] &= 0b10
        mmm_update()

    @staticmethod
    def open_valve1():
        MMM_DATA['valve'] |= 0b01
        mmm_update()

    @staticmethod
    def open_valves():
        MMM_DATA['valve'] = 0b11
        mmm_update()

    @staticmethod
    def close_valves():
        print 'open_valves'
        MMM_DATA['valve'] = 0b00
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
            self.user = prompt_user()
            if self.user is not None:
                self.user_wid.set_text(self.user, 30, BLUE)

            self.initialize()
            self.cuff_pressure.update(-1) # insure pressure gets updated.
        else:
            screen_touched = True

    def initialize(self):
        # pygame.init()

        pygame.display.init()
        pygame.font.init()
        # print pygame.display.Info()
        pygame.mouse.set_cursor(*CURSOR)

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

        self.instruction = Widget(self, rect=(WIDTH - 200, 0, 200, 50),
                                  background_color=(0, 0, 0))
        self.bp_result = Widget(self, rect=(WIDTH - 200, 75, 200, 30),
                                background_color=(0, 0, 0))
        self.map_result = Widget(self, rect=(WIDTH - 200, 100, 200, 30),
                                 background_color=(0, 0, 0))
        self.hr_result = Widget(self, rect=(WIDTH - 200, 125, 200, 30),
                                background_color=(0, 0, 0))
        self.bp_result.set_text("BP:", 30, BLUE)
        self.map_result.set_text("MP:", 30, BLUE)
        self.hr_result.set_text("HR:", 30, BLUE)
        self.user_wid = Widget(self, rect=(WIDTH - 150, HEIGHT-50, 200, 50),
                               background_color=(0, 0, 0))
        self.user_wid.set_text(self.user, 30, BLUE)
        self._display_surf = pygame.display.set_mode((WIDTH, HEIGHT),
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

        self.turn_pump_off()
        self.open_valve0()
        self.open_valve1()

        self.valve0_led.on() ## this should not be necessary
        self.valve1_led.on() ## this should not be necessary

        self._display_surf.blit(self._image_surf, (0, 0))

    def on_loop(self):
        if self.modes[self.mode].is_complete():
            if abort_test:
                self.mode = self.abort_transition[self.mode]
            else:
                self.mode = self.normal_transition[self.mode]
            self.modes[self.mode].start()

        ## update widgets
        drive.serial_interact(1)
        cuff_pressure = last_cuff_pressure
        self.cuff_pressure.update(int(cuff_pressure))
        # self.text.set_text('%3d' % cuff_pressure, 30)

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

    @staticmethod
    def on_cleanup():
        pygame.quit()

    def on_key_down(self, event):
        if event.key == pygame.locals.K_ESCAPE or event.key == pygame.locals.K_LEFT:
            self._running = False

    def mainloop(self):
        if self.initialize() == False:
            self._running = False
        count = 0
        while self._running:
            self.on_render()
            self.on_loop()
            drive.serial_interact()

            for event in pygame.event.get():
                self.on_event(event)
            count += 1
if __name__ == "__main__":
    theApp = Tester()
    theApp.open_valves()
    theApp.mainloop()
