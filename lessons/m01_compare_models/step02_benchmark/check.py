import time


class Reply:
    def __init__(self, content):
        self.content = content


class Fixed:
    def __init__(self, answers, delay=0.0, fail_on=()):
        self.answers, self.delay, self.fail_on, self.i = answers, delay, set(fail_on), 0

    def chat(self, messages, tools=None, json_schema=None):
        i, self.i = self.i, self.i + 1
        time.sleep(self.delay)
        if i in self.fail_on:
            raise RuntimeError("boom")
        return Reply(self.answers[i % len(self.answers)])


CASES = [{"prompt": "a", "check": lambda x: x == "A"}, {"prompt": "b", "check": lambda x: x == "B"}]


def check_accuracy(m):
    """accuracy = correct / n"""
    rows = m.run_benchmark({"good": Fixed(["A", "B"]), "half": Fixed(["A", "x"])}, CASES)
    assert [r["model"] for r in rows] == ["good", "half"]
    assert rows[0]["accuracy"] == 1.0 and rows[1]["accuracy"] == 0.5 and rows[0]["n"] == 2, rows


def check_errors_do_not_stop(m):
    """an exception is counted, the run continues"""
    rows = m.run_benchmark({"flaky": Fixed(["A", "B"], fail_on={0})}, CASES)
    assert rows[0]["errors"] == 1 and rows[0]["accuracy"] == 0.5 and rows[0]["n"] == 2, rows


def check_latency_only_successes(m):
    """mean latency counts successful calls only"""
    rows = m.run_benchmark({"slow": Fixed(["A", "B"], delay=0.02)}, CASES)
    assert 0.015 < rows[0]["mean_latency_s"] < 0.2, rows
    allfail = m.run_benchmark({"dead": Fixed(["A"], fail_on={0, 1})}, CASES)
    assert allfail[0]["mean_latency_s"] is None and allfail[0]["errors"] == 2 and allfail[0]["accuracy"] == 0.0, allfail


def check_repeats(m):
    """repeats multiplies the number of calls"""
    llm = Fixed(["A", "B"])
    rows = m.run_benchmark({"x": llm}, CASES, repeats=3)
    assert rows[0]["n"] == 6 and llm.i == 6, (rows, llm.i)


def check_same_prompts_for_all(m):
    """every model gets the same user message format"""
    seen = []

    class Spy(Fixed):
        def chat(self, messages, tools=None, json_schema=None):
            seen.append(messages)
            return super().chat(messages)
    m.run_benchmark({"s": Spy(["A", "B"])}, CASES)
    assert seen == [[{"role": "user", "content": "a"}], [{"role": "user", "content": "b"}]], seen


def check_empty_cases(m):
    """no cases -> accuracy 0.0 and no crash"""
    rows = m.run_benchmark({"x": Fixed(["A"])}, [])
    assert rows[0]["n"] == 0 and rows[0]["accuracy"] == 0.0 and rows[0]["mean_latency_s"] is None, rows
