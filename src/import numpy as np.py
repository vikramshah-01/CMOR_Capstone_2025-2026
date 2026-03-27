import numpy as np
import pandas as pd

# Given data
N = 5
p = 0.6
r, d = 100, 110
alpha = {0: 0.4, 1: 0.3, 2: 0.2, 3: 0.1}  # P(W=k)=alpha_k

def beta(a: int) -> float:
    """beta_a = P(W >= a)."""
    if a <= 0:
        return 1.0
    return sum(prob for k, prob in alpha.items() if k >= a)

A_candidates = list(range(0, 5))

# compute V_m(i) for i up to some max_i 
max_i = 80
pad = 10
Imax = max_i + pad

V = np.zeros((N + 1, Imax + 1))          # V[m,i]
Aopt = np.zeros((N + 1, Imax + 1), int)  # argmax a at (m,i)

# Base case: V_0(i) = i(r-d)
for i in range(Imax + 1):
    V[0, i] = i * (r - d)

# DP recursion
for m in range(1, N + 1):
    for i in range(max_i + 1):
        best_val = -1e18
        best_a = 0

        for a in A_candidates:
            if i == 0:
                # Vm(0)= max_a { p r + sum_{k=0}^{a-1} alpha_k V_{m-1}(k) + beta_a V_{m-1}(a) }
                s = sum(alpha[k] * V[m - 1, k] for k in alpha if k < a)
                val = p * r + s + beta(a) * V[m - 1, a]
            else:
                # Vm(i)= max_a { r + sum_{k=0}^{a-1} alpha_k[ p V(i+k) + (1-p)V(i-1+k) ]
                #              + beta_a[ p V(i+a) + (1-p)V(i-1+a) ] }
                s = sum(
                    alpha[k] * (p * V[m - 1, i + k] + (1 - p) * V[m - 1, i - 1 + k])
                    for k in alpha if k < a
                )
                val = r + s + beta(a) * (p * V[m - 1, i + a] + (1 - p) * V[m - 1, i - 1 + a])

            if val > best_val + 1e-9:
                best_val = val
                best_a = a

        V[m, i] = best_val
        Aopt[m, i] = best_a

# Report results up to i=3
V_table = pd.DataFrame(V[:N+1, :4], index=range(N+1), columns=[0,1,2,3])
A_table = pd.DataFrame(Aopt[:N+1, :4], index=range(N+1), columns=[0,1,2,3])

print("V_m(i) for i=0..3:")
print(V_table)
print("\nA(m,i) for i=0..3:")
print(A_table)