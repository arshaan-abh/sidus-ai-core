from github import GithubObject


def set_if_not_none(kwargs: dict, key: str, value):
    """
    Helper that only sets a kwarg when the value is not None,
    otherwise uses GithubObject.NotSet to avoid PyGithub assertions.
    """
    if value is not None:
        kwargs[key] = value
    else:
        kwargs[key] = GithubObject.NotSet
