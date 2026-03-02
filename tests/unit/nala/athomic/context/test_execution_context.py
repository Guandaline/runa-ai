from nala.athomic.context import ExecutionContext, context_vars


def test_default_context_uses_context_vars(monkeypatch):
    monkeypatch.setattr(context_vars, "get_tenant_id", lambda: "tenant-A")
    monkeypatch.setattr(context_vars, "get_request_id", lambda: "req-123")
    monkeypatch.setattr(context_vars, "get_trace_id", lambda: "trace-xyz")
    monkeypatch.setattr(context_vars, "get_span_id", lambda: "span-001")
    monkeypatch.setattr(context_vars, "get_user_id", lambda: "user-007")
    monkeypatch.setattr(context_vars, "get_role", lambda: "admin")
    monkeypatch.setattr(context_vars, "get_locale", lambda: "en-US")
    monkeypatch.setattr(context_vars, "get_source_ip", lambda: "192.168.0.1")
    monkeypatch.setattr(context_vars, "get_session_id", lambda: "sess-abc")
    monkeypatch.setattr(context_vars, "get_correlation_id", lambda: "corr-xyz")
    monkeypatch.setattr(context_vars, "get_feature_flags", lambda: {"new_ui": True})

    ctx = ExecutionContext()
    ctx_dict = ctx.to_dict()

    assert ctx_dict["tenant_id"] == "tenant-A"
    assert ctx_dict["request_id"] == "req-123"
    assert ctx_dict["trace_id"] == "trace-xyz"
    assert ctx_dict["span_id"] == "span-001"
    assert ctx_dict["user_id"] == "user-007"
    assert ctx_dict["role"] == "admin"
    assert ctx_dict["locale"] == "en-US"
    assert ctx_dict["source_ip"] == "192.168.0.1"
    assert ctx_dict["session_id"] == "sess-abc"
    assert ctx_dict["correlation_id"] == "corr-xyz"
    assert ctx_dict["feature_flags"]["new_ui"] is True


def test_explicit_context_overrides_context_vars():
    ctx = ExecutionContext(
        tenant_id="X",
        request_id="R",
        trace_id="T",
        span_id="S",
        user_id="U",
        role="admin",
        locale="pt-BR",
        source_ip="127.0.0.1",
        session_id="SID",
        correlation_id="CID",
        feature_flags={"beta": True},
    )

    assert ctx.tenant_id == "X"
    assert ctx.request_id == "R"
    assert ctx.trace_id == "T"
    assert ctx.span_id == "S"
    assert ctx.user_id == "U"
    assert ctx.role == "admin"
    assert ctx.locale == "pt-BR"
    assert ctx.source_ip == "127.0.0.1"
    assert ctx.session_id == "SID"
    assert ctx.correlation_id == "CID"
    assert ctx.feature_flags == {"beta": True}
