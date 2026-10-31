import numpy as np

from triage import choose_threshold, ece, load_tickets, predict, random_split, scores, selective, split, train


def test_split_has_no_template_in_two_places():
    tr, dev, test = split(load_tickets())
    sets = [{t["template"] for t in part} for part in (tr, dev, test)]
    assert not (sets[0] & sets[1]) and not (sets[0] & sets[2]) and not (sets[1] & sets[2])


def test_random_split_looks_better_than_it_is():
    tickets = load_tickets()
    honest = split(tickets)
    leaky = random_split(tickets)
    acc = lambda parts: scores(parts[2], predict(train(parts[0]), parts[2])[0])["accuracy"]  # noqa: E731
    assert acc(leaky) >= acc(honest)


def test_ece_and_selective_decision():
    assert ece([1, 1, 0, 0], [0.9, 0.9, 0.1, 0.1]) < ece([1, 1, 0, 0], [0.9, 0.9, 0.9, 0.9])
    correct, conf = np.array([1, 1, 1, 0]), np.array([0.95, 0.9, 0.8, 0.5])
    th = choose_threshold(correct, conf, 0.95, min_auto=1)
    assert th == 0.8 and selective(correct, conf, th) == {"threshold": 0.8, "coverage": 0.75, "accuracy_automated": 1.0, "to_human": 1}
    assert choose_threshold(np.array([0, 0]), np.array([0.9, 0.8]), min_auto=1) > 1


def test_model_learns():
    tr, dev, _ = split(load_tickets())
    assert scores(dev, predict(train(tr), dev)[0])["accuracy"] > 0.6
