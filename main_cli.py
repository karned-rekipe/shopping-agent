import typer

from main import _make_api_runner, _make_mcp_runner, arclith, build_mcp_server

app = typer.Typer(help="Outils de lancement du shopping agent.")


@app.command()
def api() -> None:
  arclith.run_with_probes(_make_api_runner(), transports=["api"])


@app.command("mcp-http")
def mcp_http() -> None:
  arclith.run_with_probes(_make_mcp_runner("mcp_http"), transports=["mcp_http"])


@app.command("mcp-sse")
def mcp_sse() -> None:
  arclith.run_with_probes(_make_mcp_runner("mcp_sse"), transports=["mcp_sse"])


@app.command("mcp-stdio")
def mcp_stdio() -> None:
  arclith.run_mcp_stdio(build_mcp_server("mcp_stdio"))


if __name__ == "__main__":
  app()
