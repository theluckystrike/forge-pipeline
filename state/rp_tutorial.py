"""
Tutorial: the reset parameter in ReservoirPy ESN training.

This script demonstrates the effect of resetting reservoir state before
running a trained ESN on new data. It is the verified content for the
tutorial notebook.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reservoirpy.nodes import Reservoir, Ridge
from reservoirpy.datasets import mackey_glass

# --- data ---
X = mackey_glass(n_timesteps=2000, tau=17, seed=42)
X = X.reshape(-1, 1)
train = X[:1500]
test = X[1500:2000]

# --- build ESN ---
res = Reservoir(100, lr=0.5, input_scaling=0.5, seed=42)
readout = Ridge(ridge=1e-6)
esn = res >> readout

# --- fit ---
esn.fit(train, train)

# --- predict WITHOUT reset ---
pred_no_reset = esn.run(test)

# --- reset state, then predict WITH reset ---
res.reset()
pred_reset = esn.run(test)

# --- metrics ---
mse_no_reset = float(np.mean((pred_no_reset - test) ** 2))
mse_reset = float(np.mean((pred_reset - test) ** 2))

print("MSE no reset :", mse_no_reset)
print("MSE reset    :", mse_reset)
print("first 3 no_reset:", np.round(pred_no_reset[:3, 0], 4))
print("first 3 reset   :", np.round(pred_reset[:3, 0], 4))

# --- plot the transient ---
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(test[:60], label="target", color="black", lw=1.5)
ax.plot(pred_no_reset[:60], label="no reset", color="tab:blue", ls="--")
ax.plot(pred_reset[:60], label="reset", color="tab:red", ls=":")
ax.set_xlabel("timestep")
ax.set_ylabel("value")
ax.legend()
fig.tight_layout()
fig.savefig("/tmp/reset_transient.png", dpi=120)
print("saved /tmp/reset_transient.png")
