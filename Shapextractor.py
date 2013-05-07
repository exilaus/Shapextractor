import compileall
import subprocess
import RPi.GPIO as gpio 
import time
import os 
import binascii
from PIL import Image,ImageChops,ImageOps
import pygame.image
import pygame.camera

PINS = [9,25,11,8] #GPIO stepper 
SEQA = [(9,),(9,25),(25,),(25,11)]
SEQB = [(11,),(11,8),(8,),(8,9)] 
LASER = 18 #GPIO FOR MANAGE LASER LINE
LIGHT = 7 #GPIO FOR MANAGE WHITE LEDS OR PLED
DELAY = 0.002 
CROPIMAGE = 180

def cheese(z):
 i = 0 
 while (i < 220000):
  im1 = cam.get_image()
  time.sleep(0.1)     
  p.ChangeDutyCycle(12)
  p.ChangeFrequency(50)   
  time.sleep(0.2)
  im2 = cam.get_image()
  time.sleep(0.2)
  p.ChangeDutyCycle(0)
  time.sleep(0.1)
  pygame.image.save(im1, "a%08d.jpg" % z)
  pygame.image.save(im2, "b%08d.jpg" % z)
  im2 = Image.open("a%08d.jpg" % z)
  im1 = Image.open("b%08d.jpg" % z)
  diff = ImageChops.difference(im2, im1)
  diff = ImageOps.grayscale(diff)
  diff = ImageOps.posterize(diff, 6)
  v = diff.getcolors()
  i= v[0][0]
  print i
  im1 = Image.new("RGB", (640,480))
  im1.paste(diff)
  im1.save("%08d.jpg" % z, quality= 100)
  im2.save("./tmp/a%08d.jpg" % z, quality= 100)

def stepper(sequence, pins):
    for step in sequence:
        for pin in pins:
            gpio.output(pin, gpio.HIGH) if pin in step else gpio.output(pin, gpio.LOW)
        time.sleep(DELAY) 



try:
   with open('/dev/video0'): pass 
except IOError:
   print 'Check your webcam'
   exit() 
print 'Scanextractor 0.5'
print 'init system ....' 
gpio.setmode(gpio.BCM)
gpio.setup(LIGHT, gpio.OUT)
gpio.setup(LASER, gpio.OUT)
for pin in PINS:
    gpio.setup(pin, gpio.OUT) 
gpio.output(LIGHT, gpio.HIGH)

print 'init camera....'
#init camera
import pygame.image
pygame.camera.init()
cam = pygame.camera.Camera(pygame.camera.list_cameras()[0])
cam.start()
subprocess.call("v4l2-ctl --set-ctrl white_balance_automatic=0" ,shell=True)
subprocess.call("v4l2-ctl --set-ctrl sharpness=63" ,shell=True)
img = cam.get_image()

print 'Start scan....'
z=0
p = gpio.PWM(LASER, 50)
p.start(50)
p.ChangeDutyCycle(0)   
p.ChangeFrequency(50)

#rotate and photo scan process
for x in range(0,512):
 print 'Full step N-' , x
 cheese(z)
 stepper(SEQA,PINS)
 stepper(SEQB,PINS)
 z=z+1
 #frame = myCamera.getImage().rotate90().save("%08d.jpg" % z)

print 'clean up system....'
# finish gpio use
p.stop()
gpio.cleanup()
pygame.camera.quit()

#generate projectkey & folders
pkey=binascii.b2a_hex(os.urandom(4))
subprocess.call("mkdir ./models/%s" % pkey,shell=True)
subprocess.call("mkdir ./models/%s/jpg" % pkey,shell=True)

print 'start extractor....'
subprocess.call("./Shapextractor >./models/%s/%s.ply" % (pkey,pkey) ,shell=True)

print 'clean up temp direcotry....'

#clean workbench add project in web site
subprocess.call("mv *.jpg ./models/%s/jpg/" % pkey,shell=True)
with open("index.htm", "a") as myfile:
 myfile.write('<A href="./PLY Viewer.htm?file=./models/%s/%s.ply">View </a>&nbsp;&nbsp;&nbsp; <A href="./models/%s/%s.ply">Download </a> &nbsp;&nbsp; <img src="./models/%s/jpg/a00000000.jpg"></img>  <br><br>' % (pkey,pkey,pkey,pkey,pkey))
subprocess.call("chmod 777 -R ./" ,shell=True)
print 'Scanextractor done....'


