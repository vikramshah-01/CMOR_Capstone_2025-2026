import numpy as np


def time_dependent_norwood(t0, tf, dt, x0, V_a0, V_v0, K_a, K_v, gamma_int, gamma_ext, L_int, L_ext, B_int, B_ext, R_int, R_ext, R_s, R_p, R_BTS, C_SA, C_PA, C_SV, C_PV, V_total, HR,
                           E_min_a, E_max_a, t_onset_a, m_1a, tau_1a, m_2a, tau_2a, E_min_v, E_max_v, t_onset_v, m_1v, tau_1v, m_2v, tau_2v):
    '''
    Inputs:
        t0: float, >0
            Initial timepoint for evaluation (in minutes). x0 is the vector value of the variables at t0,
        tf: float, >0
            final timepoint (in minutes)
        dt: float, >0
            time step
        x0: 14x, or 14x1 array
            Initial value at t=t0 vector for all variables in the order: p_a, p_v, Q_int, Q_ext, V_a, V_v, Q_SA, Q_SV, Q_PA, Q_PV, P_SA, P_SV, P_PA, P_PV
            Really only and p_a, p_v, Q_int, Q_ext, V_a, V_v, Q_SV, Q_PV, and P_SA are need so the others can be set to zero. 
        params: 
    '''

    def H_fun(delta_p, gamma):
        return 1/(1+np.exp(-gamma*(delta_p)))
    
    def Ea_fun(t, HR, E_min, E_max, t_onset, m_1a, tau_1a, m_2a, tau_2a):

        def g(t, t_onset, m_i, tau_i):
            # FIX (Bug 4): clamp to avoid negative base raised to fractional
            # exponent, which produces NaN/complex in NumPy.
            return (np.maximum(t - t_onset, 0.0) / tau_i) ** m_i

        T = 1 / HR
        t_vec = np.arange(0, T, 0.00001)
        k = np.max((g(t_vec, t_onset, m_1a, tau_1a) / (1 + g(t_vec, t_onset, m_1a, tau_1a))) * (1 / (1 + g(t_vec, t_onset, m_2a, tau_2a))))

        E = ((E_max - E_min) / k) * (g(t, t_onset, m_1a, tau_1a) / (1 + g(t, t_onset, m_1a, tau_1a))) * (1 / (1 + g(t, t_onset, m_2a, tau_2a))) + E_min

        return E

    def Ev_fun(t, HR, E_min, E_max, t_onset, m_1v, tau_1v, m_2v, tau_2v):

        def g(t, t_onset, m_i, tau_i):
            # FIX (Bug 4): same clamp as Ea_fun.
            return (np.maximum(t - t_onset, 0.0) / tau_i) ** m_i

        T = 1 / HR
        t_vec = np.arange(0, T, 0.00001)
        k = np.max((g(t_vec, t_onset, m_1v, tau_1v) / (1 + g(t_vec, t_onset, m_1v, tau_1v))) * (1 / (1 + g(t_vec, t_onset, m_2v, tau_2v))))

        E = ((E_max - E_min) / k) * (g(t, t_onset, m_1v, tau_1v) / (1 + g(t, t_onset, m_1v, tau_1v))) * (1 / (1 + g(t, t_onset, m_2v, tau_2v))) + E_min

        return E


    # T[0] is the timepoint for x0
    t_vec = np.arange(t0, tf + dt, dt)

    x0 = x0.reshape(14)

    # FIX (Bug 1 & 2): allocate x_store ONCE for the full time series and never
    # overwrite it with a reshape.  Previously x_store was replaced by a (14,1)
    # stub after the first solve and then reshaped back to (14,1) on every loop
    # iteration, destroying all previously stored columns.
    x_store = np.full(shape=(14, len(t_vec)), fill_value=np.nan)
    x_store[:, 0] = x0

    # --- first step (t_vec[0] -> t_vec[1]) ---
    t = t_vec[1]
    E_a = Ea_fun(t, HR, E_min_a, E_max_a, t_onset_a, m_1a, tau_1a, m_2a, tau_2a)
    E_v = Ev_fun(t, HR, E_min_v, E_max_v, t_onset_v, m_1v, tau_1v, m_2v, tau_2v)

    A = [[1, 0, 0, 0, -(E_a/V_a0)-(K_a*x0[0]/dt), 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 1, 0, 0, 0, -(E_v/V_v0)-(K_v*x0[1]/dt), 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, (L_int/dt)+B_int*np.abs(x0[2])+R_int, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, (L_ext/dt)+B_ext*np.abs(x0[3])+R_ext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 1/2, 0, 1/dt, 0, 0, -1/2, 0, -1/2, 0, 0, 0, 0],
         [0, 0, -1/2, 1/2, 0, 1/dt, 0, 0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, R_s, 0, 0, 0, -1, 1, 0, 0],
         # FIX (Bug 5): was [.. R_p, 0, -1, 0, 1, 0] — used P_SA (col 10) as
         # the driving pressure for Q_PA, making rows 7 and 8 identical and
         # the matrix singular.  Q_PA is driven by P_PA - P_PV (cols 12, 13).
         [0, 0, 0, 0, 0, 0, 0, 0, R_p, 0, 0, 0, -1, 1],
         [0, 0, 0, 0, 0, 0, 0, 0, R_BTS, 0, -1, 0, 1, 0],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 1],
         [0, 0, 0, -1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, -1, 1, 0, 0, C_SA/dt, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, 0, 0, -1, 1, 0, 0, C_PA/dt, 0],
         [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, C_SA, C_SV, C_PA, C_PV]]

    b = [[-E_a-(K_a*x0[0]*x0[4]/dt)],
         [-E_v-(K_v*x0[1]*x0[5]/dt)],
         [(L_int*x0[2]/dt)+H_fun(x0[0]-x0[1], gamma_int)*(x0[0]-x0[1])],
         [(L_ext*x0[3]/dt)+H_fun(x0[1]-x0[10], gamma_ext)*(x0[1]-x0[10])],
         [(x0[4]/dt)-1/2*(x0[2]-x0[9]-x0[7])],
         [(x0[5]/dt)-1/2*(x0[3]-x0[2])],
         [0], [0], [0], [0], [0],
         [C_SA*x0[10]/dt],
         [C_PA*x0[12]/dt],
         [V_total]]

    # FIX (Bug 3 & 6): np.linalg.solve returns (14,1) when b is a list-of-lists.
    # Flatten to (14,) before storing, and store into column 1 directly.
    x = np.linalg.solve(A, b).flatten()
    x_store[:, 1] = x

    # --- subsequent steps ---
    for i, t in enumerate(t_vec[2:], start=2):
        E_a = Ea_fun(t, HR, E_min_a, E_max_a, t_onset_a, m_1a, tau_1a, m_2a, tau_2a)
        E_v = Ev_fun(t, HR, E_min_v, E_max_v, t_onset_v, m_1v, tau_1v, m_2v, tau_2v)

        A = [[1, 0, 0, 0, -(E_a/V_a0)-(K_a*x[0]/dt), 0, 0, 0, 0, 0, 0, 0, 0, 0],
             [0, 1, 0, 0, 0, -(E_v/V_v0)-(K_v*x[1]/dt), 0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, (L_int/dt)+B_int*np.abs(x[2])+R_int, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, (L_ext/dt)+B_ext*np.abs(x[3])+R_ext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 1/2, 0, 1/dt, 0, 0, -1/2, 0, -1/2, 0, 0, 0, 0],
             [0, 0, -1/2, 1/2, 0, 1/dt, 0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, R_s, 0, 0, 0, -1, 1, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, R_p, 0, 0, 0, -1, 1],
             [0, 0, 0, 0, 0, 0, 0, 0, R_BTS, 0, -1, 0, 1, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 1],
             [0, 0, 0, -1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, -1, 1, 0, 0, C_SA/dt, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, -1, 1, 0, 0, C_PA/dt, 0],
             [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, C_SA, C_SV, C_PA, C_PV]]

        b = [[-E_a-(K_a*x[0]*x[4]/dt)],
             [-E_v-(K_v*x[1]*x[5]/dt)],
             [(L_int*x[2]/dt)+H_fun(x[0]-x[1], gamma_int)*(x[0]-x[1])],
             [(L_ext*x[3]/dt)+H_fun(x[1]-x[10], gamma_ext)*(x[1]-x[10])],
             [(x[4]/dt)-1/2*(x[2]-x[9]-x[7])],
             [(x[5]/dt)-1/2*(x[3]-x[2])],
             [0], [0], [0], [0], [0],
             [C_SA*x[10]/dt],
             [C_PA*x[12]/dt],
             [V_total]]

        # FIX (Bug 3): flatten so x is always (14,) for the next iteration's A/b
        x = np.linalg.solve(A, b).flatten()
        x_store[:, i] = x

    p_a  = x_store[0, :]
    p_v  = x_store[1, :]
    Q_int = x_store[2, :]
    Q_ext = x_store[3, :]
    V_a  = x_store[4, :]
    V_v  = x_store[5, :]
    Q_SA = x_store[6, :]
    Q_SV = x_store[7, :]
    Q_PA = x_store[8, :]
    Q_PV = x_store[9, :]
    P_SA = x_store[10, :]
    P_SV = x_store[11, :]
    P_PA = x_store[12, :]
    P_PV = x_store[13, :]

    return t_vec, p_a, p_v, Q_int, Q_ext, V_a, V_v, Q_SA, Q_SV, Q_PA, Q_PV, P_SA, P_SV, P_PA, P_PV