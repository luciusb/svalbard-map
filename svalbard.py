# -*- coding: utf-8 -*-
import urllib2
import os, sys
from PIL import Image,ImageFont, ImageDraw
from math import ceil
from utm import UTMtoLL,LLtoUTM

tileSize = 256
resolution=(
  21674.7100160867,#0	1:81920000
  10837.3550080434,#1	1:40960000
  5418.67750402168,#2	1:20480000
  2709.33875201084,#3	1:10240000
  1354.66937600542,#4	1:5120000
  677.334688002709,#5	1:2560000
  338.667344001355,#6	1:1280000
  169.333672000677,#7	1:640000
  84.6668360003387,#8	1:320000
  42.3334180001693,#9	1:160000
  21.1667090000847,#10	1:80000
  10.5833545000423,#11	1:40000
  5.29167725002117,#12	1:20000
  2.64583862501058,#13	1:10000
)

def p2utm(level,x,y):
  if type(x) in (tuple,list):
    x=x[0]*256+x[1]
  if type(y) in (tuple,list):
    y=y[0]*256+y[1]
  e=x*resolution[level]-5120900
  n=9998100-y*resolution[level]
  return e,n

def p2LL(level,x,y):
  e,n=p2utm(level,x,y)
  return UTMtoLL(22, e, n, '33X')

def ll2p(level,lat,lon):
  z,e,n=LLtoUTM(22,lat,lon)
  return utm2p(level,e,n)

def utm2p(level,e,n):
  x=(e+5120900)/resolution[level]
  y=(9998100-n)/resolution[level]
  return x,y

def gettile(level,x,y):
  #print "get",level,x,y
  fn='tiles/%i/%i-%i.png'%(level,x,y)
  if not os.path.exists(os.path.dirname(fn)):
    os.makedirs(os.path.dirname(fn))
  if os.path.exists(fn):
    return Image.open(fn)
  else:
    print "Downloading",level,x,y
    try:
      uri='http://geodata.npolar.no/ArcGIS/rest/services/inspire1/NP_TopoSvalbard_U33_CHL/MapServer/tile/%i/%i/%i'%(level,y,x)
      data=urllib2.urlopen(uri).read()
      if len(data):
        f=open(fn,'wb')
        f.write(data)
        f.close()
        return Image.open(fn)
    except urllib2.HTTPError:
      pass
    return Image.new("RGBA", (256, 256), (0,0,0,0))



def ltile(x):
  return int(float(x)/tileSize)

def htile(x):
  return int(ceil(float(x)/tileSize))

def GetPicture(level, box):
  sx,sy=ltile(box[0]), ltile(box[1])
  ex,ey=htile(box[2]), htile(box[3])
  sheet = Image.new("RGBA", ((ex-sx)*tileSize, (ey-sy)*tileSize), (0,0,0,0))
  posY=0
  for y in range(sy,ey+1):
    posX=0
    for x in range(sx,ex+1):
      i=gettile(level,x,y)
      destBox = (posX, posY, posX + i.size[0], posY + i.size[1])
      sheet.paste(i, destBox)
      posX+=i.size[0]
    posY+=i.size[1]#taking size of last tile
  cropbox=[int(box[0]-sx*tileSize), int(box[1]-sy*tileSize) , int(box[2]-sx*tileSize), int(box[3]-sy*tileSize)]
  sheet=sheet.crop(cropbox)
  return sheet

def StepGenerator():
  #tell in how many minutes is one step
  yield 60.
  steps=10.
  while True:
    yield steps
    steps=steps/2
    yield steps
    steps=steps/5


def generatesteps(start,stop, minc):
  """generate list of coordinates between start and stop for grid, minc determines minimal count of steps
  the coordinates steps are at logical levels 
  start and stops are in degrees, but the displayed grid should be in DD MM.MMM format (most GPS work in DD MM.MMM or DD MM SS)
  returned list consists of tuples (coodinate, text representation
  """
  res=[]
  startmins=start*60.
  endmins=stop*60.
  diff=endmins-startmins
  stepg=StepGenerator()
  step=stepg.next()
  while diff/step<minc:
    step=stepg.next()
  res=[]
  c=ceil(startmins/step)*step
  while c<endmins:
    deg,mins=divmod(c,60)
    rep="%i°"%deg 
    if mins>diff/100:
      rep+= str(mins).rstrip('0').rstrip('.')+"'"
    res.append((c/60.,rep))
    c+=step
  return res

def generateCoord(level, box, margin):
  sx, sy, ex, ey=box
  sx,sy,ex,ey=sx+margin, sy+margin, ex-margin, ey-margin
  nw=p2LL(level,sx,sy)
  ne=p2LL(level,ex,sy)
  sw=p2LL(level,sx,ey)
  se=p2LL(level,ex,ey)
  n=[(x,nw[1],rep) for x,rep in generatesteps(nw[0],ne[0],4)]
  s=[(x,sw[1],rep) for x,rep in generatesteps(sw[0],se[0],4)]
  w=[(nw[0],y,rep) for y,rep in generatesteps(sw[1],nw[1],4)]
  e=[(ne[0],y,rep) for y,rep in generatesteps(se[1],ne[1],4)]
  return w,n,e,s

def generatesheet(level, box, margin=0, listname=None, neighbours=None):
  """generates sheet from given level tiles
     start end are tuple coordinates in pixels for given level
     margin is width of ovelaping parts in pixels
     listname is name of this list (placed in topleft corner)
     neighbours is tuple of neigbours names in format (W,N,E,S), when None neither the margin line is drawn
  """
  print "generating sheet", listname
  sx,sy,ex,ey=box
  sheet = GetPicture(level, box) 
  draw=ImageDraw.Draw(sheet)
  if not listname == None:
    font=ImageFont.truetype(r"DejaVuSans.ttf", 28)
    draw.text((10,10), listname, font=font, fill=(0,0,0))

    cm=int(100/resolution[level])
    km=int(1000/resolution[level])
    steps=[cm,cm,cm,cm,cm,5*cm,km,km,km,km,5*km]
    a= 2*margin
    scalebox=[a , sheet.size[1]-margin/2, a, sheet.size[1]-margin/2+5]
    c1,c2=(0,0,0),(255,255,255)
    for step in steps:
      c1,c2=c2,c1
      scalebox[0]=scalebox[2]
      scalebox[2]+=step
      draw.rectangle(scalebox,fill=c1, outline=c2)
  
  coords=generateCoord(level, box, margin)
  w,n,e,s=[[(c,ll2p(level,c[0],c[1]),c[2])for c in line] for line in coords]
  font=ImageFont.truetype(r"DejaVuSans.ttf", 12)
  for c,p,rep in w:
    draw.line([margin-5,p[1]-box[1], margin,p[1]-box[1]],fill=(0,0,0),width=1)
    draw.text((5, p[1]-box[1]-5 ), rep, font=font, fill=(0,0,0))
  for c,p,rep in e:
    draw.line([sheet.size[0]-margin, p[1]-box[1], sheet.size[0]-margin+5, p[1]-box[1]],fill=(0,0,0),width=1)
    draw.text((sheet.size[0]-margin+7, p[1]-box[1]-5 ), rep, font=font, fill=(0,0,0))
  for c,p,rep in s:
    draw.line([int(p[0]-box[0]), sheet.size[1]-margin, int(p[0]-box[0]), sheet.size[1]-margin+5],fill=(0,0,0),width=1)
    draw.text((p[0]-box[0]-12,sheet.size[1]-margin+7), rep, font=font, fill=(0,0,0))
  for c,p,rep in n:
    draw.line([p[0]-box[0], margin, p[0]-box[0], margin-5],fill=(0,0,0),width=1)
    draw.text((p[0]-box[0]-12,margin-17), rep, font=font, fill=(0,0,0))
    

  if not neighbours == None:
    cy=sheet.size[1]/2
    cx=sheet.size[0]/2
    font=ImageFont.truetype(r"DejaVuSans.ttf", 18)
    W,N,E,S=neighbours
    if not W == None:
      draw.line([margin,0 , margin, sheet.size[1]],fill=(0,0,0),width=1)
      draw.text((5, cy), W, font=font, fill=(0,0,0))
    if not E == None:
      draw.line([sheet.size[0]-margin,0 , sheet.size[0]-margin, sheet.size[1]],fill=(0,0,0),width=1)
      draw.text((sheet.size[0]-margin+2, cy), E, font=font, fill=(0,0,0))
    if not N == None:
      draw.line([0, margin, sheet.size[0], margin],fill=(0,0,0),width=1)
      draw.text((cx, 10), N, font=font, fill=(0,0,0))
    if not S == None:
      draw.line([0, sheet.size[1]-margin, sheet.size[0], sheet.size[1]-margin],fill=(0,0,0),width=1)
      draw.text((cx, sheet.size[1]-margin+5), S, font=font, fill=(0,0,0))
  
  return sheet


def tilegen(a , b, pagesize, margin):
  totalpix=b-a
  s=0
  e=0
  while e<totalpix:
    e=min(s+pagesize,totalpix)
    yield s+a,e+a
    s=e-2*margin



def transform(level,tile,offset,targetlevel,targettile):
  return int((tile*tileSize+offset)*2.**(targetlevel-level)-tileSize*targettile)

def enlarge(box, ratio):
  try:
    ratiox,ratioy=ratio
  except:
    ratiox,ratioy=ratio,ratio

  margainx=(box[2]-box[0])*(ratiox-1)/2.
  margainy=(box[3]-box[1])*(ratioy-1)/2.
  return [box[0]-margainx, box[1]-margainy, box[2]+margainx, box[3]+margainx]



def PictureLL(level, box, fn=None):
  if fn==None:
    fn=('(%.4fN%.4fE)-(%.4fN%.4fE)'%box).replace('.',',')+'.jpg'
    print fn
  sx,sy=ll2p(level, box[1], box[0])
  ex,ey=ll2p(level, box[3], box[2])
  GetPicture(level,[sx, sy, ex, ey] ).save(fn)


def PictureUTM(level, box, fn=None):
  if fn==None:
    fn=('(E%iN%i)-(E%iN%i)'%box).replace('.',',')+'.jpg'
    print fn
  sx,sy=utm2p(level, box[0], box[1])
  ex,ey=utm2p(level, box[2], box[3])
  GetPicture(level,[sx, sy, ex, ey] ).save(fn)



if __name__=="__main__":
  level=int(sys.argv[1])
  if len(sys.argv)>2:
    dpi=int(sys.argv[2])
  else:
    dpi=150
  #PictureUTM(level,box)
  PictureUTM(level,(500000, 8697550, 544360, 8637579))
