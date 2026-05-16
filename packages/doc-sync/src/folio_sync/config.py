from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="FOLIO_SYNC",
    settings_files=["settings.yaml", ".secrets.yaml"],
    root_path="../../",  # points to monorepo root
    environments=True,
    load_dotenv=True,
)
