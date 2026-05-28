"""Dynaconf settings for the doc-sync service (prefix: FOLIO_*)."""

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="FOLIO",
    settings_files=["settings.yaml", ".secrets.yaml"],
    environments=True,
    load_dotenv=True,
)
