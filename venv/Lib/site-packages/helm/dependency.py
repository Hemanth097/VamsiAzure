from .common import helm_run


def subcommand_run(*args, **kwargs):
    return helm_run("dependency", *args, **kwargs)


def build(*args, **kwargs):
    """https://helm.sh/docs/helm/helm_dependency_build."""
    return subcommand_run("build", *args, **kwargs)


def list(*args, **kwargs):
    """https://helm.sh/docs/helm/helm_dependency_list."""
    return subcommand_run("list", *args, **kwargs)


def update(*args, **kwargs):
    """https://helm.sh/docs/helm/helm_dependency_update."""
    return subcommand_run("update", *args, **kwargs)
