import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def flow_pressure_solver_1(C_dia, C_sys, C_A, C_V, HR, R_p, R_s, V_total):
    """
    Solve for systemic and pulmonary flow and arterial/venous pressures 
    in the simplified Norwood circulation model.
    This function uses SV = (P_v)(C_dia)-(P_a)(C_sys)
    Q_s + Q_p = HR((P_v)(C_dia)-(P_a)(C_sys)) 

    Parameters
    ----------
    C_dia : float
        Diastolic compliance (C_dia). Must be > 0.
    C_sys : float
        Systolic compliance (C_sys). Must be > 0.
    C_A : float
        Arterial compliance (C_A). Must be > 0.
    C_V : float
        Venous compliance (C_V). Must be > 0.
    HR : float
        Heart rate (HR), beats per minute. Must be > 0.
    R_p : float
        Pulmonary resistance (R_p), resistance of the pulmonary circuit. Must be > 0.
    R_s : float
        Systemic resistance (R_s), resistance of the systemic circuit. Must be > 0.
    V_total : float
        Total blood volume (V_total), sum of arterial and venous volumes. Must be > 0.


    Returns
    -------
    Q_s : float
        Systemic flow (Q_s), blood flow through the systemic circuit.
    Q_p : float
        Pulmonary flow (Q_p), blood flow through the pulmonary circuit.
    P_a : float
        Arterial pressure (P_a).
    P_v : float
        Venous pressure (P_v).
    """

    #Throws a flag if inputs are not positive
    for name, value in {
        "C_dia": C_dia,
        "C_sys": C_sys,
        "C_A": C_A,
        "C_V": C_V,
        "HR": HR,
        "R_p": R_p,
        "R_s": R_s,
        "V_total": V_total,
    }.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive (got {value}).")


    A = np.array([[1, 1, HR*C_sys, -HR*C_dia],
        [0, R_p, -1, 1],
        [R_s, 0, -1, 1],
        [0, 0, C_A, C_V]], dtype=float)
    b = np.array([[0], 
         [0], 
         [0], 
         [V_total]], dtype=float)
    
    x = np.linalg.solve(A, b)
    Q_s = x[0][0]
    Q_p = x[1][0]
    P_a = x[2][0]
    P_v = x[3][0]
    #Q_s, Q_p, P_a, P_v = map(float, x)  


    #print(f"Q_s = {Q_s}")
    #print( f"Q_p = {Q_p}")
    #print(f"P_a = {P_a}")
    #print(f"P_v = {P_v}")

    return Q_s, Q_p, P_a, P_v

def flow_pressure_solver_2(C_dia, C_A, C_V, HR, R_p, R_s, V_total, EF):
    """
    Solve for systemic and pulmonary flow and arterial/venous pressures 
    in the simplified Norwood circulation model.
    This function uses SV = (EF)(P_v)(C_dia)
    Q_s + Q_p = (HR)(EF)(P_v)(C_dia) 


    Parameters
    ----------
    C_dia : float
        Diastolic compliance (C_dia). Must be > 0.
    C_A : float
        Arterial compliance (C_A). Must be > 0.
    C_V : float
        Venous compliance (C_V). Must be > 0.
    HR : float
        Heart rate (HR), beats per minute. Must be > 0.
    R_p : float
        Pulmonary resistance (R_p), resistance of the pulmonary circuit. Must be > 0.
    R_s : float
        Systemic resistance (R_s), resistance of the systemic circuit. Must be > 0.
    V_total : float
        Total blood volume (V_total), sum of arterial and venous volumes. Must be > 0.
    EF : float
        Ejectionn Fraction (V_total), percent of atrial volume ejected with each stroke. Must be between 0 and 1.


    Returns
    -------
    Q_s : float
        Systemic flow (Q_s), blood flow through the systemic circuit.
    Q_p : float
        Pulmonary flow (Q_p), blood flow through the pulmonary circuit.
    P_a : float
        Arterial pressure (P_a).
    P_v : float
        Venous pressure (P_v).
    """

    #Throws a flag if inputs are not positive
    for name, value in {
        "C_dia": C_dia,
        "C_A": C_A,
        "C_V": C_V,
        "HR": HR,
        "R_p": R_p,
        "R_s": R_s,
        "V_total": V_total,
        "EF": EF,
    }.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive (got {value}).")
    
    for name, value in {
        "EF": EF,
    }.items():
        if value >1:
            raise ValueError(f"{name} must be less than or equal to 1 (got {value}).")
        



    A = np.array([
        [1, 1, 0, -HR*EF*C_dia],
        [0, R_p, -1, 1],
        [R_s, 0, -1, 1],
        [0, 0, C_A, C_V]], dtype=float)
    b = np.array([[0], 
         [0], 
         [0], 
         [V_total]], dtype=float)
    
    x = np.linalg.solve(A, b)
    Q_s = x[0][0]
    Q_p = x[1][0]
    P_a = x[2][0]
    P_v = x[3][0]
    #Q_s, Q_p, P_a, P_v = map(float, x)  


    #print(f"Q_s = {Q_s}")
    #print( f"Q_p = {Q_p}")
    #print(f"P_a = {P_a}")
    #print(f"P_v = {P_v}")

    return Q_s, Q_p, P_a, P_v


def saturation_solver(Q_s, Q_p, Hb, CVO2, S_pv=0.99):
    """
    Solve for mixed and systemic venous oxygen saturations 
    given systemic and pulmonary flows.

    Parameters
    ----------
    Q_s : float
        Systemic flow (Q_s), blood flow through the systemic circuit. Must be > 0.
    Q_p : float
        Pulmonary flow (Q_p), blood flow through the pulmonary circuit. Must be > 0.
    Hb : float
        Hemoglobin concentration (Hb), affecting oxygen carrying capacity. Must be > 0.
    CVO2 : float
        Total oxygen consumption (CVO2). Must be > 0.
    S_pv : float, optional
        Pulmonary venous saturation (S_pv), oxygen saturation in blood 
        returning from the lungs. Default is 0.99 (99%). Must be > 0.

    Returns
    -------
    S_m : float
        Mixed oxygen saturation (S_m), representing 
        saturation after mixing of systemic venous and pulmonary 
        venous blood. Muliply the value by 100 to get it in percent form.
    S_sv : float
        Systemic venous saturation (S_sv), oxygen saturation 
        in blood returning from the systemic circuit. Muliply the value by 
        100 to get it in percent form.
    D20 : float
        Oxygen delivery, represetning the amount of O2 delivered to systemic tissue per minute
    OER: float
        Oxygen Extraction Ratio. 
    """
    

    #Throws a flag if inputs are not positive
    for name, value in {
        "Q_s": Q_s,
        "Q_p": Q_p,
        "Hb": Hb,
        "CVO2": CVO2,
        "S_pv": S_pv,
    }.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive (got {value}).")


    A = np.array([[(Q_s+Q_p), -Q_s],
         [1.34*Hb*Q_s, -1.34*Hb*Q_s]], dtype=float)
    b = np.array([[Q_p*S_pv],
         [CVO2]], dtype=float)

    x = np.linalg.solve(A, b)
    S_m = x[0][0]
    S_sv = x[1][0]

    #print(f"S_m = {S_m}")
    #print(f"S_sv = {S_sv}")

    D20 = 1.34 * Hb * S_m * Q_s
    return S_m, S_sv, D20

