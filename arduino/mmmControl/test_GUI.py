from drive import *
from Tkinter import *
STS_T0 = -46.85;
STS_GAIN = 175.72;

data = dict(init=False,
            interval=0,
            pump_rate=0,
            valve=0,
            valve_state=True,
            pump_state=True,
            amb_pressure=True,
            amb_temp=True
            )


def update():
    for k in data:
        data[k] = int(data[k])
    send_cmd(**data)
    print data

def pump_toggle():
    pump_b.config(background="red", activebackground="red")
    data['pump_rate'] = not int(data['pump_rate'])
    update()

def valve_toggle():
    valve_b.config(background="red", activebackground="red")
    data['valve'] = not int(data['valve'])
    update()

def set_sample_interval(val):
    data['interval'] = val
    update()

def set_pump_rate(val):
    data['pump_rate'] = int(val)

def set_valve(val):
    data['valve'] = val

r = Tk()

pump_b = Button(r, text="Pump Toggle", command=pump_toggle)
pump_b.grid(row=0, column=0)

valve_b = Button(r, text="Valve Toggle", command=valve_toggle)
valve_b.grid(row=0, column=1)

reset_b = Button(r, text="Update", command=update)
reset_b.grid(row=0, column=2)

reset_b = Button(r, text="Reset", command=reset)
reset_b.grid(row=0, column=3)

Label(r, text='Sample interval ms').grid(row=1, column=0)
sam_int = Scale(r, from_=0, to = 255, orient=HORIZONTAL, command=set_sample_interval)
sam_int.set(1)
def inc_sam_int(*args):
    sam_int.set(sam_int.get() + 1)
def dec_sam_int(*args):
    sam_int.set(sam_int.get() - 1)
r.bind("<Right>", inc_sam_int)
r.bind("<Left>", dec_sam_int)
sam_int.grid(row=1, column=1)

cuff = Scale(r, from_=0, to = 24000, orient=VERTICAL, label='Cuff')
pulse = Scale(r, from_=0, to = 1024, orient=VERTICAL, label='Pulse')
flow = Scale(r, from_=0, to = 3000, orient=VERTICAL, label='Flow')
cuff.grid(row=4, column=0);
pulse.grid(row=4, column=1);
flow.grid(row=4, column=2);

amb_temp = Scale(r, from_=0, to = 40, orient=VERTICAL, label='amb_temp')
amb_press = Scale(r, from_=0, to = 100000, orient=VERTICAL, label='amb_pressure')
amb_temp.grid(row=5, column=0);
amb_press.grid(row=5, column=1);


def check_serial():
    serial_interact()
    r.after(1, check_serial)

def new_data(packet):
    GAGE_MIN_COUNT = 2470
    GAGE_MAX_COUNT = 24575 # 0x5fff
    GAGE_COUNT_RANGE = GAGE_MAX_COUNT
    GAGE_MAX_PRESSURE_MB = 2000
    GAGE_SENSITIVITY = float(GAGE_COUNT_RANGE) / GAGE_MAX_PRESSURE_MB

    bits = packet[1]
    bar = (bits - GAGE_MIN_COUNT) / GAGE_SENSITIVITY
    mmhg = (bits - 2470) * 280 / 15030.
    cuff.set(mmhg)
    pulse.set(packet[3])
    if(packet[2] > 0):
        flow.set(packet[2])
        
    # print packet
def new_status(packet):
    if packet.devid == 3:
        amb_press.set(packet.value)
    elif packet.devid == 4:
        degrees_c = STS_T0 + (STS_GAIN * packet.value) / (1l << 16);
        amb_temp.set(degrees_c)
    elif packet.devid == 5:
        if packet.value:
            pump_b.config(background="green", activebackground="green")
        else:
            pump_b.config(background="grey", activebackground="grey")
    elif packet.devid == 6:
        if packet.value:
            valve_b.config(background="green", activebackground="green")
        else:
            valve_b.config(background="grey", activebackground="grey")
def new_short(packet):
    print packet, '%x %x' % (ord(packet[0]), ord(packet[1]))
    if packet[0] == 'F':
        print 'flow_serial_avail:', ord(packet[1])
    
subscribe(MeasurementsPID.PID, new_data)
subscribe(StatusPID.PID, new_status)
subscribe(ShortPID.PID, new_short)
# b = Button(r, text="Send Msg", command=update)
# b.grid(row=2, column=0, columnspan=2)
r.after(100, check_serial)
r.mainloop()
