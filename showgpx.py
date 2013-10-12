# -*- coding: utf-8 -*-
import os, sys
from PIL import Image,ImageFont, ImageDraw
import gpxpy
from svalbard import utm2p, ll2p, enlarge, GetPicture, tilegen, generatesheet

def DrawGpx(level, gpxs, outfn, box=None):
  tracks=[]
  bboxes=[]
  color=colorgen()
  minx,maxx,miny,maxy=(None,None,None,None)
  for gpx in gpxs:
    gpx_file = open(gpx, 'r')
    gpx = gpxpy.parse(gpx_file)
    for track in gpx.tracks:
      gpxpoints=[]
      for segment in track.segments:
        for point in segment.points:
          x,y=ll2p(level, point.longitude, point.latitude)
          gpxpoints.append((x,y))
          if minx==None or x<minx: minx=x
          if maxx==None or x>maxx: maxx=x
          if miny==None or y<miny: miny=y
          if maxy==None or y>maxy: maxy=y
      tracks.append(gpxpoints)
  if box==None:
    sx,sy,ex,ey=enlarge((int(minx),int(miny), int(maxx), int(maxy)),1.5)
  else:
    sx,sy=utm2p(level, box[0], box[1])
    ex,ey=utm2p(level, box[2], box[3])
  bg=GetPicture(level,[sx, sy, ex, ey])
  bg.save(outfn)
  draw=ImageDraw.Draw(bg)
  for track in tracks:
    draw.line([(int(x-sx),int(y-sy)) for x,y in track] ,fill=color.next(),width=3)
  bg.save(outfn)

def colorgen():
  while True:
    for c in ('blueviolet','green','purple','blue', 'red','orange', 'yellow', 'brown', 'darkslateblue','green', 'green','deeppink', 'limegreen','maroon'  ):
      print c
      yield c
  

if __name__=="__main__":
  DrawGpx(9, ('edited_withsplit.gpx','ship.gpx'), 'svalbard2013_combined.png' )
  DrawGpx(8, ['ship.gpx'], 'svalbard2013_ship.png' )
  DrawGpx(10, ['edited_withsplit.gpx'], 'svalbard2013.png' )
