# Get Dependencies
import numpy as np
import scipy.optimize

# # default compliance values
# C_d = 2/100       # 30C_s
# C_s = .01/100       # from TGA
# C_sa = 1/135
# C_pv = 30 * C_sa
# C_pa = 2 * C_sa

# finetuned values
C_s = 0.16040435
C_d = 2.26285145
C_sa = 0.01
C_pv = 0.06301968
C_pa = 0.01

# # default inputs

UVR = 45
LVR = 35
PVR = 10
HR = 114

S_sa = 0.99 # give narrow interval: .98 - 1 assuming lungs are healthy
Hb = 15.0
CVO2u = 50
CVO2l = 40

def fun_flows(variables, *param):

    ( UVR, LVR, PVR, HR, C_d, C_s, C_sa, C_pv, C_pa) = param
    ( Q_v, Q_u, Q_l, Q_p, P_sa, P_pa, P_pv ) = variables
    eqn_a01 = Q_v - HR *( C_d * P_pv - C_s * P_sa)
    eqn_a02 = Q_u + Q_l - Q_v
    eqn_a03 = Q_p - Q_v
    eqn_a04 = PVR * Q_p - (P_pa - P_pv)
    eqn_a05 = UVR * Q_u - (P_sa - P_pa)
    eqn_a06 = LVR * Q_l - (P_sa - P_pa)
    eqn_a07 = 1 - (C_sa * P_sa + C_pv * P_pv + C_pa * P_pa)     # remember these compliances are divided by volume  
                                                                # preload (dehydration, bleeding) - low volume increases all compliances
                                                                # cardiac failure (everything is high) - poor contractility, change C_d and C_s
                                                                # high PVR (pulmonary hypertension, secondary infection, etc)
    return [eqn_a01, eqn_a02, eqn_a03, eqn_a04, eqn_a05, eqn_a06, eqn_a07]

def fun_sat(variables, *param):
    
    ( Q_p, Q_u, Q_l, S_sa, CVO2u, CVO2l, Hb) = param
    ( S_pa, S_pv, S_svu, S_svl ) = variables
    
    # O2 consumption = CVO2 (c=consumption, Vo2 = volume of oxygen)
    # volume of oxygen/min going into organs x = 1.34 * hemoglobin * Q_x * S_sa
    # volume of oxygen/min leaving organs x = 1.34 * hemoglobin * Q_x * S_sv
    # hemoglobin can be controlled by physicians, O2 consumption depends on activity
    # S = oxygen saturation in blood (fractions)
    # 100 and 1000 are unit transformations

    eqn_s1 = CVO2u - 1.34 * Hb / 100 * Q_u * 1000 * (S_sa - S_svu)
    eqn_s2 = CVO2l - 1.34 * Hb / 100 * Q_l * 1000 *(S_sa - S_svl)
    eqn_s3 = Q_p * S_pa - (Q_u * S_svu + Q_l * S_svl)
    eqn_s4 = S_sa - S_pv
    
    return [eqn_s1, eqn_s2, eqn_s3, eqn_s4]

if __name__ == "__main__":

    med_flag = 0 # 0 - baseline, 1 - vasopressin, 2 - phenylephrine
    # The haemodynamic effects of phenylephrine after cardiac surgery

    if med_flag == 1:
        print('Vasopressin is ON')
        param_flows = (( 1 + 0.28 )*UVR, \
                    ( 1 + 0.28 )*LVR, \
                    ( 1 - 0.222 )*PVR, \
                        HR, C_d, C_s, C_sa, C_pv, C_pa)
    elif med_flag == 2:
        print('Phenylephrine is ON')
        param_flows = ( ( 1 + 0.287 )*UVR, \
                    ( 1 + 0.287 )*LVR, \
                    ( 1 + 0.287 )*PVR, \
                        HR, C_d, C_s, C_sa, C_pv, C_pa)
    else:
        print('Baseline')
        param_flows = ( UVR, LVR, PVR, HR, C_d, C_s, C_sa, C_pv, C_pa)


    z0_flows = (3.1, 1.5, 1.5, 3.2, 75, 26, 2)

    result_flows = scipy.optimize.fsolve(fun_flows, z0_flows, args=param_flows, full_output=True, xtol=1e-4, maxfev=1000, factor=0.1) 
    ( Q_v, Q_u, Q_l, Q_p, P_sa, P_pa, P_pv) = result_flows[0]

    param_sat = ( Q_p, Q_u, Q_l, S_sa, CVO2u, CVO2l, Hb)
    z0_sat = (0.55, 0.99, 0.55, 0.55)

    result_O2_sat = scipy.optimize.fsolve(fun_sat, z0_sat, args=param_sat, full_output=True, xtol=1e-4, maxfev=1000, factor=0.1) 
    ( S_pa, S_pv, S_svu, S_svl ) = result_O2_sat[0]

    OER = (Q_u * (S_sa - S_svu) + Q_l * (S_sa - S_svl))/ ((Q_u + Q_l) * S_sa)

    TPG_base = 17.086
    TPG_vasopressin = P_pa-P_pv
    TPG_change = (TPG_vasopressin - TPG_base)/TPG_base*100

    # Flows for Fontan
    print('Q_v =', np.round(Q_v,2))
    print('Q_u =', np.round(Q_u, 2))
    print('Q_l =', np.round(Q_l,2))
    print('Q_p =', np.round(Q_p,2))
    print('P_sa =', np.round(P_sa,2))
    print('P_pv =', np.round(P_pv,2))
    print('P_pa =', np.round(P_pa,2))
    print('TPG =', np.round(P_pa-P_pv,3))
    print('TPG change =', np.round(TPG_change,2), '%')
    print('OER = ', np.round(OER,3))
    print('Flows Solution flag:', result_flows[2])
    print('Flows Solution msg:', result_flows[3])

    # Oxygen
    print('S_pa =', np.round(S_pa,2))
    print('S_pv =', np.round(S_pv,2))
    print('S_svu =', np.round(S_svu,2))
    print('S_svl =', np.round(S_svl,2))
    print('Flows Solution flag:', result_O2_sat[2])
    print('Flows Solution msg:', result_O2_sat[3])

