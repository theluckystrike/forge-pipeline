import numpy as np
from reservoirpy.nodes import Reservoir, Ridge
from reservoirpy.datasets import mackey_glass

# Generate a time series
X = mackey_glass(n_timesteps=2000, tau=17, seed=42)
X = X.reshape(-1, 1)

# Split train/test
train_len = 1500
X_train, X_test = X[:train_len], X[train_len:]

# Build ESN
res = Reservoir(100, lr=0.5, input_scaling=1.0, seed=42)
readout = Ridge(ridge=1e-6)

# Case 1: fit WITHOUT reset between train and test
esn_no_reset = res >> readout
esn_no_reset.fit(X_train, X_train)
pred_no_reset = esn_no_reset.run(X_test)

# Case 2: reset state before test
res2 = Reservoir(100, lr=0.5, input_scaling=1.0, seed=42)
readout2 = Ridge(ridge=1e-6)
esn_reset = res2 >> readout2
esn_reset.fit(X_train, X_train)
res2.reset()  # wash out internal memory
pred_reset = esn_reset.run(X_test)

print("X_test shape:", X_test.shape)
print("pred_no_reset shape:", pred_no_reset.shape)
print("pred_reset shape:", pred_reset.shape)
print("no_reset first 3:", np.round(pred_no_reset[:3,0],4))
print("reset first 3:", np.round(pred_reset[:3,0],4))
print("no_reset last 3:", np.round(pred_no_reset[-3:,0],4))
print("reset last 3:", np.round(pred_reset[-3:,0],4))
print("MSE no_reset:", np.mean((pred_no_reset-X_test)**2))
print("MSE reset:", np.mean((pred_reset-X_test)**2))
