import cgi
import cgitb; cgitb.enable()
import compileall
import subprocess
import RPi.GPIO as gpio 
import time
import os 
import binascii
from PIL import Image,ImageChops,ImageOps,ImageDraw
import pygame.image
import pygame.camera
import ConfigParser


#Take Photos and modify ====================================================================================
def cheese(z):
 i = 0 
 while (i < (RESW*RESH*65/100) or i > (RESW*RESH*95/100) ):
  im1 = cam.get_image()
  time.sleep(0.055)     
  p.ChangeDutyCycle(12)
  time.sleep(0.055)
  im2 = cam.get_image()
  time.sleep(0.055)
  p.ChangeDutyCycle(0)
  time.sleep(0.055)
  pygame.image.save(im1, "b%08d.jpg" % z)
  pygame.image.save(im2, "a%08d.jpg" % z)
  im2 = Image.open("b%08d.jpg" % z).rotate(ROT)
  im1 = Image.open("a%08d.jpg" % z).rotate(ROT)
  draw = ImageDraw.Draw(im2)
  draw.rectangle([0,0,RESW,CROPH], fill=0)
  draw = ImageDraw.Draw(im1)
  draw.rectangle([0,0,RESW,CROPH], fill=0)
  draw.line((int(RESW/2), 0,int(RESW/2),CROPH),fill=255)
  diff = ImageChops.difference(im2, im1)
  diff = ImageOps.grayscale(diff)
  diff = ImageOps.posterize(diff, 6)
  v = diff.getcolors()
  i= v[0][0]
  #print i
  im1.save("b%08d.jpg" % z, quality= 90)
  im1 = Image.new("RGB", (RESW,RESH))
  im1.paste(diff)
  im1.save("%08d.jpg" % z, quality= 90)
  im2.save("a%08d.jpg" % z, quality= 90)

#STEPPER====================================================================================================  
def stepper(sequence, pins):
    for step in sequence:
        for pin in pins:
            gpio.output(pin, gpio.HIGH) if pin in step else gpio.output(pin, gpio.LOW)
        time.sleep(DELAY) 


#SYSTEM=====================================================================================================
print '<!DOCTYPE html>'
print '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
print '<title>Shapextractor</title>'
print '<link rel="stylesheet" type="text/css" href="./PLY Viewer/style.css">'
print '<body>'
print '<h2>Shapextractor Scan</h2>'
print '<div style="width: 100%; text-align:center">	<br>'

try:
   with open('/dev/video0'): pass 
except IOError:
   print 'Check your webcam</br>'
   exit() 
print 'Scanextractor 0.7</br>'
print 'Init system ....</br>' 
import cgi
form = cgi.FieldStorage() 

A = int(form.getvalue('A'))
An = int(form.getvalue('An'))
B = int(form.getvalue('B'))
Bn = int(form.getvalue('Bn'))
LASER = int(form.getvalue('LASER')) #GPIO FOR MANAGE LASER LINE
LIGHT = int(form.getvalue('LIGHT')) #GPIO FOR MANAGE WHITE LEDS OR PLED
DELAY = float(form.getvalue('DELAY')) #stepper sequence delay
CROPH = int(form.getvalue('CROPH'))  #pix to remove from top.(need for  clean image final output)
QUALITY = int(form.getvalue('QUALITY'))  #(0 to 2) 0=512photo  1=2014 2=4028
RESW= int(form.getvalue('RESW'))
RESH= int(form.getvalue('RESH'))
ROT= int(form.getvalue('ROT'))

CAMERA_HFOV = float(form.getvalue('CAMERA_HFOV'))
CAMERA_DISTANCE = float(form.getvalue('CAMERA_DISTANCE'))
LASER_OFFSET = float(form.getvalue('LASER_OFFSET')) 
HORIZ_AVG = int(form.getvalue('HORIZ_AVG'))
VERT_AVG = int(form.getvalue('VERT_AVG'))
FRAME_SKIP = int(form.getvalue('FRAME_SKIP'))
POINT_SKIP = int(form.getvalue('POINT_SKIP'))


PINS = [A,An,B,Bn] #GPIO stepper 
SEQA = [(A,),(A,An)]
SEQB = [(An,),(An,B)]
SEQC = [(B,),(B,Bn)]
SEQD = [(Bn,),(Bn,A)] 

gpio.setmode(gpio.BCM)
gpio.setup(LIGHT, gpio.OUT)
gpio.setup(LASER, gpio.OUT)
for pin in PINS:
    gpio.setup(pin, gpio.OUT) 
gpio.output(LIGHT, gpio.HIGH)

#CAMERA=====================================================================================================
print 'Init camera....</br>'
import pygame.image
pygame.camera.init()
cam = pygame.camera.Camera(pygame.camera.list_cameras()[0],(RESW,RESH))
cam.start()
if ROT==90 :
 z=RESW
 RESW=RESH
 RESH=z
subprocess.call("v4l2-ctl --set-ctrl white_balance_automatic=0" ,shell=True)
subprocess.call("v4l2-ctl --set-ctrl sharpness=63" ,shell=True)

#STEP'n'CHEESE==============================================================================================
print 'Start scan....</br>'
z=0
p = gpio.PWM(LASER, 50)
p.start(0)
p.ChangeDutyCycle(0)   
p.ChangeFrequency(50)
for x in range(0,512):
# print 'Full step N-' , x
print '<img src="toc.jpg"/>'
 cheese(z)
 if z==1 :
  cheese(z)
  print '<img src="tic.jpg"/>'
 z=z+1
 stepper(SEQA,PINS)
 if QUALITY >>1 :
  cheese(z)
  print '<img src="tic.jpg"/>'
  z=z+1
 stepper(SEQB,PINS)
 if QUALITY >>0 :
  cheese(z)
  print '<img src="tic.jpg"/>'
  z=z+1
 stepper(SEQC,PINS)
 if QUALITY >>1 :
  cheese(z)
  print '<img src="tic.jpg"/>'
  z=z+1
 stepper(SEQD,PINS)

#CLOSE resource (gpio & camera) and prepare folder project==================================================
print 'Cleanup system....</br>'
# finish gpio use
p.stop()
gpio.cleanup()
pygame.camera.quit()
pkey=binascii.b2a_hex(os.urandom(4))
subprocess.call("mkdir ./models/%s" % pkey,shell=True)
subprocess.call("mkdir ./models/%s/jpg" % pkey,shell=True)

#shapextratctor=============================================================================================
print 'Start extractor....</br>'
subprocess.call("./Shapextractor %s %s %s %s %s %s %s %s >./models/%s/%s.ply" % (CAMERA_HFOV,CAMERA_DISTANCE,LASER_OFFSET,HORIZ_AVG,VERT_AVG,FRAME_SKIP,POINT_SKIP,ROT,pkey,pkey) ,shell=True)

print 'Clean up temp direcotry....</br>'

#clean workbench add project in web site
subprocess.call("mv *.jpg ./models/%s/jpg/" % pkey,shell=True)
with open("index.htm", "a") as myfile:
 myfile.write('<A href="./PLY Viewer.htm?file=./models/%s/%s.ply">View </a>&nbsp;&nbsp;&nbsp; <A href="./models/%s/%s.ply">Download </a> &nbsp;&nbsp; <img src="./models/%s/jpg/a00000000.jpg"></img>  <br><br>\n' % (pkey,pkey,pkey,pkey,pkey))
subprocess.call("chmod 777 -R ./" ,shell=True)
print 'Scanextractor done....</br>'
print '</body></html>'


