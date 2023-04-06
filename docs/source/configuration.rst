Configuration
========================================

Configuring the add-on
----------------------------------------

After enabling the addon, you should be able to access its settings. ``umodel_tools`` supports
multiple game profiles. A ``game profile`` is a set of game-specific settings such as ``UE Viewer`` export directory and
asset library. Game profiles are required for the correct import of material node trees with respect to the
game-specific Unreal Engine materials.

In order to add a game profile, you can use the ``+`` and ``-`` buttons in the profile list. You can name your profile
with an arbitrary name by double clicking it in the list. The currently selected profile determines the currently active
profile.

1. Inside of the profile settings you need to specify the ``Game`` parameter with the Unreal Engine game you want to
   import the assets or maps from. If the game is not available in the dropdown menu, you can try the ``Generic`` entry
   which can attempt to approximate material generation for any game. In case the result of the ``Generic`` algorithm
   happens to be unfavorable, you can :doc:`implement the game handler yourself <create_game_profile>` or request a game
   to be supported by creating `an issue <https://github.com/skarndev/umodel_tools/issues>`_. See the list of
   :doc:`supported games <supported_games>`.

2. 

