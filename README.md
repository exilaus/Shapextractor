Shapextractor
====================
Is a headless 3d scanner full automated with RPI and with low cost items.
Is based from http://www.sjbaker.org/wiki/index.php?title=A_Simple_3D_Scanner.

Why i create/modify it?
I want use my RPi as 3d plattaform, printing and scanning,
 meanwile i waiting my 3d printer (www.Makibox.com) i try to create something for it.

HW needs:

- ulm2003 + 28BYJ-48 (ebay)
- 6cm diameter plate to add on stepper
- thin laser line (DX)
- webcam compatible with pygame (640x480 currently i use ps3eye and no like it too much 

sharpen)
- usb lamp ??? (is added in code but not really need if work with stable light)

SW needs:
- last Raspbian “wheezy”
- raspberry-gpio-python Release 0.5.2a

How works,
process is diveded in 3 part :
- capture (python) take photos ,manipulate it, rotate spintable , manage led&laser , generate ply
- reconstruction (c++)  , read photos and create point cloud
- html pages ready for publish (WebGL ply viewer with XB PointStream )

For start:
 start.sh
 if need web server startweb.sh

To do:
- Trace more and more clear laser line
- Set parameter via external file
- Find low cost and small webcamera supported by RPI&Pygame

Gallery :
https://plus.google.com/photos/114285476102201750422/albums/5868629874379483185

Model no tested and take little update (waiting for 3dprinter):
http://sketchup.google.com/3dwarehouse/details?mid=ef682e116c511065eee8499fa420acaa


Special thanks to:

Antonio Orlando (it make a name)
Henrik Peiss 

Sjbaker (for original code)
Tbuser  (spinscan code)

Raspberry PI

Makibox/Makible team!!!!

Mauro
exilaus@hotmail.com
