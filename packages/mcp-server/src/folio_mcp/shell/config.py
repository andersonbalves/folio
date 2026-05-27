"""Dynaconf settings for the MCP server (prefix: FOLIO_MCP_*)."""

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="FOLIO_MCP",
    settings_files=["settings.yaml", ".secrets.yaml"],
    root_path="../../",  # points to monorepo root
    environments=True,
    load_dotenv=True,
)
