REQUIRES = ["torch"]


def _t():
    import torch
    return torch


def check_loss_only_on_hidden(m):
    """visible patches do not contribute to the loss"""
    torch = _t()
    pred, target = torch.zeros(1, 4, 2), torch.zeros(1, 4, 2)
    target[0, 0] = 100.0                                   # a huge error on a VISIBLE patch
    keep = torch.tensor([[True, True, False, False]])
    assert float(m.masked_latent_loss(pred, target, keep)) == 0.0, "the visible patch leaked into the loss"


def check_loss_value(m):
    """smooth L1 over hidden patches"""
    torch = _t()
    pred, target = torch.zeros(1, 2, 1), torch.tensor([[[0.5], [3.0]]])
    keep = torch.tensor([[False, False]])
    # smooth_l1: 0.5*0.5^2 = 0.125 for |e|=0.5 ; |e|-0.5 = 2.5 for |e|=3
    assert abs(float(m.masked_latent_loss(pred, target, keep)) - (0.125 + 2.5) / 2) < 1e-6


def check_loss_without_hidden(m):
    """nothing hidden -> zero, not NaN"""
    torch = _t()
    x = torch.randn(2, 3, 4, requires_grad=True)
    out = m.masked_latent_loss(x, torch.randn(2, 3, 4), torch.ones(2, 3, dtype=torch.bool))
    assert float(out) == 0.0 and not torch.isnan(out), out
    out.backward()


def check_loss_has_gradient(m):
    """gradient flows to the prediction"""
    torch = _t()
    pred = torch.randn(2, 4, 3, requires_grad=True)
    m.masked_latent_loss(pred, torch.randn(2, 4, 3), torch.tensor([[True, True, False, False]] * 2)).backward()
    assert pred.grad is not None and pred.grad[:, 2:].abs().sum() > 0 and pred.grad[:, :2].abs().sum() == 0


def check_ema_formula(m):
    """teacher = m*teacher + (1-m)*student"""
    torch = _t()
    t, s = torch.nn.Linear(1, 1, bias=False), torch.nn.Linear(1, 1, bias=False)
    t.weight.data.fill_(1.0)
    s.weight.data.fill_(3.0)
    m.ema_update(t, s, 0.75)
    assert abs(float(t.weight) - (0.75 * 1.0 + 0.25 * 3.0)) < 1e-6, float(t.weight)


def check_ema_no_grad_and_student_untouched(m):
    """the teacher gets no gradient history and the student does not change"""
    torch = _t()
    t, s = torch.nn.Linear(2, 2), torch.nn.Linear(2, 2)
    before = s.weight.clone()
    m.ema_update(t, s, 0.9)
    assert torch.equal(s.weight, before), "student was modified"
    assert t.weight.requires_grad and t.weight.grad_fn is None, "teacher weights must stay plain leaf parameters"
