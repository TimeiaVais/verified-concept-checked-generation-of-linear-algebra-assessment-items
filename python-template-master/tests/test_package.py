import importlib.resources

import python_template


def test_package_ships_the_typing_marker() -> None:
    marker = importlib.resources.files(python_template).joinpath("py.typed")

    assert marker.is_file()
