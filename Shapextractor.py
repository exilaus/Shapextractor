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

#A = 9
#An = 25
#B = 11
#Bn = 8
#LASER = 18 #GPIO FOR MANAGE LASER LINE
#LIGHT = 7 #GPIO FOR MANAGE WHITE LEDS OR PLED
#DELAY = 0.002 
#CROPH = 180  #pix to remove from top.(need for  clean image final output)
#QUALITY = 1  #(0 to 2) 0=512photo  1=2014 2=4028
#RESV=640
#RESH=480
#ROT=0

#PINS = [A,An,B,Bn] #GPIO stepper 
#SEQA = [(A,),(A,An)]
#SEQB = [(An,),(An,B)]
#SEQC = [(B,),(B,Bn)]
#SEQD = [(Bn,),(Bn,A)] 


#Take Photos and modify ====================================================================================
def cheese(z):
 i = 0 
 while (i < (RESV*RESH*65/100) or i > (RESV*RESH*90/100) ):
  im1 = cam.get_image()
  time.sleep(0.05)     
  p.ChangeDutyCycle(12)
  time.sleep(0.05)
  im2 = cam.get_image()
  time.sleep(0.05)
  p.ChangeDutyCycle(0)
  time.sleep(0.05)
  pygame.image.save(im1, "b%08d.jpg" % z)
  pygame.image.save(im2, "a%08d.jpg" % z)
  im2 = Image.open("b%08d.jpg" % z).rotate(ROT)
  im1 = Image.open("a%08d.jpg" % z).rotate(ROT)
  draw = ImageDraw.Draw(im2)
  draw.rectangle([0,0,RESV,CROPH], fill=0)
  draw = ImageDraw.Draw(im1)
  draw.rectangle([0,0,RESV,CROPH], fill=0)
  diff = ImageChops.difference(im2, im1)
  diff = ImageOps.grayscale(diff)
  diff = ImageOps.posterize(diff, 6)
  v = diff.getcolors()
  i= v[0][0]
  print i
  im1.save("b%08d.jpg" % z, quality= 90)
  im1 = Image.new("RGB", (RESV,RESH))
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
try:
   with open('/dev/video0'): pass 
except IOError:
   print 'Check your webcam'
   exit() 
print 'Scanextractor 0.5'
print 'Init system ....' 
config = ConfigParser.ConfigParser()
config.read('Shapextractor.ini')

A = int(config.get('PYTHON', 'A'))
An = int(config.get('PYTHON', 'An'))
B = int(config.get('PYTHON', 'B'))
Bn = int(config.get('PYTHON', 'Bn'))
LASER = int(config.get('PYTHON', 'LASER')) #GPIO FOR MANAGE LASER LINE
LIGHT = int(config.get('PYTHON', 'LIGHT')) #GPIO FOR MANAGE WHITE LEDS OR PLED
DELAY = float(config.get('PYTHON', 'DELAY')) #stepper sequence delay
CROPH = int(config.get('PYTHON', 'CROPH'))  #pix to remove from top.(need for  clean image final output)
QUALITY = int(config.get('PYTHON', 'QUALITY'))  #(0 to 2) 0=512photo  1=2014 2=4028
RESV= int(config.get('PYTHON', 'RESV'))
RESH= int(config.get('PYTHON', 'RESH'))
ROT= int(config.get('PYTHON', 'ROT'))

CAMERA_HFOV = float(config.get('C++', 'CAMERA_HFOV'))
CAMERA_DISTANCE = float(config.get('C++', 'CAMERA_DISTANCE'))
LASER_OFFSET = float(config.get('C++', 'LASER_OFFSET')) 
HORIZ_AVG = int(config.get('C++', 'HORIZ_AVG'))
VERT_AVG = int(config.get('C++', 'VERT_AVG'))
FRAME_SKIP = int(config.get('C++', 'FRAME_SKIP'))
POINT_SKIP = int(config.get('C++', 'POINT_SKIP'))


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
print 'Init camera....'
import pygame.image
pygame.camera.init()
cam = pygame.camera.Camera(pygame.camera.list_cameras()[0],(RESV,RESH))
cam.start()
if ROT==90 :
 z=RESV
 RESV=RESH
 RESH=z
subprocess.call("v4l2-ctl --set-ctrl white_balance_automatic=0" ,shell=True)
subprocess.call("v4l2-ctl --set-ctrl sharpness=63" ,shell=True)

#STEP'n'CHEESE==============================================================================================
print 'Start scan....'
z=0
p = gpio.PWM(LASER, 50)
p.start(0)
p.ChangeDutyCycle(0)   
p.ChangeFrequency(50)
for x in range(0,512):
 print 'Full step N-' , x
 cheese(z)
 if z==1 :
  cheese(z)
 z=z+1
 stepper(SEQA,PINS)
 if QUALITY >>1 :
  cheese(z)
  z=z+1
 stepper(SEQB,PINS)
 if QUALITY >>0 :
  cheese(z)
  z=z+1
 stepper(SEQC,PINS)
 if QUALITY >>1 :
  cheese(z)
  z=z+1
 stepper(SEQD,PINS)

#CLOSE resource (gpio & camera) and prepare folder project==================================================
print 'cleanup system....'
# finish gpio use
p.stop()
gpio.cleanup()
pygame.camera.quit()
pkey=binascii.b2a_hex(os.urandom(4))
subprocess.call("mkdir ./models/%s" % pkey,shell=True)
subprocess.call("mkdir ./models/%s/jpg" % pkey,shell=True)

#shapextratctor=============================================================================================
print 'start extractor....'
subprocess.call("./Shapextractor %s %s %s %s %s %s %s %s >./models/%s/%s.ply" % (CAMERA_HFOV,CAMERA_DISTANCE,LASER_OFFSET,HORIZ_AVG,VERT_AVG,FRAME_SKIP,POINT_SKIP,ROT,pkey,pkey) ,shell=True)

print 'clean up temp direcotry....'

#clean workbench add project in web site
subprocess.call("mv *.jpg ./models/%s/jpg/" % pkey,shell=True)
with open("index.htm", "a") as myfile:
 myfile.write('<A href="./PLY Viewer.htm?file=./models/%s/%s.ply">View </a>&nbsp;&nbsp;&nbsp; <A href="./models/%s/%s.ply">Download </a> &nbsp;&nbsp; <img src="./models/%s/jpg/a00000000.jpg"></img>  <br><br>\n' % (pkey,pkey,pkey,pkey,pkey))
subprocess.call("chmod 777 -R ./" ,shell=True)
print 'Scanextractor done....'


