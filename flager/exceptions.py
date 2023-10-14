class BaseError(Exception):
    pass


class FeatureFlagNotFound(BaseError):
    pass


class FeatureFlagNotDefined(BaseError):
    pass
