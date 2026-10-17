"""jepa_lab: small, CPU-friendly JEPA experiments for learning the ideas hands-on (docs/jepa.md has the tutorial).

    ssl.py          I-JEPA-style masked latent prediction on 8x8 digit images (sklearn, no download);
                    variants: ema (I-JEPA teacher), sigreg (LeJEPA, no teacher), naive (collapses), pixel (MAE-like)
    sigreg.py       SIGReg: push embeddings towards an isotropic Gaussian (LeJEPA), plus collapse diagnostics
    world_model.py  a toy 2D world: learn an action-conditioned latent world model (LeWorldModel / V-JEPA 2-AC idea),
                    plan with CEM + MPC in latent space, detect "surprising" transitions from prediction error

Needs PyTorch (pip install torch). Everything runs on a laptop CPU in minutes.
"""
