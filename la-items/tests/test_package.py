import importlib.resources

import la_items


def test_package_ships_the_typing_marker() -> None:
    marker = importlib.resources.files(la_items).joinpath("py.typed")

    assert marker.is_file()
