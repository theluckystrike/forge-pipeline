import json

cells = []

def md(src):
    cells.append({"cell_type":"markdown","metadata":{},"source":src})

def code(src, outputs=None):
    cells.append({"cell_type":"code","execution_count":None,"metadata":{},"outputs":outputs or [],"source":src})

md([
 "## The `reset` parameter in ReservoirPy\n",
 "\n",
 "This tutorial explains what the `reset` method does on a ReservoirPy node and why it matters when you run a trained Echo State Network (ESN) on new data.\n",
 "\n",
 "Every node in ReservoirPy keeps an internal state, a vector that carries the memory of the inputs it has seen. When you train an ESN, the reservoir state at the end of training holds information about the training sequence. If you then run the same ESN on a test sequence without touching that state, the first predictions are influenced by the leftover training state. Calling `reset()` zeroes the state so the network starts each run from a clean slate.\n",
 "\n",
 "The difference is easiest to see on a forecasting task. We train an ESN on the Mackey-Glass time series, then predict the next 500 steps twice, once with the training state intact and once after a `reset()`.\n",
])

code([
 "import numpy as np\n",
 "import matplotlib.pyplot as plt\n",
 "from reservoirpy.nodes import Reservoir, Ridge\n",
 "from reservoirpy.datasets import mackey_glass\n",
 "\n",
 "X = mackey_glass(n_timesteps=2000, tau=17, seed=42).reshape(-1, 1)\n",
 "train, test = X[:1500], X[1500:2000]\n",
 "\n",
 "res = Reservoir(100, lr=0.5, input_scaling=0.5, seed=42)\n",
 "readout = Ridge(ridge=1e-6)\n",
 "esn = res >> readout\n",
 "esn.fit(train, train)\n",
 "\n",
 "# run without touching the state\n",
 "pred_no_reset = esn.run(test)\n",
 "\n",
 "# zero the reservoir state, then run again\n",
 "res.reset()\n",
 "pred_reset = esn.run(test)\n",
 "\n",
 "mse_no_reset = float(np.mean((pred_no_reset - test) ** 2))\n",
 "mse_reset = float(np.mean((pred_reset - test) ** 2))\n",
 "print(f\"MSE without reset: {mse_no_reset:.3e}\")\n",
 "print(f\"MSE with reset   : {mse_reset:.3e}\")\n",
])

md([
 "The two runs give very different errors. Without a reset the reservoir carries its training state into the test run, so the first predictions are already close to the target and the mean squared error is tiny. After a `reset()` the state starts at zero, the network needs a few timesteps to warm up, and the transient pushes the error up.\n",
 "\n",
 "The plot below zooms into the first 60 timesteps of the test sequence. The no-reset prediction tracks the target from the first step. The reset prediction starts slightly off and converges within a few steps.\n",
])

code([
 "fig, ax = plt.subplots(figsize=(8, 4))\n",
 "ax.plot(test[:60], label=\"target\", color=\"black\", lw=1.5)\n",
 "ax.plot(pred_no_reset[:60], label=\"no reset\", color=\"tab:blue\", ls=\"--\")\n",
 "ax.plot(pred_reset[:60], label=\"reset\", color=\"tab:red\", ls=\":\")\n",
 "ax.set_xlabel(\"timestep\")\n",
 "ax.set_ylabel(\"value\")\n",
 "ax.legend()\n",
 "fig.tight_layout()\n",
 "plt.show()\n",
])

md([
 "## When to use `reset`\n",
 "\n",
 "Use `reset()` when you want each run to be independent of what came before, for example when you evaluate a model on several separate sequences or when you compare runs that should start from the same initial condition. Skip it when the training state is a useful prior, such as when the test sequence continues directly from the training sequence.\n",
 "\n",
 "The `reset` method lives on every node and returns the previous state, so you can inspect or restore it if needed. See the [node documentation](https://reservoirpy.readthedocs.io/en/latest/user_guide/node.html) for the full API.\n",
])

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "dev", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}

with open("/tmp/reset_tutorial.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("wrote /tmp/reset_tutorial.ipynb with", len(cells), "cells")
