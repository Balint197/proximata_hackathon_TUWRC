import sys, yaml, math, subprocess, json
from PIL import Image, ImageDraw
base=sys.argv[1]; out=sys.argv[2]
meta=yaml.safe_load(open(base+'.yaml')); img=Image.open(base+'.pgm').convert('RGB')
res=meta['resolution']; ox,oy=meta['origin'][:2]; H=img.height
d=ImageDraw.Draw(img)
def px(x,y): return ((x-ox)/res, H-(y-oy)/res)
# grid every 1 m
for gx in range(int(ox)-1, int(ox+img.width*res)+2):
    a=px(gx,oy); d.line([(a[0],0),(a[0],H)],fill=(200,220,255))
for gy in range(int(oy)-1, int(oy+H*res)+2):
    a=px(ox,gy); d.line([(0,a[1]),(img.width,a[1])],fill=(200,220,255))
o=px(0,0); d.ellipse([o[0]-3,o[1]-3,o[0]+3,o[1]+3],outline=(0,0,255))
for extra in sys.argv[3:]:
    name,x,y,yaw=extra.split(','); x,y,yaw=float(x),float(y),float(yaw)
    p=px(x,y); q=px(x+.5*math.cos(yaw),y+.5*math.sin(yaw))
    d.ellipse([p[0]-5,p[1]-5,p[0]+5,p[1]+5],outline=(255,0,0)); d.line([p,q],fill=(255,0,0))
    d.text((p[0]+6,p[1]-12),name,fill=(255,0,0))
s=max(1,int(round(900/max(img.width,img.height))))
img=img.resize((img.width*s,img.height*s),Image.NEAREST); img.save(out); print(img.size, 'origin',ox,oy)
