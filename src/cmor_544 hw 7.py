import numpy as np

# alpha = 0.9

# Price transition matrix
P = np.array([
    [0.0, 1.0, 0.0, 0.0],
    [0.3, 0.0, 0.7, 0.0],
    [0.0, 0.7, 0.0, 0.3],
    [0.0, 0.0, 1.0, 0.0]
])

prices = [0, 1, 2, 3]

# Order States
# 0:(0,0), 1:(1,0), 2:(2,0), 3:(3,0), 4:(0,1), 5:(1,1), 6:(2,1), 7:(3,1)
states = [(y, z) for z in [0, 1] for y in prices]

def state_index(y, z):
    return z * 4 + y

def actions(state):
    y, z = state
    if z == 0:
        return ["hold", "buy"]
    else:
        return ["hold", "sell"]

def reward_and_transition(state, action):
    """
    Returns:
        r: immediate reward
        next_probs: length-8 vector of transition probabilities
    """
    y, z = state
    next_probs = np.zeros(8)

    if action == "hold":
        r = 0
        next_z = z
    elif action == "buy":
        r = -y
        next_z = 1
    elif action == "sell":
        r = y
        next_z = 0
    else:
        raise ValueError("Invalid action")

    for y_next in prices:
        next_probs[state_index(y_next, next_z)] = P[y, y_next]

    return r, next_probs

# def policy_evaluation(policy):
#     """
#     Solve:
#         V = r_pi + alpha * P_pi * V
#     => (I - alpha P_pi)V = r_pi
#     """
#     n = len(states)
#     A = np.eye(n)
#     b = np.zeros(n)

#     for s_idx, s in enumerate(states):
#         a = policy[s_idx]
#         r, probs = reward_and_transition(s, a)
#         A[s_idx, :] -= alpha * probs
#         b[s_idx] = r

#     V = np.linalg.solve(A, b)
#     return V

# def policy_improvement(V):
#     new_policy = []
#     stable = True

#     for s_idx, s in enumerate(states):
#         best_action = None
#         best_value = -np.inf

#         for a in actions(s):
#             r, probs = reward_and_transition(s, a)
#             q = r + alpha * probs @ V
#             if q > best_value:
#                 best_value = q
#                 best_action = a

#         new_policy.append(best_action)

#     return new_policy

# def policy_iteration(initial_policy, verbose=True):
#     policy = initial_policy[:]
#     iteration = 0

#     while True:
#         V = policy_evaluation(policy)

#         if verbose:
#             print(f"Iteration {iteration}")
#             print("Policy:", policy)
#             print("Value function:", np.round(V, 4))
#             print()

#         new_policy = policy_improvement(V)

#         if new_policy == policy:
#             return policy, V

#         policy = new_policy
#         iteration += 1

# # Initial policy
# # buy at (0,0), sell at (3,1), hold elsewhere
# initial_policy = [
#     "buy",   # (0,0)
#     "hold",  # (1,0)
#     "hold",  # (2,0)
#     "hold",  # (3,0)
#     "hold",  # (0,1)
#     "hold",  # (1,1)
#     "hold",  # (2,1)
#     "sell"   # (3,1)
# ]

# opt_policy, opt_V = policy_iteration(initial_policy)

# print("Optimal policy:", opt_policy)
# print("Optimal value function:", np.round(opt_V, 4))

import gurobipy as gp
from gurobipy import GRB

# Build LP model
m = gp.Model("stock_trading_lp")
m.setParam("OutputFlag", 0)

# Value variables V(s)
V = m.addVars(len(states), lb=-GRB.INFINITY, name="V")

# Objective: minimize sum of V(s)
m.setObjective(gp.quicksum(V[s] for s in range(len(states))), GRB.MINIMIZE)

# Bellman inequality constraints:
# V(s) >= r(s,a) + alpha * sum P(s'|s,a) V(s')
for s_idx, s in enumerate(states):
    for a in actions(s):
        reward, probs = reward_and_transition(s, a)
        m.addConstr(
            V[s_idx] >= reward + alpha * gp.quicksum(probs[j] * V[j] for j in range(len(states))),
            name=f"bellman_{s_idx}_{a}"
        )

# Solve
m.optimize()

# Extract optimal value function
V_star = np.array([V[s].X for s in range(len(states))])

# Recover optimal policy
policy = []
for s_idx, s in enumerate(states):
    best_action = None
    best_q = -float("inf")

    for a in actions(s):
        reward, probs = reward_and_transition(s, a)
        q = reward + alpha * np.dot(probs, V_star)
        if q > best_q:
            best_q = q
            best_action = a

    policy.append(best_action)

# Print results
print("Optimal value function:")
for s_idx, s in enumerate(states):
    print(f"V{s} = {V_star[s_idx]:.4f}")

print("\nOptimal policy:")
for s_idx, s in enumerate(states):
    print(f"pi{s} = {policy[s_idx]}")