Installation
========================================

.. note::
    Before learning about the add-on's usage, make sure you have completed the :doc:`installation` and :doc:`configuration`
    parts.

``umodel_tools`` provides a few distinct features that you can use to recover 3D data from an Unreal Engine game.
This guide will go through each of them in detail.

.. note::
    Many ``umodel_tools`` operators can take a significant time to complete, depending on the amount of game 3D
    resources being converted and other factors. During these operators Blender's UI will be completely frozen
    (non-interactable). If you want to track the progress and get some estimates, you can launch Blender through command
    line (terminal / shell). The add-on will be reporting progress there using text-based progress bars.

Map import
-----------------------------------------
The add-on is able to import `.json` files, produced by ``FModel`` from Unreal Engine maps (``.umap``).

.. warning::
    It is not guaranteed that you can load the entire game level using this techique, as some of the objects are
    typically placed on the level dynamically using blueprints or C++ code in UE. The importer is only able to
    understand static data such as static mesh or light placements. However, for many games this is more than enough to
    recreate some particular scene.

In order to import a map do the following:
1. Export a map using ``FModel``. Make sure you are running a correct game profile and all of the game assets needed are
    available in the ``UModel Export Directory``.
2. In Blender, go to ``File`` -> ``Import`` -> ``Import Unreal Map``. An import dialogue should appear.
3. Select the ``.json`` file of a map that you want to import. Selecting multiple maps at once is **supported**, in
   this case, all of them will be imported into the same scene (yet, separated into different collections).
4. Make sure to configure the import settings correctly on the sidebar. The meaning of each option can be acquired by
   hovering over it.
5. Hit the ``Import Unreal Map`` button to confirm and start the import operation.


Batch asset import
------------------------------------------