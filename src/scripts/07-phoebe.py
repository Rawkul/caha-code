import phoebe
from phoebe import u
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Ejemplo con V. Cambiar aquí para hacer el ajuste diferente con cada filtro.
# Solo están "B", "V" o "R".
FILTER = "V"

lcr = pd.read_csv("output/data/{}.csv".format(FILTER))

# Datos iniciales conocidos
PERIOD = 5.4108 * u.hour
DISTANCE = 389.895 * 3.086e+16

# Define basic binary
b = phoebe.default_contact_binary()

flux = np.array(lcr.flux_normalized)
sigmas = np.array(lcr.error_flux_normalized)

b.add_dataset("lc", times = np.array(lcr.time) * u.hour, fluxes = flux, dataset = FILTER, sigmas = sigmas)
b.set_value("period@binary@orbit@component", PERIOD)
b.set_value("distance", DISTANCE)

print(b.get_parameter(qualifier='fluxes', dataset=FILTER, context='dataset'))

b.plot(x='phases', show=True)

b.add_solver('estimator.ebai',
             ebai_method='knn',
             lc_datasets='R',
             solver = "myebai")
             
b.run_solver(solver='myebai', solution='ebai_sol') 
print(b.adopt_solution('ebai_sol', trial_run=True))

b.flip_constraint('asini@binary', solve_for='sma@binary')
b.flip_constraint('requivsumfrac', solve_for='requiv@primary')
b.flip_constraint('teffratio', solve_for='teff@primary')
b.adopt_solution('ebai_sol', adopt_parameters=['teffratio', 'requivsumfrac', 'incl', 't0_supconj'])

print(b.filter(qualifier=['ecc', 'per0', 'teff', 'sma', 'incl', 'q', 'requiv', 't0_supconj'], context='component'))
b.set_value_all('pblum_mode', 'dataset-scaled')
b.run_compute(irrad_method='none', model='after_estimators', overwrite=True)

b.plot(x='phases', m='.', show=True)
plt.ylabel("Flujo normalizado")
plt.xlabel("Fase")
plt.title("V")
plt.show()
plt.savefig("output/{}-ajuste.png".format(FILTER))

# A PARTIR DE AQUÍ EL CÓDIGO ES MUY PESADO Y SE REQUIERE DE MUCHA CAPACIDAD DE CÓMPUTO. CAMBIAR NITER=1 PARA
# REALIZAR UNA SOLA ITERACIÓN Y VER CUÁNTO PUEDE TARDAR
NITER = 1000

# ----
# OPTIMIZACIÓN DE LOS PARÁMETROS
b.add_compute('ellc', compute='fastcompute', overwrite = True)
b.add_solver('optimizer.nelder_mead',
             fit_parameters=['teffratio', 'requivsumfrac', 'incl@binary', 'q', 'ecc', 'per0', "t0_supconj"],
             #fit_parameters=["t0_supconj"],
             overwrite = True,
             solver = "mypowell")

print(b.get_solver(solver='mypowell'))
b.run_solver(solver='mypowell', maxiter=NITER, solution='nelder_sol')

print(b.get_solution('nelder_sol').filter(qualifier=['message', 'nfev', 'niter', 'success']))
print(b.adopt_solution('nelder_sol', trial_run=True))
b.adopt_solution('nelder_sol')

b.run_compute(compute="phoebe01", model='after_nm', overwrite = True)
b.plot(x='phases', m='.', show=True)

# ----
# ESTIMACIÓN DE LA INCERTIDUMBRE
b.add_distribution({'teffratio': phoebe.gaussian_around(0.1),
                    'requivsumfrac': phoebe.gaussian_around(0.1),
                    'incl@binary': phoebe.gaussian_around(3),
                    # 'sma@binary': phoebe.gaussian_around(0.1),
                    'q': phoebe.gaussian_around(0.1),
                    'ecc': phoebe.gaussian_around(0.01),
                    'per0': phoebe.gaussian_around(0.01)},
                    distribution='dist_error', 
                    overwrite_all = True)

b.add_solver('sampler.emcee',
             init_from='dist_error',
             compute='phoebe01',
             solver='emcee_solver', 
             overwrite = True)
                
b.run_solver('emcee_solver', niters=NITER, nwalkers=16, solution='emcee_sol')

b.plot_distribution_collection('dist_error', show=True, save = "a.png")

b.uncertainties_from_distribution_collection(solution='emcee_sol', tex=True)
