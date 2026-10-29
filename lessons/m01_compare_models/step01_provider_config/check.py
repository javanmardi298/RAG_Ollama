def _raises(m, env, needle):
    try:
        m.resolve_config(env)
    except ValueError as e:
        assert needle in str(e).lower(), f"message should mention {needle!r}: {e}"
        return
    raise AssertionError(f"expected ValueError for {env}")


def check_defaults(m):
    """no environment -> offline"""
    c = m.resolve_config({})
    assert c == {"provider": "offline", "model": "", "api_base": "", "budget_usd": 0.0, "cloud": False}, c


def check_ollama_default_model(m):
    """ollama gets its default model; an explicit model wins"""
    assert m.resolve_config({"LEARN_PROVIDER": "ollama"})["model"] == "qwen2.5:7b"
    assert m.resolve_config({"LEARN_PROVIDER": "ollama", "LEARN_MODEL": "llama3.2:3b"})["model"] == "llama3.2:3b"


def check_unknown_provider(m):
    """unknown provider is an error"""
    _raises(m, {"LEARN_PROVIDER": "gpt"}, "unknown provider")


def check_opencode_needs_slash(m):
    """opencode needs provider/model"""
    _raises(m, {"LEARN_PROVIDER": "opencode"}, "provider/model")
    _raises(m, {"LEARN_PROVIDER": "opencode", "LEARN_MODEL": "claude"}, "provider/model")
    assert m.resolve_config({"LEARN_PROVIDER": "opencode", "LEARN_MODEL": "anthropic/x"})["model"] == "anthropic/x"


def check_api_base_and_key(m):
    """openai_compatible needs an api base; anthropic needs a key"""
    _raises(m, {"LEARN_PROVIDER": "openai_compatible", "LEARN_MODEL": "x"}, "api_base")
    _raises(m, {"LEARN_PROVIDER": "anthropic"}, "anthropic_api_key")
    c = m.resolve_config({"LEARN_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k"})
    assert c["cloud"] is True and c["model"] == "claude-sonnet-5-5" and "k" not in str(c["model"])


def check_budget(m):
    """budget parses to float; bad values raise"""
    assert m.resolve_config({"LEARN_BUDGET_USD": "1.5"})["budget_usd"] == 1.5
    _raises(m, {"LEARN_BUDGET_USD": "abc"}, "number")
    _raises(m, {"LEARN_BUDGET_USD": "-1"}, "negative")


def check_cloud_flag(m):
    """cloud is true only where data leaves the machine"""
    assert m.resolve_config({"LEARN_PROVIDER": "ollama"})["cloud"] is False
    assert m.resolve_config({"LEARN_PROVIDER": "openai_compatible", "LEARN_API_BASE": "http://x/v1"})["cloud"] is True
