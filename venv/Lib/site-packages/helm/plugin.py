from .common import helm_run


def subcommand_run(*args, **kwargs):
    return helm_run("plugin", *args, **kwargs)


def install(*args, **kwargs):
    return subcommand_run("install", *args, **kwargs)


def list(*args, **kwargs):
    return subcommand_run("list", *args, **kwargs)


def uninstall(*args, **kwargs):
    return subcommand_run("uninstall", *args, **kwargs)


def update(*args, **kwargs):
    return subcommand_run("update", *args, **kwargs)
