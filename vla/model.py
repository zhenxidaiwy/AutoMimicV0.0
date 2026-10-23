"""High-level 'watch the human' model: keypoint window -> future robot reference chunk + dance / phase / contact."""
import torch
import torch.nn as nn

from data import PHASES


class WatchNet(nn.Module):
  def __init__(self, W=30, H=25, d=128, layers=3, heads=4, n_joint=29, aux=True):
    super().__init__()
    self.H, self.out_dim, self.aux = H, n_joint + 6, aux
    self.inp = nn.Linear(17 * 3, d)
    self.pos = nn.Parameter(torch.zeros(1, W, d))
    enc = nn.TransformerEncoderLayer(d, heads, 4 * d, dropout=0.1, batch_first=True, norm_first=True)
    self.enc = nn.TransformerEncoder(enc, layers)
    self.norm = nn.LayerNorm(2 * d)
    self.act_head = nn.Sequential(nn.Linear(2 * d, 2 * d), nn.GELU(), nn.Linear(2 * d, H * self.out_dim))
    self.dance_head = nn.Linear(2 * d, 2)
    self.phase_head = nn.Linear(2 * d, len(PHASES))
    self.contact_head = nn.Linear(2 * d, 4)  # (L planted?, R planted?) x 2 logits

  def forward(self, x):
    h = self.enc(self.inp(x) + self.pos)
    h = self.norm(torch.cat([h[:, -1], h.mean(1)], -1))  # last token (now) + window summary
    out = {"chunk": self.act_head(h).view(-1, self.H, self.out_dim)}
    if self.aux:
      out.update(dance=self.dance_head(h), phase=self.phase_head(h), contact=self.contact_head(h).view(-1, 2, 2))
    return out
