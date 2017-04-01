import sys
from pylab import *
from numpy import *
from drive import *

data = dict(init=False,
            interval=0,
            pump_rate=0,
            valve=0, ## for valve0 and valve1 control
            pump_state=True,
            amb_pressure=True,
            amb_temp=True,
            valve_state=True, ## for valve status request
            )


def update():
    for k in data:
        data[k] = int(data[k])
    send_cmd(**data)

N = 60 * 200
data = zeros((N, 2), int)
count = 0
def new_data(packet):
    global count
    # 0    - 2594
    # 200 -- 14500

    bits = packet[1]
    bar = (bits - GAGE_MIN_COUNT) / GAGE_SENSITIVITY
    mmhg = (bits - 2470) * 280 / 15030.
    if(count < N):
        data[count] = packet[0], packet[2]
        print count, data[count]
    # print packet
    count += 1
subscribe(MeasurementsPID.PID, new_data)

def check_serial():
    serial_interact()
while count < N:
    check_serial()

f = open(sys.argv[1], 'wb')
f.write(data.tostring())
f.close()
print 'wrote:', f.name

plot(data[:,0], data[:,1])
show()
