import ImageTk
from pylab import *
import glob
from Tkinter import *
import bpc
import PIL.Image as Image

offx=30
offy=10
fontsize=18

WIDTH = 800
HEIGHT = 480
class CanvasButton:
    buttons = []
    def top(self):
        self.can.lift('button')
    def __init__(self, can, label, bbox, anchor='center', 
                 offx=offx, offy=offy, fontsize=fontsize,
                 command=None):
        self.bbox = bbox
        self.command = command

        can.create_text(bbox[0] + offx, 
                        bbox[1] + offy, 
                        text=label,
                        font=("Helvetica", fontsize),
                        anchor=anchor, 
                        tag='button')
        can.create_rectangle(bbox[0], bbox[1], 
                             bbox[2] + bbox[0], 
                             bbox[3] + bbox[1])
        self.buttons.append(self)
        can.bind('<Button-1>', self.find_button)
        self.can = can

    def find_button(self, event):
        x = event.x
        y = event.y
        for b in self.buttons:
            if b.command is not None:
                if (b.bbox[0] < x and x < b.bbox[0] + b.bbox[2] and
                    b.bbox[1] < y and y < b.bbox[2] + b.bbox[3]):
                    b.command(event)

def clear_can():
    can.delete("image")
    # can.create_rectangle(0, 0, WIDTH, HEIGHT, fill='white')
    can.update_idletasks()
image_tk = None
def display_image(im):
    '''
    display image im in GUI window
    '''
    global image_tk
    
    x,y = im.size
    
    scale = max([x/float(WIDTH), y/float(HEIGHT)])
    x = int(x / scale)
    y = int(y / scale)

    im = im.resize((x,y));
    image_tk = ImageTk.PhotoImage(im)

    ## delete all canvas elements with "image" in the tag
    clear_can()
    can.create_image([(WIDTH + x) / 2 - x/2,
                      0 + y / 2], 
                     image=image_tk, 
                     tag="image")
root = Tk()
root.attributes("-fullscreen",False)
ucontrol = None
listener = None
def start(event):
    global ucontrol, listener
    global image_tk
    if image_tk is not None:
        del image_tk
    clear_can()
    if listener is None:
        listener = bpc.Listener()
    if ucontrol is None:
        ucontrol = bpc.uControl(listener)
    try:
        name = "test%d.uct" % start.tid
        sys, dia = bpc.main(name, listener, ucontrol)
        image_fn = 'images/%s.png' % name
        figure(620)
        title('%.0f/%.0f' % (sys, dia))
        savefig(image_fn)

        start.tid += 1
        im = Image.open(image_fn)
        display_image(im)
        can.update_idletasks()
        clf()
        start_b.top()
    finally:
        ucontrol.deflate(10, fast=True)
start.tid = len(glob.glob('images/*.uct'))


can = Canvas(root, width=WIDTH, height=HEIGHT)
start_b = CanvasButton(can, 'Start', (0, 0, 80, 20), command=start)
can.pack()
root.mainloop()
import sys
sys.exit()
