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
2. ``UModel Export Directory`` should be set to an existing folder where you will export the game assets to using
   ``UModel``.
3. ``Asset directory`` should be set to an existing directory where Blender will keep a library of assets for this game
   profile. It has to be an existing directory.

Configuring UModel (UEViewer) and extracting assets
----------------------------------------------------
When you launch UModel, you will be greated with the ``UE Viewer Startup Options`` window.

.. image:: images/umodel_welcome.png
    :width: 450


1. Point the ``Path to game files:`` option to the location of your game.
2. Enable the ``Override game detection`` checkbox.
3. Select the version of Unreal Engine and the specific game (if available) in two dropdown menus below.

   .. note::
        If a specific game is not available in the menu, you need to select the exact version of Unreal Engine this game
        was built with. This can be usually found fairly easily in the search engines. If the version is incorrect, you
        are likely to face crashes of UModel on attempt to view or export assets.
4. The rest of the settings may remain unchanged. Hit ``Okay`` to load the game in ``UE Viewer``.

Once the game is loaded, you should be able to see the ``Choose a package to open`` window with a tree view of the
game's files. We need to configure a few more things before exporting textures and models.

.. image:: images/umodel_tree.png
    :width: 450


1. Click on the ``Tools`` button in the bottom of the window.
2. Select ``Options`` in the dropdown.

The ``Options`` window should appear.

.. image:: images/umodel_options.png
    :width: 450

1. Enter the path to your export directory into the ``Export to this folder`` field. It should be the same directory as
   the one we specified in the add-on's game profile settings as ``UModel Export Directory``.
2. Make sure that both ``Skeletal Mesh`` and ``Static Mesh`` under the ``Mesh Export`` section are set to `ActorX`. The
   ``umodel_tools`` Blender add-on supports only the .psk/.pskx files as mesh assets.
3. Make sure that ``Texture format`` under ``Texture Export`` section is set to ``PNG``. Other extensions are also
   supported by the add-on, but `.png` is more reliable, and can be easily opened by various graphics software.
4. Leave all other settings unchanged (as shown on the picture), and git ``OK`` to save the settings.

As the configuration is over, it is recommended to export **the entire** game into the export folder. In order to do
that, right click on the root folder in the tree view and choose ``Export folder content``. This will bring up the
already familiar ``Export options`` window. It should be already configured properly, so just hit the ``OK`` button to
perform the export.

.. note::
    The export procedure may take a significant amount of time, be patient, it is a one-time task.
    It is normally possible to export only the ``Game`` directory, ignoring the ``Engine`` directory which can save
    some space, but this may vary from game to game and is not guaranteed to work in all the cases. However, if you want
    shorter import times or less disk space usage, you can also experiment with various UEViewer startup options.

Configuring FModel and extracting maps
----------------------------------------------------
1. Launch ``FModel``.
2. In the top menu of ``FModel`` select `Settings`. A `Settings` window should appear.

.. image:: images/fmodel_settings.png
    :width: 650

3. Set ``Output Directory`` to any directory on your PC you want ``FModel`` to export to.
4. Set ``Game's Archive Directory`` to the directory of your game.
5. Set ``UE Versions`` to the correct game profile or Unreal Engine version (if specific game is not available).
6. Hit ``Okay``, which should save the settings and restart the application.

You can now launch ``FModel`` again and export a map with it. In order to to do this, find the required map, right click
on its name in the tree view and select ``Save Properties (.json)``. This will produce a `.json` output file in the
``Output Directory``. Alternatively, you can export the entire directory by right clicking it and choosing
``Export Folder's Packages Properties (.json)`` (also applied to child directories).

.. warning::
    Some games' maps cannot be reliably exported by ``FModel``. This usually happens in case some third-party level
    building system was used by the game's developers. You can check the rough result of the state of the map to be
    exported using the FModel's builtin 3D viewer.
