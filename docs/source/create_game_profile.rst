Creating a game profile
========================================

In order to provide dedicated support for any game, you need to implement a game profile Python module.
These modules are located in ``umodel_tools/game_profiles`` directory in the source code tree. The modules are fetched
automatically on add-on's loading with basic validation performed.

Game support steps
----------------------------------------
1. Create a ``.py`` file in the ``umodel_tools/game_profiles`` which will be your game profile script (e.g. my_game.py).
2. Inside the file, define ``GAME_NAME`` and ``GAME_DESCRIPTION`` constants. These strings will be used in the add-on's
   UI.
3. Implement **all** functions defined in the ``GameHandler`` protocol, which you can find in the
   ``umodel_tools/__init__.py`` file. The functions should be implemented as free-standing functions, not methods.


Game profile API
----------------------------------------
.. automodule:: umodel_tools.game_profiles.__init__
    :members: