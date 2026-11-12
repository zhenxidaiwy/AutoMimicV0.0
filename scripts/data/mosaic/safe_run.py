"""Run mosaic.py with torch.load kept at weights_only=True (PyTorch >= 2.6 default), allow-listing exactly the
globals that live/yolov8n-pose.pt references (listed with pickletools, no unpickling):
  python safe_run.py mosaic.py <in_cut.mp4> <out.mp4> <dets.json> [imgsz]"""
import builtins, collections, runpy, sys
import torch
import ultralytics.nn.modules.block as B
import ultralytics.nn.modules.conv as C
import ultralytics.nn.modules.head as H
import ultralytics.nn.tasks as T
nn = torch.nn
torch.serialization.add_safe_globals([
  builtins.getattr, builtins.set, collections.OrderedDict,
  nn.SiLU, nn.BatchNorm2d, nn.ModuleList, nn.Sequential, nn.Conv2d, nn.MaxPool2d, nn.Upsample,
  B.Bottleneck, B.C2f, B.DFL, B.SPPF, C.Concat, C.Conv, H.Detect, H.Pose, T.PoseModel])
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
