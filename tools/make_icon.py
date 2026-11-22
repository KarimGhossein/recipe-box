"""Draws build/icon.png (minimalist avocado on the ivory card). Usage: python3 tools/make_icon.py ivory build/icon.png"""
import math, sys
from PIL import Image, ImageDraw, ImageFilter
SS=4; S=1024*SS
W=824*SS; off=(S-W)//2; R=185*SS
def egg(cx, cy, hw, hh, top_k=0.60, n=720):
    # pear/egg outline: narrower at the top
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n
        y=-math.cos(t)
        f=top_k+(1-top_k)*((1-math.cos(t))/2)**0.9
        x=math.sin(t)*f
        pts.append((cx+x*hw, cy+y*hh))
    return pts
def rot(pts, cx, cy, deg):
    a=math.radians(deg); c,s=math.cos(a),math.sin(a)
    return [(cx+(x-cx)*c-(y-cy)*s, cy+(x-cx)*s+(y-cy)*c) for x,y in pts]
variant=sys.argv[1] if len(sys.argv)>1 else 'ivory'
if variant=='ivory':
    card_top,card_bot=(250,246,236),(238,231,215); skin=(52,74,40); flesh=(214,219,150); inner=(236,234,190); pit=(150,104,58); rim=(205,174,107)
else:
    card_top,card_bot=(44,60,36),(28,40,24); skin=(240,232,206); flesh=(214,219,150); inner=(236,234,190); pit=(150,104,58); rim=(205,174,107)
icon=Image.new('RGBA',(S,S),(0,0,0,0))
card=Image.new('RGBA',(W,W)); d=ImageDraw.Draw(card)
for y in range(W):
    t=y/(W-1); d.line([(0,y),(W,y)],fill=tuple(int(card_top[i]*(1-t)+card_bot[i]*t) for i in range(3))+(255,))
m=Image.new('L',(W,W),0); ImageDraw.Draw(m).rounded_rectangle([0,0,W-1,W-1],R,fill=255)
icon.paste(card,(off,off),m)
ImageDraw.Draw(icon).rounded_rectangle([off,off,off+W-1,off+W-1],R,outline=(214,203,178,255),width=3*SS)  # soft warm edge, no shadow
d=ImageDraw.Draw(icon)
# hairline inner frame, like the app's gold rules
ins=60*SS; d.rounded_rectangle([off+ins,off+ins,off+W-ins,off+W-ins],R-ins+10*SS,outline=rim+(150 if variant=='ivory' else 170,),width=3*SS)
cx,cy=S/2,S/2+18*SS; ang=-14
hw,hh=238*SS,312*SS
skin_pts=rot(egg(cx,cy,hw,hh),cx,cy,ang)
flesh_pts=rot(egg(cx,cy+5*SS,hw-22*SS,hh-22*SS),cx,cy,ang)
inner_pts=rot(egg(cx,cy+12*SS,hw-66*SS,hh-66*SS, top_k=0.62),cx,cy,ang)
d.polygon(skin_pts,fill=skin+(255,))
d.polygon(flesh_pts,fill=flesh+(255,))
# soft inner glow toward the pit
glow=Image.new('L',(S,S),0); ImageDraw.Draw(glow).polygon(inner_pts,fill=255); glow=glow.filter(ImageFilter.GaussianBlur(40*SS))
icon.paste(inner+(255,),(0,0),glow)
# pit in the lower bulb
a=math.radians(ang); px,py=cx-math.sin(a)*(-70*SS), cy+math.cos(a)*(78*SS)
pr=106*SS
d.ellipse([px-pr,py-pr,px+pr,py+pr],fill=pit+(255,))
# single small highlight on the pit
hr=26*SS; hx,hy=px-38*SS,py-40*SS
hl=Image.new('L',(S,S),0); ImageDraw.Draw(hl).ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=110); hl=hl.filter(ImageFilter.GaussianBlur(6*SS))
icon.paste((255,236,200,255),(0,0),hl)
out=icon.resize((1024,1024),Image.LANCZOS)
out.save(sys.argv[2])
