import pkg_resources


def get_version() -> str:
    return pkg_resources.require(__name__)[0].version
