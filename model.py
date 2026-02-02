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
    sum=0
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
P0=20.0

usage_dict_global = defaultdict(list)

def P_app(duration=1, name="app", bat_drain=0.01, disp=False, stream=False, base=0, I=125, clock_speed='med', usage_dict=False, brightness=0.5, screen_size=10568.16):
    energy_loss=bat_drain*max_bat
    drain=energy_loss/(duration/60)
    drain-=base
    p_app=drain
    display_power=0
    stream_power=0
    CPU_power=0
    if disp:
        display_power=P_disp(I, screen_size, brightness, power_area_density)
        #p_disp+=display_power
        drain-=display_power
    if stream:
        stream_power=P_stream(stream)
        #p_net+=stream_power
        drain-=stream_power
    if not usage_dict:
        usage=get_usage(drain, clock_speed, cores)
        usage_dict_global[name].append(usage)
        return p_app
    else:
        CPU_power = P_CPU(usage_dict[name], clock_speed)
        return display_power+stream_power+CPU_power

duration = 40*60
t=np.arange(duration) #minutes
P_doms = []
num_samples = 2
for _ in range(num_samples):
    P_doms.append(np.array([P0]*duration))

#Sample 1
#I had my watch connected via BT all day
P_doms[0]+=P_base(BT=1)
# I was connected to wifi until 5 am
P_doms[0][0:5*60]+=P_base(wifi='connected')
# Until 2PM I never turned off my wifi but was connected to 5G
P_doms[0][5*60:14*60]+=P_base(cell='5G', wifi='searching')
#Was home for rest of the night (connected to wifi)
P_doms[0][14*60:]+= P_base(wifi='connected')

#Sample 2
#Stayed at home until around 11am
P_doms[1][0:11*60]+=P_base(wifi='connected')
#Went out until around 2pm
P_doms[1][11*60:16*60]+=P_base(cell='5G', wifi='searching')
#Was home for rest of night
P_doms[1][16*60:]+=P_base(wifi='connected')

#usages are: d (display), s (stream)
#Event is:
#(start time, duration, app name, battery energy drain (percent as decimal), has display?, streams data?, idle power component, grey scale, clock speed)
events_test = [
    [
        #Started coros run
        (6*60, 48, 'coros', 0.32, '', '5G', 50, 'high'),
        #Someone checked my locatoin
        (8*60, 121, 'life360', 0.09, '', '', 200, 'low'),
        #Sent some emails
        (15*60, 5+5, 'gmail', 0.02, 'd', 'wifi', 70, 'med'),
        #I played polytopia game
        (17*60, 18, 'polytopia', 0.04, 'd', '', 130, 'high'),
        #I googled something
        (19*60, 8+18, 'chrome', 0.04, 'd', 'wifi', 100, 'low')
    ],
    #Tic toc 63%, maps 14, pandora 8, chrome 4, messages 3, phone 2
    [
        #Scrolled in the morning 0.72
        (5*60, 3*60, 'tictoc', 0.27, 'd', 'wifi', 125, 'med'),
        #Listend to music
        (8*60, 3*60, 'pandora', 0.08, '', '', 125, 'med'),
        #Took a drive
        (11*60, 28, 'maps', 0.07, 'd', '5G', 200, 'med'),
        #Googled something
        (12*60, 16, 'chrome', 0.04, 'd', '5G', 200, 'low'),
        #drove back home
        (15*60+5, 28, 'maps', 0.07, 'd', '5G', 200, 'med'),
        #scrolled some more
        (16*60, 60+54, 'tictoc', 0.18, 'd', 'wifi', 125, 'med'),
        #made a phone call
        (18*60, 17, 'phone', 0.02, '', 'wifi', 200, 'low'),
        #sent some texts
        (18*60+30, 19, 'messages', 0.03, 'd', 'wifi', 200, 'low'),
        #scrolled a bit 
        (19*60, 2*60, 'tictoc', 0.18, 'd', 'wifi', 125, 'med')
    ]
]

events_sim = [
    [
        #Started coros run
        (6*60, 48, 'coros', 0.32, '', '5G', 50, 'high'),
        #Someone checked my locatoin
        (8*60, 121, 'life360', 0.09, '', '', 200, 'low'),
        #Sent some emails
        (15*60, 5+5, 'gmail', 0.02, 'd', 'wifi', 70, 'med'),
        #I played polytopia game
        (17*60, 18, 'polytopia', 0.04, 'd', '', 130, 'high'),
        #I googled something
        (19*60, 8+18, 'chrome', 0.04, 'd', 'wifi', 100, 'low')
    ],
    #Tic toc 63%, maps 14, pandora 8, chrome 4, messages 3, phone 2
    [
        #Scrolled in the morning 0.72
        (5*60, 3*60, 'tictoc', 0.27, 'd', 'wifi', 125, 'med'),
        #Listend to music
        (8*60, 3*60, 'pandora', 0.08, '', '', 125, 'med'),
        #Took a drive
        (11*60, 28, 'maps', 0.07, 'd', '5G', 200, 'med'),
        #Googled something
        (12*60, 16, 'chrome', 0.04, 'd', '5G', 200, 'low'),
        #drove back home
        (15*60+5, 28, 'maps', 0.07, 'd', '5G', 200, 'med'),
        #scrolled some more
        (16*60, 60+54, 'tictoc', 0.18, 'd', 'wifi', 125, 'med'),
        #made a phone call
        (18*60, 17, 'phone', 0.02, '', 'wifi', 200, 'low'),
        #sent some texts
        (18*60+30, 19, 'messages', 0.03, 'd', 'wifi', 200, 'low'),
        #scrolled a bit 
        (19*60, 2*60, 'tictoc', 0.18, 'd', 'wifi', 125, 'med')
    ]
]

def model_usage(events, P_dom): 
    P=P_dom.copy()
    for time, duration, name, bat_drain, display, stream, I, speed in events:
        P[time:time+duration]+= P_app(duration, name, bat_drain, display, stream, P_dom[time], I, speed)
    return P

def simulate(events, P_dom, usage_dict, brightness, screen_size):
    P=P_dom.copy()
    for time, duration, name, bat_drain, display, stream, I, speed in events:
        P[time:time+duration]+= P_app(duration, name, bat_drain, display, stream, P_dom[time], I, speed, usage_dict, brightness, screen_size)
    return P

P_mods=[]
P_sims=[]

for i in range(num_samples):
    P_mods.append(model_usage(events_test[i], P_doms[i]))

for k, v in usage_dict_global.items():
    print(f"{k}: {v}")
    print()

#Average chip usage for now
usage_dict_avg = {k: float(np.mean(v)) for k, v in usage_dict_global.items()}
for i in range(num_samples):
    P_sims.append([simulate(events_sim[i], P_doms[i], usage_dict_avg, 0.5, screen_size), simulate(events_sim[i], P_doms[i], usage_dict_avg, 0.5, screen_size)])

t_ticknames = [i for i in range(1, 37, 5)]
t_tickvals = np.array(t_ticknames)*60

def analyze_power(P, max_bat, up=1, label=None):
    E = max_bat-np.cumsum(P)/60
    E_perc = E/max_bat
    idx_empty = np.abs(E).argmin()

    def plot_fig(y, name):
        plt.plot(t, y, label=label)
        plt.xticks(t_tickvals, t_ticknames)
        plt.grid()
        plt.title(name)

    plt.subplot(2, 1, 1)
    plot_fig(P, 'Power (mW) vs time (hours)')
    #plt.subplot(2, 2, 2)
    #plot_fig(E, 'Energy (mWh) vs time (hours)')
    #plt.plot(t, [0]*len(t))
    plt.subplot(2, 1, 2)
    plot_fig(E_perc, 'Battery life (percent of full) vs time (hours)')
    plt.scatter(t[idx_empty], E_perc[idx_empty])
    up_mod = -5 if up<0 else 0
    plt.annotate(
        f"{t[idx_empty]//60}",
        (t[idx_empty], E_perc[idx_empty]),
        textcoords="offset points",
        xytext=(-5, 5*up+up_mod)
    )
    #plt.plot(t, [0]*len(t))

for i in range(num_samples):
    plt.figure()
    sim5=P_sims[i][0].copy()
    sim5+=P_base(BT=True)
    sim1 = P_sims[i][0].copy()
    sim1-=P_doms[1]
    sim1+=P0
    sim2=sim1.copy()
    sim3=sim1.copy()
    sim4=sim1.copy()
    sim1+=P_base(wifi='connected')
    sim2+=P_base(cell='5G')
    sim3+=P_base(cell='5G', wifi='searching')
    sim4+=P_base(cell='LTE')
    analyze_power(P_mods[i], max_bat, -1, label='mixed wifi and 5G searching')
    analyze_power(sim1, max_bat, label='only wifi')
    analyze_power(sim2, max_bat, label='only 5G')
    analyze_power(sim3, max_bat, label='only 5G with wifi searching')
    analyze_power(sim4, max_bat, label='only LTE')
    analyze_power(sim5, max_bat, -1, label='mixed wifi and 5G searching with BT')
    plt.legend()
    plt.tight_layout()
    plt.show()