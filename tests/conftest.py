import pytest


def pytest_addoption(parser):
    parser.addoption("--run-db", action="store_true", help="Run PostgreSQL integration tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-db"):
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Use --run-db with migrated PostgreSQL"))


@pytest.fixture
def anyio_backend():
    return "asyncio"
