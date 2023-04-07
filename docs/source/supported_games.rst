Supported games
========================================

.. note::
    If the game is not on this list, it is still worth a try. See below.

This page describes the state of specific game support in the ``umodel_tools`` add-on. If the game is not on the list,
you can :doc:`implement the game handler yourself <create_game_profile>` or request a game to be supported by creating
`an issue <https://github.com/skarndev/umodel_tools/issues>`_. If the game is not on the list, it is possible to attempt
loading it using the approximated ``Generic`` algorithm, see :doc:`configuration`.

The map (.umap) files of some games cannot be reliably exported through ``FModel``, and some games require the ACL
support in order to be opened by ``UModel (UEViewer)``, see :doc:`installation` for that. This kind of specifics is
reflected in the table below.


.. list-table:: List of officially supported games
   :widths: 20 10 10 50 10
   :header-rows: 1

   * - Game
     - UModel support
     - FModel support
     - Comment
     - Status
   * - `Hogwarts Legacy by Portkey Games (2023) <https://www.hogwartslegacy.com/en-us>`_
     - ACL
     - Yes
     - The maps and assets are consistently imported. Blended materials are not currently imported correctly.
       Some dynamic interactive object placements are not imported.
     - Gold