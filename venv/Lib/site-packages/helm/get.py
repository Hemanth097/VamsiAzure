from typing import Iterable

import yaml

from .common import helm_run


def subcommand_run(*args, **kwargs):
    return helm_run("get", *args, **kwargs)


def all(*args, **kwargs) -> str:
    """https://helm.sh/docs/helm/helm_get_all."""
    data = subcommand_run("all", *args, **kwargs).stdout
    return data


def hooks(release: str, *args, **kwargs) -> Iterable[dict]:
    """https://helm.sh/docs/helm/helm_get_hooks."""
    data = subcommand_run("hooks", release, *args, **kwargs).stdout
    return yaml.safe_load_all(data)


def manifest(release: str, *args, **kwargs) -> Iterable[dict]:
    """https://helm.sh/docs/helm/helm_get_manifest."""
    data = subcommand_run("manifest", release, *args, **kwargs).stdout
    return yaml.safe_load_all(data)


def notes(release: str, *args, **kwargs):
    """https://helm.sh/docs/helm/helm_get_notes."""
    return subcommand_run("notes", release, *args, **kwargs)


def values(release: str, *args, **kwargs) -> dict:
    """https://helm.sh/docs/helm/helm_get_values."""
    data = subcommand_run("values", release, *args, **kwargs).stdout
    return yaml.safe_load(data)
