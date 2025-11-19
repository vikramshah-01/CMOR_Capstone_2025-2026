import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def systolic_and_diastolic_compliance_solver(P_v, HR, EF, Q_s, Q_p):
    """
    Solve for diastolic compliances from pressures, heart rate, ejection fraction
    and systemic & pulmonary flows.

    Uses Q_s + Q_p = HR*EF*P_v*C_dia to solve for C_dia



    Parameters
    ----------

    P_v : array_like, shape (n,) or (n, 1)
        Venous pressure samples (mmHg).
        Must be > 0 elementwise.
    HR : array_like, shape (n,) or (n, 1)
        Heart rate (beats per minute) samples.
        Must be > 0 elementwise.
    EF : array_like, shape (n,) or (n, 1)
        Ejection fraction as a decimel 
        Must be > 0 and <=1 elementwise
    Q_s : array_like, shape (n,) or (n, 1)
        Systemic flow (L/min).
        Must be > 0 elementwise.
    Q_p : array_like, shape (n,) or (n, 1)
        Pulmonary flow (L/min).
        Must be > 0 elementwise.


    Returns
    -------
    C_sys : float
        Estimated systolic compliance (C_sys). In units of mmHg.
    C_dia : float
        Estimated diastolic compliance (C_dia). In units of mmHg.
    """




    A = HR*EF*P_v
    b = (Q_s + Q_p)

    x, residuals, rank, s= sp.linalg.lstsq(A, b)
    print(x)
    C_dia = x[0][0]

    return C_dia

