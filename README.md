# umodel_tools
![PyLint](https://github.com/skarndev/umodel_tools/actions/workflows/pylint.yml/badge.svg)
Blender addon featuring static mesh import from UModel (UE Viewer) with materials and reverse engineering of 3D ripped UE scenes.

# Building
The addon requires a set of extra dependencies, which can be automatically paked into the distribution by a build script. In order to make a distribution, launch the ``build.py`` script with ``--dist [path/to/your/dist]`` argument. Your Python interpreter must have pip installed. 

# Installation
A packed addon distribution can be installed like a regular [Blender addon](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html).

# Requirements
- Blender 3.4 is required to run the tool.
- [UEViewer (UModel)](https://www.gildor.org/en/projects/umodel) version capable of opening and extracting the files of your target game. 
- Blender 2.8+ version of the [PSK import plugin](https://github.com/Befzz/blender3d_import_psk_psa). It must be installed and enabled in your Blender, in order for umodel_tools to work correctly.

# Usage
After enabling umodel_tools, enter path to UEViewer export directory in your scene properties tab. You also need to specify an arbitrary asset library directory which can be any directory you want umodel_tools to save converted meshes, materials and textures into.

The addon features two operators, located in the Object dropdown menu: 
- Recover Unreal assest
  
  1. Find an asset in UEViewer.
  2. Export the asset by right-clicking on it, and choosing ``Export`` in the context menu. Make sure your UEViewer is configured to output .pskx files, and not .gltf.
  3. Right-click the asset in UEViewer and select the ``Copy package path`` option. This will copy the path of the asset into your clipboard.
  4. In Blender, open the ``Object`` dropdown menu, select ``Recover Unreal asset``. In the pop-up Window specify the texture settings, and whether you want PBR materials or not. If the PBR option is selected, the importer will attempt to reconstruct Unreal materials using normal maps, SRO (specular/roughness/ambient occlusion) or MROH (metallic/roughness/ambient occlusion/height) maps. Otherwise, only the Diffuse map will be used.
  5. 
      - If nothing was selected, the addon will import the mesh to a 3D cursor position. 
      - If any objects were selected, it will try to replace them with copies of the imported mesh. The latter feature is useful for recovering placement information of objects on the scene produced by 3D ripper tools (such as [NinjaRipper](https://ninjaripper.com)). It can only work if the number of vertices of the original asset matches the number of vertices of the ripped mesh, otherwise a borked result is to be expected.

- Realign Unreal asset
  1. Roughly align the imported assset next to the ripped mesh, so that they are rotations are roughly similar.
  2. Select the imported asset and the ripped mesh.
  3. Run ``Realign Unreal asset`` operator in the ``Object`` dropdown menu. The ripped mesh will be hidden, and the imported mesh will be moved to its position, retaining correct world transformation.

# Notes
1. The assets are stored in the asset library and linked to the Blender scene from it. umodel_tools also maintains the categorization of the asset, so that they work in Blender's [asset browser](https://docs.blender.org/manual/en/latest/editors/asset_browser.html). Currently previews for assets are not generated due to Blender's crash of unknown origin when doing so.
2. The alignment functionality of the addon cannot produce good results on meshes whose vertices are all co-planar (flat plane-like meshes). No checks performed regarding this issue. 

# Games
This addon was tested on the following games:
  - Atomic Heart
  - Hogwarts Legacy

In theory, any game capable of being opened by the UEViewer should be compatible. However, some adjustments may need to be done to the material generation code based on game's specifics. 

# Disclaimer
3D assets used by most of the games are copyrighted property of game's owners. This software does not promote asset piracy and is intended for artistic and research purposes only.
