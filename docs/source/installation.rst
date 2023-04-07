Installation
========================================
In order to install ``umodel_tools`` you need to perform a few steps depending on the chosen type of installation.

Installing a pre-packed distribution
-----------------------------------------
A pre-packed distribution includes all the addon dependencies and does not require any extra building steps to be
performed on it. It is installed as a regular Blender
`add-on <https://docs.blender.org/manual/en/latest/editors/preferences/addons.html>`_.

.. note::
    Blender 3.4 or newer is required for the add-on to run.

1. Download a release distribution from the `releases <https://github.com/skarndev/umodel_tools/releases>`_ page.
2. Install the addon.

Installing from .zip archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. In Blender, go to ``Edit -> Preferences... -> Add-ons -> Install``.
2. In the file dialog window select the addon's .zip archive.
3. Search ``umodel_tools`` in the search field, and enable the add-on.

Installing manually
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Go to Blender add-on installation directory. On Windows, it is normally located at
   ``C:\Users\{$User}\AppData\Roaming\Blender Foundation\{$BlenderVersion}\scripts\addons\``,
   on Mac or Linux you can find it at ``/home/{$User}/.config/blender/{$BlenderVersion}/scripts/addons/``.
   If it does not exist, create it.

2. Copy the contents of the released distribution into the ``addons`` directory.
3. In Blender, go to ``Edit -> Preferences... -> Add-ons``, click the reload button.
4. Search ``umodel_tools`` in the search field, and enable the add-on.

Installing from sources
-----------------------------------------
You may want to install the addon from sources if you plan to alter the code, e.g. for developing game support scripts.

1. Install `python3 <https://www.python.org>`_ into your system, if you do not have it.
   It is recommended to use the same version of the interpreter as Blender's in-built one.
   In order to find out the version of Python in Blender, open the Python console (Shift + F4).
   The version of Python will be printed as the first row.ddd
2. Make sure `pip <https://pip.pypa.io/en/stable/getting-started/>`_ is installed.
3. Install `git <https://git-scm.com>`_ into your system, if you do not have it.
4. Clone the repo with ``git clone https://github.com/skarndev/umodel_tools.git``.
5. ``cd umodel_tools``
6. Run the build script with ``python build.py`` or ``python3 build.py``.
7. Create a symbolic link
   (`Windows
   <https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/mklink?source=recommendations>`_,
   `Linux / Mac <https://en.wikipedia.org/wiki/Ln_(Unix)>`_) of the ``umodel_tools/umodel_tools`` directory to the
   Blender add-on directory.
8. After the installation is complete, you should be able to see the addon in the installed add-ons list. Enable it.

Installing UEViewer (UModel)
-----------------------------------------
``UEViewer`` is used by the addon to extract the Unreal Engine games' assets such as 3D models, textures and materials
which can later be imported into Blender by ``umodel_tools``.

The official version of UEViewer can be downloaded from
`Gildor's website <https://www.gildor.org/en/projects/umodel#files>`_.
Some newer games require ACL support to be opened by UEViewer, which has not yet made it into the official release.
You can download the ACL-capable build of UEViewer from
`this thread <https://www.gildor.org/smf/index.php/topic,8304.msg43604.html#msg43604>`_. Install the tool somewhere on
your PC.

Installing FModel
-----------------------------------------
``FModel`` is another game exploration software which is capable of extracting Unreal Engine games maps. You need to
install it only if you want to import entire maps into Blender. It can be downloaded from their
`website <https://fmodel.app>`_. Install the tool somewhere on your PC.

.. warning::
    FModel does not work on Linux or Mac, even through Wine. It is essential for importing maps. If you want to import
    maps, you need to use Windows or ask somebody on Windows to export them for you.

