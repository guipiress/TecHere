class CategoryNotFoundError(Exception):
    pass


class ProductConstraintError(Exception):
    pass


class UserEmailAlreadyExistsError(Exception):
    pass


class UserCPFAlreadyExistsError(Exception):
    pass


class OrderConstraintError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass