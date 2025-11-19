# Get Dependencies
import numpy as np
import scipy.optimize
import pandas as pd
from openpyxl import load_workbook


def fun_flows(variables, *param):

    ( uvr, lvr, pvr, hr, C_d, C_s, C_sa, C_pv, C_pa) = param
    ( Q_v, Q_u, Q_l, Q_p, P_sa, P_pa, P_pv ) = variables
    eqn_a01 = Q_v - hr *( C_d * P_pv - C_s * P_sa)
    eqn_a02 = Q_u + Q_l - Q_v
    eqn_a03 = Q_p - Q_v
    eqn_a04 = pvr * Q_p - (P_pa - P_pv)
    eqn_a05 = uvr * Q_u - (P_sa - P_pa)
    eqn_a06 = lvr * Q_l - (P_sa - P_pa)
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

N_realizations = 100
MC_patient_std = 0.3
MC_med_std = 0.25
med_flag = 2 # 0 - baseline, 1 - vasopressin, 2 - phenylephrine

# finetuned values
C_s = 0.16040435
C_d = 2.26285145
C_sa = 0.01
C_pv = 0.06301968
C_pa = 0.01

# default inputs
UVR_mean = 45
LVR_mean = 35
PVR_mean = 10
HR_mean = 114

UVR_std = UVR_mean*0.2
LVR_std = LVR_mean*0.2
PVR_std = PVR_mean*0.4
HR_std = HR_mean*0.3


S_sa = 0.99
Hb = 15.0
CVO2u = 50
CVO2l = 40




# patient
# effect of the drug



if med_flag == 1:
    sheet_name = 'Vasopressin'
    print('Vasopressin is ON')
elif med_flag == 2:
    sheet_name = 'Phenylephrine'
    print('Phenylephrine is ON')
else:
    sheet_name = 'Baseline'
    print('Baseline')


SVR_base_mc = np.zeros(N_realizations)
PVR_base_mc = np.zeros(N_realizations)

SVR_mc = np.zeros(N_realizations)
PVR_mc = np.zeros(N_realizations)

Q_v_mc = np.zeros(N_realizations)
Q_u_mc = np.zeros(N_realizations)
Q_l_mc = np.zeros(N_realizations)

P_sa_mc = np.zeros(N_realizations)
P_pa_mc = np.zeros(N_realizations)
P_pv_mc = np.zeros(N_realizations)

S_pa_mc = np.zeros(N_realizations)
OER_mc = np.zeros(N_realizations)




# Gamma distribution parameters
# mean = shape * scale
# var = shape * scale^2

# std = sqrt(var)
# var = std^2

# scale = std^2 / mean
# shape = mean^2 / std^2

UVR_scale = UVR_std**2 / UVR_mean
UVR_shape = UVR_mean**2 / UVR_std**2

LVR_scale = LVR_std**2 / LVR_mean
LVR_shape = LVR_mean**2 / LVR_std**2

PVR_scale = PVR_std**2 / PVR_mean
PVR_shape = PVR_mean**2 / PVR_std**2

HR_scale = HR_std**2 / HR_mean
HR_shape = HR_mean**2 / HR_std**2

# Vasopressin parameters
eff_vaso_svr_mean = ( 1 + 0.287 )
eff_vaso_svr_std = eff_vaso_svr_mean * MC_med_std
eff_vaso_svr_scale = eff_vaso_svr_std**2 / eff_vaso_svr_mean
eff_vaso_svr_shape = eff_vaso_svr_mean**2 / eff_vaso_svr_std**2

eff_vaso_pvr_mean = ( 1 - 0.222 )
eff_vaso_pvr_std = eff_vaso_pvr_mean * MC_med_std
eff_vaso_pvr_scale = eff_vaso_pvr_std**2 / eff_vaso_pvr_mean
eff_vaso_pvr_shape = eff_vaso_pvr_mean**2 / eff_vaso_pvr_std**2

# Phenylephrine parameters
eff_phe_svr_mean = ( 1 + 0.287 )
eff_phe_svr_std = eff_phe_svr_mean * MC_med_std
eff_phe_svr_scale = eff_phe_svr_std**2 / eff_phe_svr_mean
eff_phe_svr_shape = eff_phe_svr_mean**2 / eff_phe_svr_std**2

eff_phe_pvr_mean = ( 1 + 0.287 )
eff_phe_pvr_std = eff_phe_pvr_mean * MC_med_std
eff_phe_pvr_scale = eff_phe_pvr_std**2 / eff_phe_pvr_mean
eff_phe_pvr_shape = eff_phe_pvr_mean**2 / eff_phe_pvr_std**2



for n in range(N_realizations):

    # Randomize patient
    uvr = np.random.gamma(UVR_shape, UVR_scale)
    lvr = np.random.gamma(LVR_shape, LVR_scale)
    pvr = np.random.gamma(PVR_shape, PVR_scale)
    hr = np.random.gamma(HR_shape, HR_scale)

    if med_flag == 1:
        random_eff_vaso_svr = np.random.gamma(eff_vaso_svr_shape, eff_vaso_svr_scale)
        random_eff_vaso_pvr = np.random.gamma(eff_vaso_pvr_shape, eff_vaso_pvr_scale)

        uvr_random = uvr * random_eff_vaso_svr
        lvr_random = lvr * random_eff_vaso_svr
        pvr_random = pvr * random_eff_vaso_pvr

        param_flows = ( uvr_random, \
                    lvr_random, \
                    pvr_random, \
                        hr, C_d, C_s, C_sa, C_pv, C_pa )
    elif med_flag == 2:
        random_eff_phe_svr = np.random.gamma(eff_phe_svr_shape, eff_phe_svr_scale)
        random_eff_phe_pvr = np.random.gamma(eff_phe_pvr_shape, eff_phe_pvr_scale)

        uvr_random = uvr * random_eff_phe_svr
        lvr_random = lvr * random_eff_phe_svr
        pvr_random = pvr * random_eff_phe_pvr

        param_flows = ( uvr_random, \
                    lvr_random, \
                    pvr_random, \
                        hr, C_d, C_s, C_sa, C_pv, C_pa )
    else:

        uvr_random = uvr
        lvr_random = lvr
        pvr_random = pvr
        param_flows = ( uvr_random, lvr_random, pvr_random, hr, C_d, C_s, C_sa, C_pv, C_pa)


    z0_flows = (3.1, 1.5, 1.5, 3.2, 75, 26, 2)

    result_flows = scipy.optimize.fsolve(fun_flows, z0_flows, args=param_flows, full_output=True, xtol=1e-4, maxfev=1000, factor=0.1) 
    ( Q_v, Q_u, Q_l, Q_p, P_sa, P_pa, P_pv) = result_flows[0]

    param_sat = ( Q_p, Q_u, Q_l, S_sa, CVO2u, CVO2l, Hb)
    z0_sat = (0.55, 0.99, 0.55, 0.55)

    result_O2_sat = scipy.optimize.fsolve(fun_sat, z0_sat, args=param_sat, full_output=True, xtol=1e-4, maxfev=1000, factor=0.1) 
    ( S_pa, S_pv, S_svu, S_svl ) = result_O2_sat[0]

    oer = (Q_u * (S_sa - S_svu) + Q_l * (S_sa - S_svl))/ ((Q_u + Q_l) * S_sa)

    SVR_base_mc[n] = (1/(1/uvr + 1/lvr)) * (17.1 / 19.6)
    PVR_base_mc[n] = pvr * (1.8 / 10.0)

    SVR_mc[n] = (1/(1/uvr_random + 1/lvr_random)) * (17.1 / 19.6)
    PVR_mc[n] = pvr_random * (1.8 / 10.0)

    Q_v_mc[n] = Q_v
    Q_u_mc[n] = Q_u
    Q_l_mc[n] = Q_l

    P_sa_mc[n] = P_sa
    P_pa_mc[n] = P_pa
    P_pv_mc[n] = P_pv

    S_pa_mc[n] = 100*S_pa
    OER_mc[n] = 100*oer





print('Monte Carlo Simulation Results with ', N_realizations, ' realizations:')

print('Mean SVR =', np.round(np.mean(SVR_mc), 2), '\t Std SVR =', np.round(np.std(SVR_mc), 2))
print('Mean PVR =', np.round(np.mean(PVR_mc), 2), '\t Std PVR =', np.round(np.std(PVR_mc), 2))

print('Mean Q_v =', np.round(np.mean(Q_v_mc), 2), '\t Std Q_v =', np.round(np.std(Q_v_mc), 2))
print('Mean Q_u =', np.round(np.mean(Q_u_mc), 2), '\t Std Q_u =', np.round(np.std(Q_u_mc), 2))
print('Mean Q_l =', np.round(np.mean(Q_l_mc), 2), '\t Std Q_l =', np.round(np.std(Q_l_mc), 2))

print('Mean P_sa =', np.round(np.mean(P_sa_mc), 1), '\t Std P_sa =', np.round(np.std(P_sa_mc), 1))
print('Mean P_pa =', np.round(np.mean(P_pa_mc), 1), '\t Std P_pa =', np.round(np.std(P_pa_mc), 1))
print('Mean P_pv =', np.round(np.mean(P_pv_mc), 1), '\t Std P_pv =', np.round(np.std(P_pv_mc), 1))

print('Mean S_pa =', np.round(np.mean(S_pa_mc), 1), '\t Std S_pa =', np.round(np.std(S_pa_mc), 1))
print('Mean OER =', np.round(np.mean(OER_mc), 1), '\t Std OER =', np.round(np.std(OER_mc), 1))


df_results = pd.DataFrame({
    'SVR_base': SVR_base_mc,
    'PVR_base': PVR_base_mc,
    'SVR': SVR_mc,
    'PVR': PVR_mc,
    'Q_v': Q_v_mc,
    'Q_u': Q_u_mc,
    'Q_l': Q_l_mc,
    'P_sa': P_sa_mc,
    'P_pa': P_pa_mc,
    'P_pv': P_pv_mc,
    'S_pa': S_pa_mc,
    'OER': OER_mc
})



df_MC_factors = pd.DataFrame({
    'MC_patient_std': [MC_patient_std],
    'MC_med_std': [MC_med_std]})

# from pd dataframe to excel
todays_date = pd.Timestamp.now().strftime('%Y-%m-%d')
output_file = f'monte_carlo_results_{todays_date}.xlsx'


with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df_results.to_excel(writer, sheet_name=sheet_name, index=False)
    df_MC_factors.to_excel(writer, sheet_name='MC_parameters', index=False)