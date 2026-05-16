from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="FOLIO_MCP",
    settings_files=["settings.yaml", ".secrets.yaml"],
    root_path="../../",  # aponta pra raiz do monorepo
    environments=True,
    load_dotenv=True,
)
