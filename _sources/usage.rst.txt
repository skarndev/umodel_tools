Usage
========================================

.. note::
    Before learning about the add-on's usage, make sure you have completed the :doc:`installation` and
    :doc:`configuration` parts.

``umodel_tools`` provides a few distinct features that you can use to recover 3D data from an Unreal Engine game.
This guide will go through each of them in detail.

.. note::
    Many ``umodel_tools`` operators can take a significant time to complete, depending on the amount of game 3D
    resources being converted and other factors. During these operators Blender's UI will be completely frozen
    (non-interactable). If you want to track the progress and get some estimates, you can launch Blender through command
    line (terminal / shell). The add-on will be reporting progress there using text-based progress bars.

Map import
-----------------------------------------
The add-on is able to import ``.json`` files, produced by ``FModel`` from Unreal Engine maps (``.umap``).

.. warning::
    It is not guaranteed that you can load the entire game level using this techique, as some of the objects are
    typically placed on the level dynamically using blueprints or C++ code in UE. The importer is only able to
    understand static data such as static mesh or light placements. However, for many games this is more than enough to
    recreate some particular scene.

In order to import a map do the following:

1. Export a map using ``FModel``. Make sure you are running a correct game profile and all of the game assets needed are
   available in the ``UModel Export Directory``.
2. In Blender, go to ``File`` -> ``Import`` -> ``Import Unreal Map``. An import dialogue should appear.
3. Select the ``.json`` file of a map that you want to import. Selecting multiple maps at once is **supported**, in this
   case, all of them will be imported into the same scene (yet, separated into different collections).
4. Make sure to configure the import settings correctly on the sidebar. The meaning of each option can be acquired by
   hovering over it.
5. Hit the ``Import Unreal Map`` button to confirm and start the import operation.


Batch asset import
------------------------------------------
The add-on is able to import multiple game assets at once. You can even convert the entirery of game assets into a
reusable asset database in one run. Unlike the map importer operator, this operator is located in Blender's ``Object``
menu, typically located at the top of the viewport.

1. In order to batch import Unreal Engine models into Blender, go to ``Object`` menu and select
   ``Import Unreal Assets``. An operator settings prompt should appear.
2. The settings are similar to map import, with the exception of ``Asset subdir``. It indicates the subdirectory within
   the game's file tree we want to import assets from. ``/`` would indicate root directory, which means importing
   **all** the assets. ``/Game/Environment/`` would indicate that only the assets located in that subdirectory will be
   imported.

.. note::
    Depending on the scope of the batch import and various other factors this operation may take a significant amount of
    time.

.. note::
    Assets imported with any operation are marked as Blender assets. The add-on automatically takes care of adding the
    files into the ``.cats.txt`` file which preserves the directory tree in the asset browser. In order to see the
    assets in the asset browser, make sure to set the value of current profile's ``Asset directory`` parameter as an
    asset search path (``Edit`` -> ``Preferences`` -> ``File Paths`` -> ``Asset Libraries`` -> ``Add Asset Library``).
    For now the assets do not have their previews generated automatically. You can use
    `this addon <https://github.com/Gorgious56/asset_browser_utilities>`_ to batch generate them.