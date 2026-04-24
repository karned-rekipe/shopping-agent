from main import _make_mcp_runner, arclith

if __name__ == "__main__":
  arclith.run_with_probes(_make_mcp_runner("mcp_sse"), transports=["mcp_sse"])
