import numpy as np
from decimal import *


def base_seir_model(init_vals, params, t):
    S_0, E_0, I_0, R_0 = init_vals
    S, E, I, R = [S_0], [E_0], [I_0], [R_0]
    alpha, beta, gamma = params
    dt = t[1] - t[0]
    for _ in t[1:]:
        next_S = S[-1] - (beta*S[-1]*I[-1])*dt
        next_E = E[-1] + (beta*S[-1]*I[-1] - alpha*E[-1])*dt
        next_I = I[-1] + (alpha*E[-1] - gamma*I[-1])*dt
        next_R = R[-1] + (gamma*I[-1])*dt
        S.append(next_S)
        E.append(next_E)
        I.append(next_I)
        R.append(next_R)
    return np.stack([S, E, I, R]).T


def seir_model_with_soc_dist(init_vals, params, t):
    S_0, E_0, I_0, R_0 = init_vals
    S, E, I, R = [S_0], [E_0], [I_0], [R_0]
    alpha, beta, gamma, rho = params
    dt = t[1] - t[0]
    for _ in t[1:]:
        next_S = S[-1] - (rho*beta*S[-1]*I[-1])*dt
        next_E = E[-1] + (rho*beta*S[-1]*I[-1] - alpha*E[-1])*dt
        next_I = I[-1] + (alpha*E[-1] - gamma*I[-1])*dt
        next_R = R[-1] + (gamma*I[-1])*dt
        S.append(next_S)
        E.append(next_E)
        I.append(next_I)
        R.append(next_R)
    return np.stack([S, E, I, R]).T



# Define parameters
t_max = 100
dt = 1
t = np.linspace(0, t_max, int(t_max/dt) + 1)
N = 10000
init_vals = 1 - 1/N, 1/N, 0, 0

alpha = 0.2   # inverse of incub period 1/t_incub
beta = 1.75   # average contact rate in pop
gamma = 0.5   # inverse of meen infectious period (1/t_infectious
rho = 0.5       # social distancing 1 0.5 0.8

r0 = beta/gamma
print ('R0: ' , r0)

params = alpha, beta, gamma , rho
# Run simulation
results = seir_model_with_soc_dist(init_vals, params, t)
#results = base_seir_model(init_vals, params, t)

#print(results)
for r in range(1,99,1):
    Susp = Decimal(results[r][0])*100
    Exp = Decimal(results[r][1])*100
    Inf = Decimal(results[r][2])*100
    Rec = Decimal(results[r][3])*100
    Tot = Susp + Exp + Inf + Rec
    #print (Susp*100)
    print( r , ' Susp: ' , "{:.{}f}".format( Susp, 2 )            , ' Exp: ' , "{:.{}f}".format( Exp, 2 )  , ' Inf: ' , "{:.{}f}".format( Inf, 2 )      , ' Rec: ' , "{:.{}f}".format( Rec, 2 )   , ' Tot: ' , "{:.{}f}".format( Tot, 2 ) )
    #print(r, '  Susp:  ',Decimal(results[r][0]) , '  Expos: ', Decimal(results[r][1])  , ' Inf:   ',Decimal(results[r][2]), '  Rec:  ',Decimal(results[r][3])                              )

print ("gedaan")
