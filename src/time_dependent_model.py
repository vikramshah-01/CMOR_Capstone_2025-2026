import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def time_dependent_norwood(R_s, R_p, R_BTS, C_s, C_p, P_sa_0, P_pa_0, Q_Ao, t_end, dt):
    """
    Simulate the time-dependent Norwood circulation model using a backward
    Euler discretization of the pressure ODEs and algebraic flow-pressure
    relationships.

    This function solves the following system at each time t:

        (1) R_S Q_SA = P_SA - P_SV
        (2) R_P Q_PA = P_PA - P_PV
        (3) R_BTS Q_PA = P_SA - P_PA
        (4) 0 = P_PV - P_SV
        (5) Q_PA + Q_SA = Q_AO(t)
        (6) Q_PV + Q_SV = Q_AO(t)
        (7) C_S dP_SA/dt = Q_SA - Q_SV
        (8) C_P dP_PA/dt = Q_PA - Q_PV

    with finite-difference approximation

        dP/dt ≈ (P(t_n) - P(t_{n-1})) / dt.

    All parameters must be strictly greater than zero.

    Parameters
    ----------
    R_s : float, >0
        Systemic vascular resistance R_S  [Wood units = mmHg·min/L].
    R_p : float, >0
        Pulmonary vascular resistance R_P  [Wood units = mmHg·min/L].
    R_BTS : float, >0
        BTS shunt resistance R_BTS  [Wood units = mmHg·min/L].
    C_s : float, >0
        Systemic arterial compliance C_S  [L/mmHg].
    C_p : float, >0
        Pulmonary arterial compliance C_P  [L/mmHg].

    P_sa_0 : float, >0
        Initial systemic arterial pressure P_SA(0)  [mmHg].
    P_pa_0 : float, >0
        Initial pulmonary arterial pressure P_PA(0)  [mmHg].

    Q_Ao : callable t --> L/min
        Function returning aortic outflow Q_AO(t)  [L/min].
        Must accept a single argument t (minutes).

    t_end : float, >0
        End time of the simulation  [min].
    dt : float, >0
        Time step for discretization  [min].

    Returns
    -------
    t_vec : ndarray
        Time values  [min].
    Q_sa : ndarray
        Systemic arterial flow Q_SA(t)  [L/min].
    Q_sv : ndarray
        Systemic venous flow Q_SV(t)  [L/min].
    Q_pa : ndarray
        Pulmonary arterial flow Q_PA(t)  [L/min].
    Q_pv : ndarray
        Pulmonary venous flow Q_PV(t)  [L/min].
    P_sa : ndarray
        Systemic arterial pressure P_SA(t)  [mmHg].
    P_sv : ndarray
        Systemic venous pressure P_SV(t)  [mmHg].
    P_pa : ndarray
        Pulmonary arterial pressure P_PA(t)  [mmHg].
    P_pv : ndarray
        Pulmonary venous pressure P_PV(t)  [mmHg].

    Notes
    -----
    Wood units are defined as mmHg·min/L.
    Compliance units mL/mmHg are equivalent to L/mmHg up to a constant factor.
    The linear system is solved using scipy.linalg.lstsq to accommodate
    potential singularity from algebraic constraints.
    """
    if R_s <= 0:
        raise ValueError(f"R_s must be > 0 (Wood units), got {R_s}")
    if R_p <= 0:
        raise ValueError(f"R_p must be > 0 (Wood units), got {R_p}")
    if R_BTS <= 0:
        raise ValueError(f"R_BTS must be > 0 (Wood units), got {R_BTS}")

    if C_s <= 0:
        raise ValueError(f"C_s must be > 0, got {C_s}")
    if C_p <= 0:
        raise ValueError(f"C_p must be > 0, got {C_p}")

    if P_sa_0 < 0:
        raise ValueError(f"P_sa_0 must be >= 0 mmHg, got {P_sa_0}")
    if P_pa_0 < 0:
        raise ValueError(f"P_pa_0 must be >= 0 mmHg, got {P_pa_0}")

    # Time parameters
    if t_end <= 0:
        raise ValueError(f"t_end must be > 0 seconds, got {t_end}")
    if dt <= 0:
        raise ValueError(f"dt must be > 0 seconds, got {dt}")

    # Q_Ao must be a callable waveform
    if not callable(Q_Ao):
        raise TypeError("Q_Ao must be a callable function Q_Ao(t).")
    

    if dt>t_end:
        raise print(f'dt > t_end ({dt} > {t_end})\n')
    


    t_vec = np.arange(0, t_end, dt)
    Q_sa = np.full(len(t_vec), np.nan)
    Q_sv = np.full(len(t_vec), np.nan)
    Q_pa = np.full(len(t_vec), np.nan)
    Q_pv = np.full(len(t_vec), np.nan)
    P_sa = np.full(len(t_vec), np.nan)
    P_sv = np.full(len(t_vec), np.nan)
    P_pa = np.full(len(t_vec), np.nan)
    P_pv = np.full(len(t_vec), np.nan)

    for i in range(len(t_vec)):
        Q_v = Q_Ao(t_vec[i])
        A = np.array([[R_s, 0, 0, 0, -1, 1, 0, 0],
                        [0, 0, R_p, 0, 0, 0, -1, 1],
                        [0, 0, R_BTS, 0, -1, 0, 1, 0],
                        [0, 0, 0, 0, 0, -1, 0, 1],
                        [1, 0, 1, 0, 0, 0, 0, 0],
                        [0, 1, 0, 1, 0, 0, 0, 0],
                        [-dt, dt, 0, 0, C_s, 0, 0, 0],
                        [0, 0, -dt, dt, 0, 0, C_p, 0]])
        if i==0:        
            b = np.array([[0],
                        [0],
                        [0],
                        [0],
                        [Q_v],
                        [Q_v],
                        [P_sa_0*C_s],
                        [P_pa_0*C_p]])
        else:
            b = np.array([[0],
                        [0],
                        [0],
                        [0],
                        [Q_v],
                        [Q_v],
                        [P_sa[i-1]*C_s],
                        [P_pa[i-1]*C_p]])
        
        x, residuals, rank, s= sp.linalg.lstsq(A, b)
        Q_sa[i] = x[0, 0]
        Q_sv[i] = x[1, 0]
        Q_pa[i] = x[2, 0]
        Q_pv[i] = x[3, 0]
        P_sa[i] = x[4, 0]
        P_sv[i] = x[5, 0]
        P_pa[i] = x[6, 0]
        P_pv[i] = x[7, 0]



    return t_vec, Q_sa, Q_sv, Q_pa, Q_pv, P_sa, P_sv, P_pa, P_pv

def time_dependent_norwood_valve(R_s, R_p, R_BTS, C_s, C_p, P_sa_0, P_pa_0, Q_Ao, t_end, dt):
    """
    Simulate the time-dependent Norwood circulation model using a backward
    Euler discretization of the pressure ODEs and algebraic flow-pressure
    relationships.

    This function solves the following system at each time t:

        (1) R_S Q_SA = P_SA - P_SV
        (2) R_P Q_PA = P_PA - P_PV
        (3) R_BTS Q_PA = P_SA - P_PA
        (4) 0 = P_PV - P_SV
        (5) Q_PA + Q_SA = Q_AO(t)
        (6) Q_PV + Q_SV = Q_AO(t)
        (7) C_S dP_SA/dt = Q_SA - Q_SV
        (8) C_P dP_PA/dt = Q_PA - Q_PV

    with finite-difference approximation

        dP/dt ≈ (P(t_n) - P(t_{n-1})) / dt.

    All parameters must be strictly greater than zero.

    Parameters
    ----------
    R_s : float, >0
        Systemic vascular resistance R_S  [Wood units = mmHg·min/L].
    R_p : float, >0
        Pulmonary vascular resistance R_P  [Wood units = mmHg·min/L].
    R_BTS : float, >0
        BTS shunt resistance R_BTS  [Wood units = mmHg·min/L].
    C_s : float, >0
        Systemic arterial compliance C_S  [L/mmHg].
    C_p : float, >0
        Pulmonary arterial compliance C_P  [L/mmHg].

    P_sa_0 : float, >0
        Initial systemic arterial pressure P_SA(0)  [mmHg].
    P_pa_0 : float, >0
        Initial pulmonary arterial pressure P_PA(0)  [mmHg].

    Q_Ao : callable t --> L/min
        Function returning aortic outflow Q_AO(t)  [L/min].
        Must accept a single argument t (minutes).

    t_end : float, >0
        End time of the simulation  [min].
    dt : float, >0
        Time step for discretization  [min].

    Returns
    -------
    t_vec : ndarray
        Time values  [min].
    Q_sa : ndarray
        Systemic arterial flow Q_SA(t)  [L/min].
    Q_sv : ndarray
        Systemic venous flow Q_SV(t)  [L/min].
    Q_pa : ndarray
        Pulmonary arterial flow Q_PA(t)  [L/min].
    Q_pv : ndarray
        Pulmonary venous flow Q_PV(t)  [L/min].
    P_sa : ndarray
        Systemic arterial pressure P_SA(t)  [mmHg].
    P_sv : ndarray
        Systemic venous pressure P_SV(t)  [mmHg].
    P_pa : ndarray
        Pulmonary arterial pressure P_PA(t)  [mmHg].
    P_pv : ndarray
        Pulmonary venous pressure P_PV(t)  [mmHg].

    Notes
    -----
    Wood units are defined as mmHg·min/L.
    Compliance units mL/mmHg are equivalent to L/mmHg up to a constant factor.
    The linear system is solved using scipy.linalg.lstsq to accommodate
    potential singularity from algebraic constraints.
    """
    if R_s <= 0:
        raise ValueError(f"R_s must be > 0 (Wood units), got {R_s}")
    if R_p <= 0:
        raise ValueError(f"R_p must be > 0 (Wood units), got {R_p}")
    if R_BTS <= 0:
        raise ValueError(f"R_BTS must be > 0 (Wood units), got {R_BTS}")

    if C_s <= 0:
        raise ValueError(f"C_s must be > 0, got {C_s}")
    if C_p <= 0:
        raise ValueError(f"C_p must be > 0, got {C_p}")

    if P_sa_0 < 0:
        raise ValueError(f"P_sa_0 must be >= 0 mmHg, got {P_sa_0}")
    if P_pa_0 < 0:
        raise ValueError(f"P_pa_0 must be >= 0 mmHg, got {P_pa_0}")

    # Time parameters
    if t_end <= 0:
        raise ValueError(f"t_end must be > 0 seconds, got {t_end}")
    if dt <= 0:
        raise ValueError(f"dt must be > 0 seconds, got {dt}")

    # Q_Ao must be a callable waveform
    if not callable(Q_Ao):
        raise TypeError("Q_Ao must be a callable function Q_Ao(t).")
    

    if dt>t_end:
        raise print(f'dt > t_end ({dt} > {t_end})\n')
    


    t_vec = np.arange(0, t_end, dt)
    Q_sa = np.full(len(t_vec), np.nan)
    Q_sv = np.full(len(t_vec), np.nan)
    Q_pa = np.full(len(t_vec), np.nan)
    Q_pv = np.full(len(t_vec), np.nan)
    P_sa = np.full(len(t_vec), np.nan)
    P_sv = np.full(len(t_vec), np.nan)
    P_pa = np.full(len(t_vec), np.nan)
    P_pv = np.full(len(t_vec), np.nan)

    for i in range(len(t_vec)):
        Q_v = Q_Ao(t_vec[i])
        A = np.array([[R_s, 0, 0, 0, -1, 1, 0, 0],
                        [0, 0, R_p, 0, 0, 0, -1, 1],
                        [0, 0, R_BTS, 0, -1, 0, 1, 0],
                        [0, 0, 0, 0, 0, -1, 0, 1],
                        [1, 0, 1, 0, 0, 0, 0, 0],
                        [0, 1, 0, 1, 0, 0, 0, 0],
                        [-dt, dt, 0, 0, C_s, 0, 0, 0],
                        [0, 0, -dt, dt, 0, 0, C_p, 0]])
        if i==0:        
            b = np.array([[0],
                        [0],
                        [0],
                        [0],
                        [Q_v],
                        [Q_v],
                        [P_sa_0*C_s],
                        [P_pa_0*C_p]])
        else:
            b = np.array([[0],
                        [0],
                        [0],
                        [0],
                        [Q_v],
                        [Q_v],
                        [P_sa[i-1]*C_s],
                        [P_pa[i-1]*C_p]])
        
        x, residuals, rank, s= sp.linalg.lstsq(A, b)
        

        if x[0, 0] < 0:
            x[0, 0] = 0
        if x[1, 0] < 0:
            x[1, 0] = 0
        if x[2, 0] < 0:
            x[2, 0] = 0
        if x[3, 0] < 0:
            x[3, 0] = 0
        if x[4, 0] < 0:
            x[4, 0] = 0
        if x[5, 0] < 0:
            x[5, 0] = 0
        if x[6, 0] < 0:
            x[6, 0] = 0
        if x[7, 0] < 0:
            x[7, 0] = 0
        
        Q_sa[i] = x[0, 0]
        Q_sv[i] = x[1, 0]
        Q_pa[i] = x[2, 0]
        Q_pv[i] = x[3, 0]
        P_sa[i] = x[4, 0]
        P_sv[i] = x[5, 0]
        P_pa[i] = x[6, 0]
        P_pv[i] = x[7, 0]



    return t_vec, Q_sa, Q_sv, Q_pa, Q_pv, P_sa, P_sv, P_pa, P_pv


def Q_Ao(t):
    T     = 0.0125
    T_max = 0.0050
    T_s   = 0.0080
    Q_max = 5.0

    t_new = t % T
    if 0.0 <= t_new <= T_max:
        return Q_max * t_new / T_max
    elif T_max <= t_new <= T_s:
        return Q_max * (T_s - t_new) / (T_s - T_max)
    elif T_s <= t_new <= T:
        return 0.0
    else:
        return 0.0

import math

def Q_Ao_2(t):
    """
    Physiologically smoother neo-aortic valve flow waveform.

    Parameters
    ----------
    t : float
        Time in minutes.
    Returns
    -------
    float
        Instantaneous aortic valve flow in L/min.
    """


    hr_bpm=140              # neonatal / young infant Norwood-ish default
    weight_kg=3.5
    co_ml_per_kg_min=250.0  # target mean cardiac output
    ejection_fraction=0.5  # fraction of cycle spent ejecting
    alpha=2.2               # controls upstroke
    beta=3.8                 # controls downslope; peak occurs early


    # Cardiac cycle length in minutes
    T = 1.0 / hr_bpm
    tau = (t % T) / T  # normalized cycle time in [0,1)

    # Target cycle-mean cardiac output [L/min]
    CO_target = weight_kg * co_ml_per_kg_min / 1000.0

    # No valve flow during diastole
    if tau >= ejection_fraction:
        return 0.0

    # Normalize systole to x in [0,1]
    x = tau / ejection_fraction

    # Smooth early-peaking ejection pulse
    raw = (x ** (alpha - 1.0)) * ((1.0 - x) ** (beta - 1.0))

    # Normalize by peak so shape max = 1
    x_peak = (alpha - 1.0) / (alpha + beta - 2.0)
    raw_peak = (x_peak ** (alpha - 1.0)) * ((1.0 - x_peak) ** (beta - 1.0))
    shape = raw / raw_peak

    # Area under normalized shape on x in [0,1]
    beta_fn = math.gamma(alpha) * math.gamma(beta) / math.gamma(alpha + beta)
    shape_area = beta_fn / raw_peak

    # Choose amplitude so mean over the full cardiac cycle = CO_target
    amplitude = CO_target / (ejection_fraction * shape_area)

    return amplitude * shape