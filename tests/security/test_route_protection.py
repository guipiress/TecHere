"""Safety net: no route may become reachable without authentication by accident.

The test walks the real FastAPI route table, so a new endpoint that forgets
its Depends(...) fails here instead of shipping open.
"""

from fastapi.routing import APIRoute

from backend.app.dependencies import get_current_user
from backend.app.main import app

# Everything NOT listed here must depend on get_current_user (directly or
# through require_roles / require_staff / require_admin).
PUBLIC_ROUTES = {
    ("GET", "/"),
    ("POST", "/auth/login"),
    ("POST", "/users"),             # public sign-up (role is always CUSTOMER)
    ("GET", "/products"),           # public catalogue
    ("GET", "/products/{id}"),
    ("GET", "/categories"),
    ("GET", "/categories/{id}"),
}


def _dependency_calls(dependant):
    for sub in dependant.dependencies:
        yield sub.call
        yield from _dependency_calls(sub)


def _all_routes():
    def walk(routes, prefix=""):
        for route in routes:
            if isinstance(route, APIRoute):
                for method in route.methods - {"HEAD", "OPTIONS"}:
                    yield method, prefix + route.path, route

            elif (
                hasattr(route, "original_router")
                and hasattr(route, "include_context")
            ):
                context = route.include_context

                yield from walk(
                    route.original_router.routes,
                    prefix + context.prefix,
                )

    yield from walk(app.routes)


def test_every_route_requires_authentication_unless_explicitly_public():
    unprotected = [
        f"{method} {path}"
        for method, path, route in _all_routes()
        if (method, path) not in PUBLIC_ROUTES
        and get_current_user not in set(_dependency_calls(route.dependant))
    ]

    assert not unprotected, (
        "These routes are reachable without authentication: "
        + ", ".join(sorted(unprotected))
    )


def test_public_route_list_has_no_stale_entries():
    existing = {(method, path) for method, path, _ in _all_routes()}

    assert PUBLIC_ROUTES <= existing, (
        "Remove from PUBLIC_ROUTES: "
        + ", ".join(sorted(f"{m} {p}" for m, p in PUBLIC_ROUTES - existing))
    )


def test_public_routes_are_read_only_except_login_and_signup():
    mutating = {
        (method, path)
        for method, path in PUBLIC_ROUTES
        if method not in {"GET"}
    }

    assert mutating == {("POST", "/auth/login"), ("POST", "/users")}
