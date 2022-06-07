At BCN3D we work to provide customers with better solutions, especially those with advanced manufacturing needs within the 3D printing industry. Over the past year, our engineers have been hard at work on our latest passion project, putting their heart and soul into matching the high performance of our printers with an upgraded software tool to significantly improve the printing process of our users.

BCN3D Stratos is a straightforward slicing software, designed for speed and efficiency while still ensuring top-quality prints for a powerful 3D printing process. The user-friendly interface is free and compatible with all BCN3D Sigma and Epsilon printers.

BCN3D Stratos is based on the open source project Ultimaker/Cura developed by Ultimaker B.V. in cooperation with the community.

![Stratos](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-1-600x329.jpg)


# What’s new?
## IDEX reaches its full potential
BCN3D Stratos easily incorporates the benefits of the IDEX system: simply merge multi-material models, generate support structures or even cut down printing times by combining hotends with different nozzle sizes.

![IDEX](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-2.jpg)

## New user interface
The new BCN3D Stratos features a new user interface that streamlines the slicing experience for both casual and advanced users.

![New user interface](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-3-600x329.jpg)


## Format file flexibility
Importing your files to Stratos is intuitive and stress-free. Upload files of a broad range of formats swiftly through ways such as clicking on the folder icon to browse files, and dragging and dropping directly.



## Mirror and duplication modes
With a user-friendly tool and customizable settings, make use of the unique feature of controlling two print heads to double your productivity. It's now easier than ever to make the most of IDEX technology.

![Mirror and duplication modes](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-5.jpg)



## Integrated printing profiles
BCN3D Stratos works using validated printing profiles to increase the printing success rate. Just select the installed hotends and materials on the printer to get the right set of parameters. And, of course, expert users can still tweak more than 500 parameters.

![Integrated printing profiles](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-6-600x318.jpg)



## New settings panel
You can now drag the settings panel and position it anywhere on your screen. Simply double-click the header and the settings panel will return to the default position.




## Orthographic and perspective cameras
You can now choose between orthographic and perspective camera views in BCN3D Stratos, allowing you to review your models the way you want.



## Object list
If you want to print multiple parts at the same time on the large build plate of the BCN3D Epsilon, the object list will save you time. The object list helps you easily identify models on your build plate based on their filename.

![Objects list](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-9.gif)


## Align face to build plate
Orient complex models by simply selecting a face of it to rest on the build plate.

![Align face to build plate](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-10-600x338.gif)


## Infill options
New infill options are available on BCN3D Stratos. With the new Gyroid infill, you can create lightweight parts with high resistance.

![Infill options](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-11.jpg)


## Remote printing connection
Add a cloud printer and send your sliced models directly to your Sigma or Epsilon 3D printers through BCN3D Stratos.

## Visualization options
After slicing, Stratos offers a variety of preview types to ensure pinpoint accuracy. While Layer View provides visualization of each section of your print, X-ray View reveals internal parts and hidden geometries. Change the color scheme to examine every detail of travels, helpers, shell, and infill settings.

![Visualization options](https://www.bcn3d.com/wp-content/uploads/2021/07/Image-12-1-600x318.jpg)

# Development
## Translation files
To convert .po files to .mo, run this in the root of /Stratos-intern and copy the generated resources/i18n folder in the same place where Stratos keep the .po files (Stratos-internt/resources/i18n) keeping the existing .po files.

* You need to have a folder named **Uranium** containing the Uranium-Stratos repository at the same level as this repository.

```shell
mkdir build && cd build
cmake ..
make
```

