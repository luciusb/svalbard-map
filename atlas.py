# -*- coding: utf-8 -*-
import os,sys
from svalbard import utm2p, ll2p, enlarge, GetPicture, tilegen, generatesheet
from PIL import Image,ImageFont, ImageDraw


def getlevel(level,ratio):
  """select zoom level for cover sheet"""
  plevel=level
  resratio=1
  while resratio<ratio:
    resratio*=2
    plevel-=1
  return plevel


def names(x,y,maxx,maxy):
  name="%s%02i"%(chr(y+ord('A')),x+1)
  res=[None, None, None, None]
  if x>0: res[0]="%s%02i"%(chr(y+ord('A')),x)
  if y>0: res[1]="%s%02i"%(chr(y-1+ord('A')),x+1)
  if x<maxx-1: res[2]="%s%02i"%(chr(y+ord('A')),x+2)
  if y<maxy-1: res[3]="%s%02i"%(chr(y+1+ord('A')),x+1)
  return name,res

def GenerateAtlasCover(level, box, paper=(210,297), dpi=100):
  dpmm=dpi/25.4
  margin = int(10*dpmm)
  Xmax=int(paper[0]*dpmm)
  Ymax=int(paper[1]*dpmm)
  totalpixx=box[2]-box[0]
  totalpixy=box[3]-box[1]
  pagesx=(totalpixx-2*margin)/(paper[0]*dpmm-2*margin)
  pagesy=(totalpixy-2*margin)/(paper[1]*dpmm-2*margin)
   
  #select level for cover sheet
  plevel=getlevel(level, max(pagesx, pagesy))
  rratio=float(2**(level-plevel))
  coverbox=[int(x/rratio) for x in box]
  coverbox=enlarge(coverbox, 1.5)
  cover=GetPicture(plevel, coverbox )
  draw=ImageDraw.Draw(cover)
  font=ImageFont.truetype(r"DejaVuSans.ttf", 24)
  dn='atlas/%i/'%level
  if not os.path.exists(dn):
    os.makedirs(dn)
  print "Generating cover" 
  for y,(sy,ey) in enumerate(tilegen(box[1],box[3], Ymax, margin)):
    covery=int(sy/rratio-coverbox[1])
    draw.line([int(box[0]/rratio-coverbox[0]), covery, int(box[2]/rratio-coverbox[0]), covery],fill=(0,0,0),width=1)
    for x,(sx,ex) in enumerate(tilegen(box[0], box[2], Xmax, margin)):
      listname,_=names(x, y, pagesx, pagesy)  
      if x>0:
        coverx=int((sx+margin)/rratio-coverbox[0])
      else:
        coverx=int(sx/rratio-coverbox[0])
      draw.line([coverx, int(box[1]/rratio-coverbox[1]), coverx, int(box[3]/rratio-coverbox[1])],fill=(0,0,0),width=1)
      draw.text((coverx+10, covery+10), listname, font=font, fill=(0,0,0))
    draw.line([int(ex/rratio-coverbox[0]), int(box[1]/rratio-coverbox[1]), int(ex/rratio-coverbox[0]), int(box[3]/rratio-coverbox[1])],fill=(0,0,0),width=1)
  draw.line([int(box[0]/rratio-coverbox[0]), int(ey/rratio-coverbox[1]), int(box[2]/rratio-coverbox[0]), int(ey/rratio-coverbox[1])],fill=(0,0,0),width=1)
  fn=os.path.join(dn,"!cover.png")
  cover.save(fn)


def GenerateAtlas(level, box, paper=(210,297), dpi=100):
  dpmm=dpi/25.4
  margin = int(10*dpmm)
  Xmax=int(paper[0]*dpmm)
  Ymax=int(paper[1]*dpmm)
  totalpixx=box[2]-box[0]
  totalpixy=box[3]-box[1]
  pagesx=(totalpixx-2*margin)/(paper[0]*dpmm-2*margin)
  pagesy=(totalpixy-2*margin)/(paper[1]*dpmm-2*margin)
  dn='atlas/%i/'%level
  if not os.path.exists(dn):
    os.makedirs(dn)
  for y,(sy,ey) in enumerate(tilegen(box[1],box[3], Ymax, margin)):
    for x,(sx,ex) in enumerate(tilegen(box[0], box[2], Xmax, margin)):
      listname,neighbours=names(x, y, pagesx, pagesy)  
      sheet=generatesheet(level,[sx,sy,ex,ey], margin=margin, listname=listname, neighbours=neighbours)
      sheet.save(os.path.join(dn,listname+".png"))


if __name__=="__main__":
  level=int(sys.argv[1])
  if len(sys.argv)>2:
    dpi=int(sys.argv[2])
  else:
    dpi=150


  #box=(473110, 8757550, 544360, 8637579)
  #start=(382180, 8995070)
    #end=(792140, 8510270)
  #sx,sy=utm2p(level, start[0], start[1])
  #ex,ey=utm2p(level, end[0], end[1])
  sx,sy=utm2p(level, 479340, 8687760)
  ex,ey=utm2p(level,531500, 8640000)
  GenerateAtlasCover(level, [sx, sy, ex, ey], paper=(297,210),dpi=dpi)
  GenerateAtlas(level, [sx, sy, ex, ey], paper=(297,210),dpi=dpi)
