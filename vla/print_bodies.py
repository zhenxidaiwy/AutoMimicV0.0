"""Print the G1 body order used by mjlab (same order as body_pos_w in the motion npz) and joint order."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))

if __name__ == "__main__":
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.scene import Scene
  from mjlab.sim import Simulation, SimulationCfg
  from mjlab.tasks.registry import load_env_cfg

  cfg = load_env_cfg("Unitree-G1-Tracking-No-State-Estimation")
  scene = Scene(cfg.scene, device="cuda:0")
  sim = Simulation(num_envs=1, cfg=SimulationCfg(), model=scene.compile(), device="cuda:0")
  scene.initialize(sim.mj_model, sim.model, sim.data)
  robot = scene["robot"]
  print("bodies", list(robot.body_names))
  print("joints", list(robot.joint_names))
