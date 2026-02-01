import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

def P_disp(I, A, B, c):
    #I is average grey level (0 to 255)
    #A is screen area (mm^2)
    #B is brightness (0 to 1)
    #c is parameter for average power per area (fit)
    return I**(2.2)*A*B*c

def P_CPU(U, clock_speed='med', N=6):
    #U is average usage of cores
    #b and m are fitted intercept/baseline core power consumption and slope respectively
    if clock_speed=='high':
        b=125
        m=1000*N-b
    elif clock_speed=='med':
        b=100
        m=500*N-b
    elif clock_speed=='low':
        b=75
        m=200*N-b
    return m*U+b
def get_usage(P, clock_speed='med', N=6):
    if clock_speed=='high':
        b=125
        m=1000*N-b
    elif clock_speed=='med':
        b=100
        m=500*N-b
    elif clock_speed=='low':
        b=75
        m=200*N-b
    return (P-b)/m

def P_base(cell=0, wifi=0, BT=0):
    sum=20
    if cell=='5G':
        sum+=260
    elif cell=='LTE':
        sum+=160
    if wifi=='searching':
        sum+=72
    elif wifi=='connected':
        sum+=32
    if BT:
        sum+=88
    return sum

def P_stream(net):
    if net=='wifi':
        return 566
    elif net=='LTE':
        return 749
    elif net=='5G':
        return 859
    
#power distributions
p_disp=0
p_net=0

#Custom parameters for my phone
max_bat = 13819 #miliwatt hours
brightness=0.5 #My brightness was constant all day
screen_size = 10568.16 #milimeters^2
power_area_density=0.000000552 #guessed from figure
cores=6

usage_dict = defaultdict(list)

def P_app(duration=1, name="app", bat_drain=0.01, disp=False, stream=False, base=0, I=125, clock_speed='med', usage_dict=False):
    energy_loss=bat_drain*max_bat
    drain=energy_loss/(duration/60)
    drain-=base
    p_app=drain
    if disp:
        display_power=P_disp(I, screen_size, brightness, power_area_density)
        #p_drain+=display_power
        drain-=display_power
    if stream:
        stream_power=P_stream(stream)
        #p_net+=stream_power
        drain-=stream_power
    usage=get_usage(drain, clock_speed, cores)
    #usage_dict[name].append(usage)
    return p_app

duration = 40*60
t=np.arange(duration) #minutes

#Create baseline usages first
P = np.array([0.0]*duration)
#I had my watch connected via BT all day
P+=P_base(BT=1)
# I was connected to wifi until 5 am
P[0:5*60]+=P_base(wifi='connected')
# Until 2PM I never turned off my wifi but was connected to 5G
P[5*60:14*60]+=P_base(cell='5G', wifi='searching')
#Until 8PM I was connected to wifi
P[14*60:]+= P_base(wifi='connected')

base=P.copy()

#usages are: d (display), s (stream)
#Event is:
#(start time, duration, app name, battery energy drain %, has display?, streams data?, idle power component, grey scale, clock speed)
events = [
    #Started coros run
    (6*60, 42, 'coros', 0.34, '', '5G', 50, 'high'),
    #Someone checked my locatoin
    (8*60, 56, 'life360', 0.09, '', '', 200, 'med'),
    #I played polytopia game
    (17*60, 18, 'polytopia', 0.04, 'd', '', 130, 'high')
]

for time, duration, name, bat_drain, display, stream, I, speed in events:
    P[time:time+duration]+= P_app(duration, name, bat_drain, display, stream, base[time], I, speed)

print(usage_dict)

#def simulate(events):


E = max_bat-np.cumsum(P)/60
E_perc = E/max_bat
t_ticknames = [i for i in range(1, 37)]
t_tickvals = np.array(t_ticknames)*60

plt.figure()
plt.plot(t, P)
plt.xticks(t_tickvals, t_ticknames)
plt.grid()

plt.figure()
plt.plot(t, E)
plt.plot(t, [0]*len(t))
plt.xticks(t_tickvals, t_ticknames)
plt.grid()

plt.figure()
plt.plot(t, E_perc)
plt.plot(t, [0]*len(t))
plt.xticks(t_tickvals, t_ticknames)
plt.grid()

plt.show()