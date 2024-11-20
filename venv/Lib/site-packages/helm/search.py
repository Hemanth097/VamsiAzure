from typing import List, Optional

import pydantic

from helm.common import helm_run
from helm.models import HelmChartInfo


def subcommand_run(*args, **kwargs):
    return helm_run("search", *args, **kwargs)


def hub(*args, **kwargs) -> List[HelmChartInfo]:
    """https://helm.sh/docs/helm/helm_search_hub/."""
    data = subcommand_run("hub", *args, "-o", "json", **kwargs).stdout

    return pydantic.TypeAdapter(List[HelmChartInfo]).validate_json(data or "[]")


def repo(keyword: Optional[str] = None, *args, **kwargs) -> List[HelmChartInfo]:
    """https://helm.sh/docs/helm/helm_search_repo."""
    data = subcommand_run("repo", keyword, *args, "-o", "json", **kwargs).stdout
    return pydantic.TypeAdapter(List[HelmChartInfo]).validate_json(data or "[]")
