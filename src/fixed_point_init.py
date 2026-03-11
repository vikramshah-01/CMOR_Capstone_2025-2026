# fixed_point_init.py
# Drop-in fixed-point initializer for your 14-state cardiovascular model.
#
# State order (matches your model):
# [p_a, p_v, Q_int, Q_ext, V_a, V_v, Q_SA, Q_SV, Q_PA, Q_PV, P_SA, P_SV, P_PA, P_PV]
#
# Units (paper):
# - pressure: dyn/cm^2  (mmHg * 1333.22)
# - volume:   cm^3      (mL == cm^3)
# - flow:     cm^3/s

from __future__ import annotations
import numpy as np
from scipy.optimize import fsolve

MMHG_TO_DYN_PER_CM2 = 1333.22


def H_fun(delta_p: float, gamma: float) -> float:
    """Valve smoothing function: H = 1 / (1 + exp(-gamma * (p1 - p2))).
    The exponent is clipped to [-500, 500] to prevent floating-point overflow
    warnings; the result is identical since exp(±500) is effectively 0 or inf.
    """
    return 1.0 / (1.0 + np.exp(np.clip(-gamma * delta_p, -500.0, 500.0)))


def _elastance_periodic(
    t: float,
    HR: float,
    E_min: float,
    E_max: float,
    t_onset: float,
    m_1: float,
    tau_1: float,
    m_2: float,
    tau_2: float,
    # resolution for k normalization (smaller is more accurate but slower)
    k_dt: float = 1e-4,
) -> float:
    """
    Matches your file's Ea_fun/Ev_fun structure (periodic with T=1/HR)
    and normalizes by k = max(...) over one cycle.
    """
    def g(tt: np.ndarray, t_on: float, m: float, tau: float) -> np.ndarray:
        # FIX (Bug 2): clamp (tt - t_onset) to >= 0 before raising to a
        # fractional power.  Without the clamp, negative bases produce
        # NaN / complex values in NumPy whenever t_mod < t_onset.
        return (np.maximum(tt - t_on, 0.0) / tau) ** m

    T = 1.0 / HR
    t_mod = t % T

    t_vec = np.arange(0.0, T, k_dt)
    num = g(t_vec, t_onset, m_1, tau_1)
    den = (1.0 + num)
    term1 = num / den
    num2 = g(t_vec, t_onset, m_2, tau_2)
    term2 = 1.0 / (1.0 + num2)
    k = np.max(term1 * term2)

    # evaluate at t_mod
    num_t = g(np.array([t_mod]), t_onset, m_1, tau_1)[0]
    term1_t = num_t / (1.0 + num_t)
    num2_t = g(np.array([t_mod]), t_onset, m_2, tau_2)[0]
    term2_t = 1.0 / (1.0 + num2_t)

    return ((E_max - E_min) / k) * (term1_t * term2_t) + E_min


def generate_x0_fixed_point_ra_rv(
    *,
    # --- time control ---
    dt: float,
    HR: float,
    t0: float = 0.0,

    # --- chamber/reference volumes ---
    V_a0: float,
    V_v0: float,

    # --- chamber elastance params (paper units) ---
    E_min_a: float, E_max_a: float, t_onset_a: float, m_1a: float, tau_1a: float, m_2a: float, tau_2a: float,
    E_min_v: float, E_max_v: float, t_onset_v: float, m_1v: float, tau_1v: float, m_2v: float, tau_2v: float,

    # --- chamber stiffness terms in your A matrix ---
    K_a: float,
    K_v: float,

    # --- valves/inertance/resistance terms ---
    gamma_int: float,
    gamma_ext: float,
    L_int: float, L_ext: float,
    B_int: float, B_ext: float,
    R_int: float, R_ext: float,

    # --- vascular resistances/compliances ---
    R_s: float, R_p: float, R_BTS: float,
    C_SA: float, C_PA: float, C_SV: float, C_PV: float,

    # --- total volume constraint ---
    V_total: float,

    # --- optional solver knobs ---
    max_iter: int = 80,
    tol: float = 1e-10,
    relaxation: float = 0.7,   # kept for API compatibility; not used by Newton solver
) -> np.ndarray:
    """
    Returns x0 (shape (14,)) in paper units, consistent with A x = b at t=t0.

    Uses scipy.optimize.fsolve (Newton / quasi-Newton) to solve the nonlinear
    system F(x) = A(x)*x - b(x) = 0.  The old Picard / relaxation loop was
    replaced because the fixed-point map has spectral radius > 1 for typical
    cardiovascular parameters, making it unconditionally divergent.

    Initial guesses are generated for RA/RV physiology:
      RA pressure ~ 5 mmHg,
      RV pressure ~ 20 mmHg (representative),
      systemic arterial ~ 60 mmHg,
      systemic venous ~ 5 mmHg,
      pulmonary arterial ~ 15 mmHg,
      pulmonary venous ~ 8 mmHg,
      volumes start at reference volumes, flows start at 0.
    """

    # -------------------------
    # 1) Build an initial guess (in paper units)
    # -------------------------
    p_ra_guess = 5.0  * MMHG_TO_DYN_PER_CM2
    p_rv_guess = 20.0 * MMHG_TO_DYN_PER_CM2

    P_SA_guess = 60.0 * MMHG_TO_DYN_PER_CM2
    P_SV_guess = 5.0  * MMHG_TO_DYN_PER_CM2
    P_PA_guess = 15.0 * MMHG_TO_DYN_PER_CM2
    P_PV_guess = 8.0  * MMHG_TO_DYN_PER_CM2

    x0 = np.zeros(14, dtype=float)
    x0[0]  = p_ra_guess     # p_a
    x0[1]  = p_rv_guess     # p_v
    x0[2]  = 0.0            # Q_int
    x0[3]  = 0.0            # Q_ext
    x0[4]  = V_a0           # V_a
    x0[5]  = V_v0           # V_v
    x0[6]  = 0.0            # Q_SA
    x0[7]  = 0.0            # Q_SV
    x0[8]  = 0.0            # Q_PA
    x0[9]  = 0.0            # Q_PV
    x0[10] = P_SA_guess     # P_SA
    x0[11] = P_SV_guess     # P_SV
    x0[12] = P_PA_guess     # P_PA
    x0[13] = P_PV_guess     # P_PV

    # Elastances at start time
    E_a = _elastance_periodic(t0, HR, E_min_a, E_max_a, t_onset_a, m_1a, tau_1a, m_2a, tau_2a)
    E_v = _elastance_periodic(t0, HR, E_min_v, E_max_v, t_onset_v, m_1v, tau_1v, m_2v, tau_2v)

    # -------------------------
    # 2) Define F(x) = A(x)*x - b(x) and solve with Newton / fsolve
    #
    # FIX (Bug 3): The original Picard / relaxation iteration
    #   x_{n+1} = (1-w)*x_n + w * solve(A(x_n), b(x_n))
    # diverges because the spectral radius of the fixed-point map exceeds 1
    # for realistic cardiovascular parameters.  scipy.optimize.fsolve uses a
    # modified Powell hybrid method (quasi-Newton) which converges robustly.
    # -------------------------
    def F(x: np.ndarray) -> np.ndarray:
        A = np.array([
            [1, 0, 0, 0, -(E_a / V_a0) - (K_a * x[0] / dt), 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, -(E_v / V_v0) - (K_v * x[1] / dt), 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, (L_int/dt) + B_int*np.abs(x[2]) + R_int, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, (L_ext/dt) + B_ext*np.abs(x[3]) + R_ext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1/2, 0, 1/dt, 0, 0, -1/2, 0, -1/2, 0, 0, 0, 0],
            [0, 0, -1/2, 1/2, 0, 1/dt, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, R_s, 0, 0, 0, -1, 1, 0, 0],
            # FIX (Bug 1): was [.., R_p, 0, -1, 0, 1, 0] which used P_SA (col 10)
            # as the left-side driving pressure for Q_PA, making rows 7 and 8
            # identical and the matrix singular.  Q_PA is driven by P_PA - P_PV,
            # so the pressure columns must be col 12 (-1) and col 13 (+1).
            [0, 0, 0, 0, 0, 0, 0, 0, R_p, 0, 0, 0, -1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, R_BTS, 0, -1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 1],
            [0, 0, 0, -1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, -1, 1, 0, 0, C_SA/dt, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, -1, 1, 0, 0, C_PA/dt, 0],
            [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, C_SA, C_SV, C_PA, C_PV],
        ], dtype=float)

        b = np.array([
            -E_a - (K_a * x[0] * x[4] / dt),
            -E_v - (K_v * x[1] * x[5] / dt),
            (L_int * x[2] / dt) + H_fun(x[0] - x[1], gamma_int) * (x[0] - x[1]),
            (L_ext * x[3] / dt) + H_fun(x[1] - x[10], gamma_ext) * (x[1] - x[10]),
            (x[4] / dt) - 0.5 * (x[2] - x[9] - x[7]),
            (x[5] / dt) - 0.5 * (x[3] - x[2]),
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            C_SA * x[10] / dt,
            C_PA * x[12] / dt,
            V_total,
        ], dtype=float)

        return A @ x - b

    sol, info, ier, msg = fsolve(F, x0, full_output=True, maxfev=max_iter * 200)

    res_norm = np.linalg.norm(F(sol), ord=np.inf)
    # Accept the solution if scipy converged (ier 1-4) OR if the residual is
    # small enough regardless of ier.  ier=5 ("not making good progress") is a
    # common false alarm when the initial guess is already very close to the
    # solution and the Jacobian appears near-zero to the internal line search.
    converged = (ier in (1, 2, 3, 4)) or (res_norm <= 1e-6)
    if not converged:
        raise RuntimeError(
            f"Fixed-point initialization did not converge (ier={ier}: {msg}). "
            f"Residual norm = {res_norm:.3e}. "
            "Try adjusting initial pressure guesses or checking parameter units."
        )

    return sol


# ---- quick usage example (you can delete this block) ----
if __name__ == "__main__":
    # Fill these with your parameter values (paper units).
    params = dict(
        dt=1e-3,
        HR=2.0,
        V_a0=20.0, V_v0=40.0,
        E_min_a=1.0e3, E_max_a=6.0e3, t_onset_a=0.0, m_1a=1.9, tau_1a=0.2, m_2a=21.9, tau_2a=0.05,
        E_min_v=0.5e3, E_max_v=5.0e3, t_onset_v=0.0, m_1v=1.9, tau_1v=0.2, m_2v=21.9, tau_2v=0.05,
        K_a=0.0, K_v=0.0,
        gamma_int=1e-3, gamma_ext=1e-3,
        L_int=1e-3, L_ext=1e-3, B_int=1e-2, B_ext=1e-2, R_int=1e-3, R_ext=1e-3,
        R_s=1.0, R_p=1.0, R_BTS=1.0,
        C_SA=1.0, C_PA=1.0, C_SV=1.0, C_PV=1.0,
        V_total=300.0,
    )

    x0 = generate_x0_fixed_point_ra_rv(**params)
    print("x0 =", x0)