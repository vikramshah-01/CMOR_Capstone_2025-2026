import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def arterial_and_venous_compliance_solver(P_a, P_v, V_total = 0):
    """
    Uses P_a*C_A - P_v*C_V = V_total and C_V~=7C_A to solve for C_A and C_V. 
    V_total can also be solved for if  V_total = 0 is specified. If V_total is solved for then the ratios C_A/V_total and C_V/V_total are solved for


    Solve for the ratios of aterial compliance to blood volume and venous compliance to blood volume from pressures and heart rate using a linear model.
    Parameters
    ----------
    P_a : array_like, shape (n,) or (n, 1)
        Arterial pressure samples (mmHg). 
        Must be > 0 elementwise.
    P_v : array_like, shape (n,) or (n, 1)
        Venous pressure samples (mmHg).
        Must be > 0 elementwise. 
    V_total : 
        Total blood volume (L). If V_total = 0 then total blood volume is solved for and the reults of the function
        are the estimated ratio of arterial compliance to total blood volume and estimated ratio of venous compliance to total blood volume.
        If V_total is an "array_like, shape (n,) or (n, 1)" then the function uses the V_total vector to solve for the estimated values of 
        arterial compliance and venous compliance

    Returns
    -------
    C_A_hat : float
        Estimated ratio of arterial compliance (C_A, L/mmHg) to total blood volume (V_total, L). In units of 1/mmHg.
    C_V_hat : float
        Estimated ratio venous compliance (C_V, L/mmHg) to total blood volume (V_total, mL). In units of 1/mmHg.
    """
    if V_total == 0:
        V_t = np.ones(np.shape(P_a))
    else:
        V_t = V_total 
    
    
    A = P_a + 7*P_v

    x, residuals, rank, s= sp.linalg.lstsq(A, V_t)

    C_A_hat = x[0][0]
    C_V_hat = 7*C_A_hat



    return C_A_hat, C_V_hat
