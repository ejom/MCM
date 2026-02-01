def P_disp(I, A, B, c):
    #I is average grey level (0 to 255)
    #A is screen area (mm^2)
    #B is brightness (0 to 1)
    #c is parameter for average per area (fit)
    return I^(2.2)*A*B*c

def P_CPU(U, b, m):
    #U is average usage of cores
    #b and m are fitted intercept/baseline core power consumption and slope respectively
    return m*U+b

def P_base(cell, wifi, BT):
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
    






