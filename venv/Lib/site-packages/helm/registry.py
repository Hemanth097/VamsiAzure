from helm.common import helm_run


def subcommand_run(*args, **kwargs):
    return helm_run("registry", *args, **kwargs)


def login(*args, **kwargs):
    """https://helm.sh/docs/helm/helm_registry_login."""
    return subcommand_run("login", *args, **kwargs)


def logout(*args, **kwargs):
    """https://helm.sh/docs/helm/helm_registry_logout."""
    return subcommand_run("logout", *args, **kwargs)
