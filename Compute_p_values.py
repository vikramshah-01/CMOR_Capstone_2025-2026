# Get Dependencies
import numpy as np
import scipy.optimize
import pandas as pd
import scipy.stats as st
from openpyxl import load_workbook
import matplotlib.pyplot as plt


# read excel file

filename = 'monte_carlo_results_2025-07-15.xlsx'
df_baseline = pd.read_excel(filename, sheet_name='Baseline')
df_vasopressin = pd.read_excel(filename, sheet_name='Vasopressin')
df_phenylephrine = pd.read_excel(filename, sheet_name='Phenylephrine')




# Compute p-values
def compute_p_values_vaso(df_vasopressin, df_baseline, var_name):
    ttest_result = st.ttest_ind(df_vasopressin[var_name], df_baseline[var_name], 
                                     axis=0, equal_var=False, nan_policy='omit', alternative='two-sided')
    p_value = ttest_result.pvalue

    base_mean = df_baseline[var_name].mean()
    vaso_mean = df_vasopressin[var_name].mean()
    print(var_name, ' Base', round(base_mean,2) , \
          'vs Vaso ', round(vaso_mean,2), '\t', \
            round(100*(vaso_mean-base_mean)/base_mean,1) , \
            '% \t p-val =', round(p_value,4))


def compute_p_values_phe(df_phenylephrine, df_baseline, var_name):
    ttest_result = st.ttest_ind(df_phenylephrine[var_name], df_baseline[var_name], 
                                     axis=0, equal_var=False, nan_policy='omit', alternative='two-sided')
    p_value = ttest_result.pvalue

    base_mean = df_baseline[var_name].mean()
    pheny_mean = df_phenylephrine[var_name].mean()

    print(var_name, ' Base', round(df_baseline[var_name].mean(),2) , \
        'vs Phe ', round(df_phenylephrine[var_name].mean(),2), '\t', \
        round(100*(pheny_mean-base_mean)/base_mean,1) , \
        '% \t p-val =', round(p_value,4))



list_of_variables = ['SVR', 'PVR', 'Q_v', 'Q_u', 'Q_l', 'P_sa', 'P_pa', 'P_pv', 'S_pa', 'OER']

print('')
print('----------- BASELINE -----------')
for var in list_of_variables:
    print( var, ' Base mean =', round(df_baseline[var].mean(),2) , \
        '\t std =', round(df_baseline[var].std(),2) )

print('')
print('--------- VASOPRESSIN -----------')
for var in list_of_variables:
    print( var, ' Vaso mean =', round(df_vasopressin[var].mean(),2) , \
        '\t std =', round(df_vasopressin[var].std(),2) )

print('')
print('--------- PHENYLEPHRINE ---------')
for var in list_of_variables:
    print( var, ' Phen mean =', round(df_phenylephrine[var].mean(),2) , \
        '\t std =', round(df_phenylephrine[var].std(),2) )

print('')
print('')
print('')
print('------ BASELINE vs VASOPRESSIN --------')
for var in list_of_variables:
    compute_p_values_vaso(df_vasopressin, df_baseline, var)  


print('------ BASELINE vs PHENYLEPHRINE ------')
for var in list_of_variables:
    compute_p_values_phe(df_phenylephrine, df_baseline, var) 



print('----------- PVR  ----------')

fig, ax = plt.subplots(1, 2, figsize=(8, 3))
k=0
ax[k].scatter(df_baseline.PVR, df_baseline.OER, label='Baseline', alpha=0.25, color='blue')
ax[k].scatter(df_vasopressin.PVR, df_vasopressin.OER, label='Vasopressin', alpha=0.25, color='green')
# plt.scatter(df_phenylephrine.PVR, df_phenylephrine.OER, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('PVR')
ax[k].set_xlim(0,5)
ax[k].set_ylabel('OER')
ax[k].set_ylim(10,60)
ax[k].grid()

k=1
ax[k].scatter(df_baseline.PVR, df_baseline.OER, label='Baseline', alpha=0.25, color='blue')
# ax[k].scatter(df_vasopressin.PVR, df_vasopressin.OER, label='Vasopressin', alpha=0.25, color='green')
ax[k].scatter(df_phenylephrine.PVR, df_phenylephrine.OER, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('PVR')
ax[k].set_xlim(0,5)
ax[k].set_ylabel('OER')
ax[k].set_ylim(10,60)
ax[k].grid()
plt.show()


fig, ax = plt.subplots(1, 2, figsize=(8, 3))
k=0
ax[k].scatter(df_baseline.PVR, df_baseline.Q_v, label='Baseline', alpha=0.25, color='blue')
ax[k].scatter(df_vasopressin.PVR, df_vasopressin.Q_v, label='Vasopressin', alpha=0.25, color='green')
# plt.scatter(df_phenylephrine.PVR, df_phenylephrine.Q_v, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('PVR')
ax[k].set_xlim(0,5)
ax[k].set_ylabel('Q_v')
ax[k].set_ylim(0,3)
ax[k].grid()

k=1
ax[k].scatter(df_baseline.PVR, df_baseline.Q_v, label='Baseline', alpha=0.25, color='blue')
# ax[k].scatter(df_vasopressin.PVR, df_vasopressin.Q_v, label='Vasopressin', alpha=0.25, color='green')
ax[k].scatter(df_phenylephrine.PVR, df_phenylephrine.Q_v, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('PVR')
ax[k].set_xlim(0,5)
ax[k].set_ylabel('Q_v')
ax[k].set_ylim(0,3)
ax[k].grid()
plt.show()



print('----------- SVR  ----------')


fig, ax = plt.subplots(1, 2, figsize=(8, 3))
k=0
ax[k].scatter(df_baseline.SVR, df_baseline.OER, label='Baseline', alpha=0.25, color='blue')
ax[k].scatter(df_vasopressin.SVR, df_vasopressin.OER, label='Vasopressin', alpha=0.25, color='green')
# plt.scatter(df_phenylephrine.SVR, df_phenylephrine.OER, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('SVR')
ax[k].set_xlim(10,25)
ax[k].set_ylabel('OER')
ax[k].set_ylim(10,60)
ax[k].grid()

k=1
ax[k].scatter(df_baseline.SVR, df_baseline.OER, label='Baseline', alpha=0.25, color='blue')
# ax[k].scatter(df_vasopressin.SVR, df_vasopressin.OER, label='Vasopressin', alpha=0.25, color='green')
ax[k].scatter(df_phenylephrine.SVR, df_phenylephrine.OER, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('SVR')
ax[k].set_xlim(10,25)
ax[k].set_ylabel('OER')
ax[k].set_ylim(10,60)
ax[k].grid()
plt.show()






fig, ax = plt.subplots(1, 2, figsize=(8, 3))
k=0
ax[k].scatter(df_baseline.SVR, df_baseline.Q_v, label='Baseline', alpha=0.25, color='blue')
ax[k].scatter(df_vasopressin.SVR, df_vasopressin.Q_v, label='Vasopressin', alpha=0.25, color='green')
# plt.scatter(df_phenylephrine.SVR, df_phenylephrine.Q_v, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('SVR')
ax[k].set_xlim(10,25)
ax[k].set_ylabel('Q_v')
ax[k].set_ylim(0,3)
ax[k].grid()

k=1
ax[k].scatter(df_baseline.SVR, df_baseline.Q_v, label='Baseline', alpha=0.25, color='blue')
# ax[k].scatter(df_vasopressin.SVR, df_vasopressin.Q_v, label='Vasopressin', alpha=0.25, color='green')
ax[k].scatter(df_phenylephrine.SVR, df_phenylephrine.Q_v, label='Phenylephrine', alpha=0.25, color='red')
ax[k].legend()
ax[k].set_xlabel('SVR')
ax[k].set_xlim(10,25)
ax[k].set_ylabel('Q_v')
ax[k].set_ylim(0,3)
ax[k].grid()
plt.show()



# linear regression for OER vs PVR
from sklearn.linear_model import LinearRegression
def linear_regression(df, x_var, y_var):
    model = LinearRegression()
    X = df[[x_var]].values.reshape(-1, 1)
    y = df[y_var].values
    model.fit(X, y)
    return model.coef_[0], model.intercept_


coef, intercept = linear_regression(df_baseline, 'SVR_base', 'OER')
print('Baseline: intercept:', intercept, 'slope:', coef)

coef, intercept = linear_regression(df_vasopressin, 'SVR_base', 'OER')
print('Vasopressin: intercept:', intercept, 'slope:', coef)