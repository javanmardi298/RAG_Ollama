"""A latent world model you can train on a laptop, and use for DECISIONS: planning and surprise detection.

The world: a dot moving in a unit square, seen only as a 12x12 image. An action (dx, dy) moves it; walls clip.
The model (in the spirit of LeWorldModel and V-JEPA 2-AC):
    encoder   image -> z (latent state)
    predictor (z, action) -> next z
    loss      || predictor(z_t, a_t) - encoder(o_{t+1}) ||^2  +  SIGReg(z)  (prediction in latent space, no pixels)
Decisions:
    planning  Model Predictive Control with the Cross-Entropy Method: sample action sequences, roll them out in
              latent space, score by L1 distance to the goal image's embedding (the "energy" used by V-JEPA 2-AC),
              execute the first action, re-plan.
    surprise  prediction error of the world model; teleports (physically impossible jumps) score high.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from .sigreg import collapse_stats, sigreg

RES = 12
MAX_STEP = 0.1


class DotWorld:
    def __init__(self, seed: int = 0, noise: float = 0.0):
        self.rng = np.random.default_rng(seed)
        self.noise = noise
        yy, xx = np.mgrid[0:RES, 0:RES]
        self.grid = np.stack([xx, yy], -1).astype(np.float32) / (RES - 1)

    def render(self, pos: np.ndarray) -> np.ndarray:
        d2 = ((self.grid - pos) ** 2).sum(-1)
        img = np.exp(-d2 / (2 * 0.06 ** 2)).astype(np.float32)
        if self.noise:
            img += self.rng.normal(0, self.noise, img.shape).astype(np.float32)
        return img.reshape(-1)

    @staticmethod
    def step(pos: np.ndarray, action: np.ndarray) -> np.ndarray:
        return np.clip(pos + np.clip(action, -MAX_STEP, MAX_STEP), 0.0, 1.0)

    def random_pos(self) -> np.ndarray:
        return self.rng.uniform(0.05, 0.95, 2).astype(np.float32)

    def transitions(self, n: int, teleport_rate: float = 0.0):
        """Random (obs, action, next_obs, pos, next_pos, is_teleport) tuples."""
        o, a, o2, p, p2, tele = [], [], [], [], [], []
        for _ in range(n):
            pos = self.random_pos()
            act = self.rng.uniform(-MAX_STEP, MAX_STEP, 2).astype(np.float32)
            nxt = self.step(pos, act)
            t = self.rng.random() < teleport_rate
            if t:
                nxt = self.random_pos()                      # physically impossible jump
            o.append(self.render(pos)); a.append(act); o2.append(self.render(nxt))
            p.append(pos); p2.append(nxt); tele.append(t)
        f = lambda x: torch.tensor(np.array(x))  # noqa: E731
        return f(o), f(a), f(o2), f(p), f(p2), torch.tensor(tele)


class WorldModel(nn.Module):
    def __init__(self, z_dim: int = 16, hidden: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(RES * RES, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                     nn.Linear(hidden, z_dim))
        self.predictor = nn.Sequential(nn.Linear(z_dim + 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                       nn.Linear(hidden, z_dim))

    def predict(self, z: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        return z + self.predictor(torch.cat([z, a / MAX_STEP], -1))     # residual: predict the change


def train_world_model(n: int = 6000, epochs: int = 60, z_dim: int = 16, sigreg_weight: float = 1.0, lr: float = 2e-3,
                      batch: int = 256, seed: int = 0, log_every: int = 0) -> dict:
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)
    world = DotWorld(seed)
    o, a, o2, *_ = world.transitions(n)
    model = WorldModel(z_dim)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    history = []
    for ep in range(epochs):
        perm = torch.randperm(n, generator=gen)
        tot = 0.0
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            z, z2 = model.encoder(o[idx]), model.encoder(o2[idx])
            pred_loss = ((model.predict(z, a[idx]) - z2) ** 2).sum(-1).mean()
            reg = sigreg(torch.cat([z, z2]), generator=gen) / (2 * len(idx))
            loss = pred_loss + sigreg_weight * reg
            opt.zero_grad(); loss.backward(); opt.step()
            tot += loss.item() * len(idx)
        if log_every and (ep + 1) % log_every == 0 or ep == epochs - 1:
            with torch.no_grad():
                stats = collapse_stats(model.encoder(o[:1000]))
            history.append({"epoch": ep + 1, "loss": tot / n, **stats})
            if log_every:
                print(f"epoch {ep + 1}: loss {tot / n:.4f} rank {stats['effective_rank']:.1f}/{z_dim}")
    return {"model": model.eval(), "world": world, "history": history}


@torch.no_grad()
def probe_position(model: WorldModel, world: DotWorld, n: int = 1500) -> float:
    """R^2 of a linear map from z to the true (x, y): does the latent contain the physical state?"""
    from sklearn.linear_model import Ridge
    o, _, _, p, _, _ = world.transitions(n)
    z = model.encoder(o).numpy()
    half = n // 2
    reg = Ridge(alpha=1e-2).fit(z[:half], p[:half].numpy())
    return float(reg.score(z[half:], p[half:].numpy()))


@torch.no_grad()
def cem_plan(model: WorldModel, z0: torch.Tensor, z_goal: torch.Tensor, horizon: int = 6, samples: int = 256,
             elites: int = 32, iters: int = 4, gen: torch.Generator | None = None) -> torch.Tensor:
    """Cross-Entropy Method in latent space; returns the best action sequence (horizon, 2)."""
    mu = torch.zeros(horizon, 2)
    std = torch.full((horizon, 2), MAX_STEP)
    for _ in range(iters):
        acts = (mu + std * torch.randn(samples, horizon, 2, generator=gen)).clamp(-MAX_STEP, MAX_STEP)
        z = z0.expand(samples, -1)
        for t in range(horizon):
            z = model.predict(z, acts[:, t])
        energy = (z - z_goal).abs().sum(-1)                      # L1 distance to the goal embedding
        best = acts[energy.topk(elites, largest=False).indices]
        mu, std = best.mean(0), best.std(0) + 1e-3
    return mu


def evaluate_planning(model: WorldModel, world: DotWorld, episodes: int = 30, max_steps: int = 25, tol: float = 0.08,
                      planner: str = "cem", seed: int = 1) -> dict:
    """Success = true distance to goal < tol within max_steps. planner: cem | random | oracle (knows positions)."""
    rng = np.random.default_rng(seed)
    gen = torch.Generator().manual_seed(seed)
    succ, steps_used, final_d = [], [], []
    for _ in range(episodes):
        pos, goal = rng.uniform(0.1, 0.9, 2).astype(np.float32), rng.uniform(0.1, 0.9, 2).astype(np.float32)
        with torch.no_grad():
            zg = model.encoder(torch.tensor(world.render(goal)))
        done = False
        for t in range(max_steps):
            if planner == "cem":
                with torch.no_grad():
                    z0 = model.encoder(torch.tensor(world.render(pos)))
                act = cem_plan(model, z0, zg, gen=gen)[0].numpy()
            elif planner == "oracle":
                act = np.clip(goal - pos, -MAX_STEP, MAX_STEP)
            else:
                act = rng.uniform(-MAX_STEP, MAX_STEP, 2)
            pos = DotWorld.step(pos, act)
            if np.linalg.norm(pos - goal) < tol:
                done = True
                steps_used.append(t + 1)
                break
        succ.append(done)
        final_d.append(float(np.linalg.norm(pos - goal)))
    return {"planner": planner, "success_rate": float(np.mean(succ)), "mean_final_distance": float(np.mean(final_d)),
            "mean_steps_when_success": float(np.mean(steps_used)) if steps_used else None, "episodes": episodes}


@torch.no_grad()
def surprise_auc(model: WorldModel, world: DotWorld, n: int = 2000, teleport_rate: float = 0.1) -> dict:
    """Prediction error as an anomaly score: ROC AUC for telling teleports from normal moves."""
    from sklearn.metrics import roc_auc_score
    o, a, o2, _, _, tele = world.transitions(n, teleport_rate)
    err = ((model.predict(model.encoder(o), a) - model.encoder(o2)) ** 2).sum(-1).numpy()
    return {"auc": float(roc_auc_score(tele.numpy(), err)), "n": n, "teleports": int(tele.sum()),
            "mean_error_normal": float(err[~tele.numpy()].mean()), "mean_error_teleport": float(err[tele.numpy()].mean())}
