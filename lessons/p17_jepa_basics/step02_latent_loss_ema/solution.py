"""Step 2: the I-JEPA loss (masked, in embedding space) and the EMA teacher update."""
from __future__ import annotations

import torch
import torch.nn.functional as F


def masked_latent_loss(pred: torch.Tensor, target: torch.Tensor, keep: torch.Tensor) -> torch.Tensor:
    """pred, target: (B, N, D); keep: (B, N) bool, True = visible. The loss only looks at the HIDDEN patches."""
    hidden = ~keep
    if not hidden.any():
        return pred.sum() * 0.0
    return F.smooth_l1_loss(pred[hidden], target[hidden])


@torch.no_grad()
def ema_update(teacher: torch.nn.Module, student: torch.nn.Module, m: float = 0.99) -> None:
    """In place: teacher = m * teacher + (1 - m) * student, parameter by parameter."""
    for p_t, p_s in zip(teacher.parameters(), student.parameters()):
        p_t.mul_(m).add_(p_s, alpha=1 - m)


if __name__ == "__main__":
    t, s = torch.nn.Linear(2, 2), torch.nn.Linear(2, 2)
    before = t.weight.clone()
    ema_update(t, s, 0.9)
    print("teacher moved by", (t.weight - before).abs().sum().item())
