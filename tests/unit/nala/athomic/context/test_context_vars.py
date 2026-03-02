from nala.athomic.context import context_vars as ctx


def test_set_and_get_request_id():
    ctx.set_request_id("req-123")
    assert ctx.get_request_id() == "req-123"


def test_clear_request_id():
    ctx.set_request_id("req-123")
    ctx.clear_request_id()
    assert ctx.get_request_id() is None


def test_set_and_get_trace_id():
    ctx.set_trace_id("trace-abc")
    assert ctx.get_trace_id() == "trace-abc"


def test_clear_trace_id():
    ctx.set_trace_id("trace-abc")
    ctx.clear_trace_id()
    assert ctx.get_trace_id() is None


def test_set_and_get_tenant_id():
    ctx.set_tenant_id("tenant-42")
    assert ctx.get_tenant_id() == "tenant-42"


def test_clear_tenant_id():
    ctx.set_tenant_id("tenant-42")
    ctx.clear_tenant_id()
    assert ctx.get_tenant_id() is None


def test_set_and_get_user_id():
    ctx.set_user_id("user-007")
    assert ctx.get_user_id() == "user-007"


def test_clear_user_id():
    ctx.set_user_id("user-007")
    ctx.clear_user_id()
    assert ctx.get_user_id() is None


def test_set_and_get_role():
    ctx.set_role("admin")
    assert ctx.get_role() == "admin"


def test_clear_role():
    ctx.set_role("admin")
    ctx.clear_role()
    assert ctx.get_role() is None


def test_set_and_get_locale():
    ctx.set_locale("en-US")
    assert ctx.get_locale() == "en-US"


def test_clear_locale():
    ctx.set_locale("en-US")
    ctx.clear_locale()
    assert ctx.get_locale() == "pt-BR"


def test_set_and_get_source_ip():
    ctx.set_source_ip("192.168.0.1")
    assert ctx.get_source_ip() == "192.168.0.1"


def test_clear_source_ip():
    ctx.set_source_ip("192.168.0.1")
    ctx.clear_source_ip()
    assert ctx.get_source_ip() is None


def test_set_and_get_session_id():
    ctx.set_session_id("sess-xyz")
    assert ctx.get_session_id() == "sess-xyz"


def test_clear_session_id():
    ctx.set_session_id("sess-xyz")
    ctx.clear_session_id()
    assert ctx.get_session_id() is None


def test_set_and_get_correlation_id():
    ctx.set_correlation_id("corr-789")
    assert ctx.get_correlation_id() == "corr-789"


def test_clear_correlation_id():
    ctx.set_correlation_id("corr-789")
    ctx.clear_correlation_id()
    assert ctx.get_correlation_id() is None


def test_set_and_get_feature_flags():
    flags = {"beta_ui": True, "new_flow": False}
    ctx.set_feature_flags(flags)
    result = ctx.get_feature_flags()
    assert result == flags


def test_clear_feature_flags():
    ctx.set_feature_flags({"flag": True})
    ctx.clear_feature_flags()
    assert ctx.get_feature_flags() == {}


def test_get_current_context_contains_all_keys():
    ctx.set_tenant_id("t1")
    ctx.set_user_id("u1")
    ctx.set_locale("pt-BR")
    ctx.set_feature_flags({"flag": True})

    context = ctx.get_current_context_dic()
    expected_keys = {
        "tenant_id",
        "request_id",
        "trace_id",
        "span_id",
        "user_id",
        "role",
        "locale",
        "source_ip",
        "session_id",
        "correlation_id",
        "feature_flags",
    }
    assert expected_keys.issubset(context.keys())
    assert context["tenant_id"] == "t1"
    assert context["locale"] == "pt-BR"
    assert context["feature_flags"]["flag"] is True


def test_clear_all_context_resets_defaults():
    ctx.set_request_id("r1")
    ctx.set_trace_id("t1")
    ctx.set_locale("en-US")
    ctx.set_feature_flags({"exp": True})

    ctx.clear_all_context()

    assert ctx.get_request_id() is None
    assert ctx.get_trace_id() is None
    assert ctx.get_locale() == "pt-BR"
    assert ctx.get_feature_flags() == {}
