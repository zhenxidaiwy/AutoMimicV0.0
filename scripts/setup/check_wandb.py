"""Check wandb version / Settings fields and how rsl_rl calls it; whether the user is logged in."""
import inspect
import os

import wandb
from rsl_rl.utils import wandb_utils

if __name__ == "__main__":
    print("wandb", wandb.__version__)
    print("Settings has start_method:", "start_method" in wandb.Settings.model_fields)
    src = inspect.getsource(wandb_utils.WandbSummaryWriter.__init__)
    print(src[:1500])
    print("netrc has api.wandb.ai:", "api.wandb.ai" in open(os.path.expanduser("~/.netrc")).read()
          if os.path.exists(os.path.expanduser("~/.netrc")) else False)
