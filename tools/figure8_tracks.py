# Generates the figure-8 track layouts used in Aussie 8 and validates them:
# exactly one crossing, wall clearance elsewhere, arena bounds, minimum turn radius.
# Writes tracks.json and tracks_preview.png. Requires Pillow.
import math, json, sys
from PIL import Image, ImageDraw

def catmull(P, per=24):
    n = len(P); S = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i-1) % n], P[i], P[(i+1) % n], P[(i+2) % n]
        for k in range(per):
            u = k/per; u2 = u*u; u3 = u2*u
            S.append(tuple(0.5*(2*p1[j]+(-p0[j]+p2[j])*u+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*u2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*u3) for j in (0, 1)))
    return S

def gen(cx, cy, aL, aR, bL, bR, n=16, rot=0, pw=1.0, wob=None, rev=False, skew=0):
    pts = []
    for i in range(n):
        u = 2*math.pi*i/n + math.pi/n/2
        s = math.sin(u); s2 = math.sin(2*u)
        a = aR if s >= 0 else aL; b = bR if s >= 0 else bL
        y = b*math.copysign(abs(s2)**pw, s2)
        x = a*s + skew*y/b*40
        if wob: x, y = wob(x, y, s)
        c, sn = math.cos(rot), math.sin(rot)
        pts.append([round(cx + x*c - y*sn), round(cy + x*sn + y*c)])
    return pts[::-1] if rev else pts

def analyse(P):
    S = catmull(P); N = len(S)
    cum = [0]
    for i in range(1, N): cum.append(cum[-1]+math.dist(S[i], S[i-1]))
    L = cum[-1]+math.dist(S[0], S[-1])
    ad = lambda i, j: min(abs(cum[i]-cum[j]), L-abs(cum[i]-cum[j]))
    cross = []
    for i in range(N):
        for j in range(i+1, N):
            if ad(i, j) > 300 and math.dist(S[i], S[j]) < 14:
                if not any(math.dist(S[i], c) < 60 for c in cross): cross.append(S[i])
    bad = 1e9
    for i in range(N):
        for j in range(i+1, N):
            if ad(i, j) > 220:
                d = math.dist(S[i], S[j])
                if d < 135 and not any(math.dist(S[i], c) < 150 and math.dist(S[j], c) < 150 for c in cross):
                    bad = min(bad, d)
    xs = [p[0] for p in S]; ys = [p[1] for p in S]
    # min radius
    rmin = 1e9
    for i in range(N):
        a, b, c = S[i-2], S[i], S[(i+2) % N]
        t1 = math.atan2(b[1]-a[1], b[0]-a[0]); t2 = math.atan2(c[1]-b[1], c[0]-b[0])
        dt = abs((t2-t1+math.pi) % (2*math.pi)-math.pi); ds = math.dist(a, b)+math.dist(b, c)
        if dt > 1e-6: rmin = min(rmin, ds/dt)
    return dict(L=round(L), cross=len(cross), crossAt=[tuple(map(round, c)) for c in cross], sepViol=round(bad) if bad < 1e9 else None,
                x=(round(min(xs)), round(max(xs))), y=(round(min(ys)), round(max(ys))), rmin=round(rmin)), S

def wobR(amp, k):
    return lambda x, y, s: (x, y + (amp*math.sin(k*x/60) if s >= 0 else 0))
def dent(xc, amp, w):
    return lambda x, y, s: (x, y + amp*math.exp(-((x-xc)/w)**2)*(1 if y < 0 else -1)*(-1))


import math
def gen2(cx, cy, aL, aR, bL, bR, n=24, rot=0, pwL=1.0, pwR=1.0, mods=(), rev=False):
    pts=[]
    for i in range(n):
        u=2*math.pi*i/n+math.pi/n/2
        s=math.sin(u); s2=math.sin(2*u)
        a=aR if s>=0 else aL; b=bR if s>=0 else bL; pw=pwR if s>=0 else pwL
        x=a*s; y=b*math.copysign(abs(s2)**pw,s2)
        for m in mods: x,y=m(x,y)
        c,sn=math.cos(rot),math.sin(rot)
        pts.append([round(cx+x*c-y*sn),round(cy+x*sn+y*c)])
    return pts[::-1] if rev else pts
G=lambda v,c,w:math.exp(-((v-c)/w)**2)
topDent=lambda xc,amp,w:(lambda x,y:(x,y+amp*G(x,xc,w)*(1 if y<0 else 0)*min(1,-y/60)))
botDent=lambda xc,amp,w:(lambda x,y:(x,y-amp*G(x,xc,w)*(1 if y>0 else 0)*min(1,y/60)))
tipDentR=lambda amp,w,x0:(lambda x,y:(x-amp*G(y,0,w)*max(0,min(1,(x-x0)/80)),y))
tipDentL=lambda amp,w,x0:(lambda x,y:(x+amp*G(y,0,w)*max(0,min(1,(-x-x0)/80)),y))
whoops=lambda amp,k:(lambda x,y:(x,y+(amp*math.sin(x/k) if y>40 else 0)))
D = {
 'Red Centre Bowl':  gen2(480,302,385,385,188,188,n=16),
 'Kakadu Swamp':     gen2(455,300,330,415,178,190,pwR=0.7,mods=[tipDentR(95,70,250)]),
 'Flinders Ridge':   gen2(480,300,370,370,168,168,rot=0.11,pwL=0.5,pwR=1.0,rev=True),
 'Coober Pedy Pits': gen2(480,302,385,385,190,190,pwL=0.55,pwR=0.55,mods=[topDent(-210,62,60),botDent(220,62,60)]),
 'Nullarbor Flats':  gen2(480,300,398,398,150,150,pwL=0.8,pwR=0.8,mods=[whoops(14,28)],rev=True),
 'Kimberley Gorge':  gen2(468,302,405,320,194,170,pwL=0.6,pwR=0.9,mods=[topDent(-230,70,55)]),
 'Daintree Mudbath': gen2(470,300,410,300,192,176,pwL=0.65,pwR=0.6,mods=[tipDentL(90,65,250),botDent(250,40,50)],rev=True),
 'Outback Showdown': gen2(480,302,390,390,192,192,pwL=0.6,pwR=0.6,mods=[topDent(245,55,55),botDent(-245,55,55),tipDentR(40,60,260)],rev=True),
}
out = {}
im = Image.new('RGB', (960*2, 640*4), (40, 30, 50))
for k, (name, P) in enumerate(D.items()):
    info, S = analyse(P)
    print(name, info)
    out[name] = P
    ox, oy = (k % 2)*960, (k//2)*640
    d = ImageDraw.Draw(im)
    pts = [(x+ox, y+oy+40) for x, y in S]
    d.line(pts+[pts[0]], fill=(90, 60, 40), width=128, joint='curve')
    d.line(pts+[pts[0]], fill=(200, 120, 60), width=88, joint='curve')
    d.line(pts+[pts[0]], fill=(120, 70, 40), width=2)
    d.rectangle([ox, oy, ox+959, oy+639], outline=(255, 255, 255))
    d.text((ox+10, oy+10), name, fill=(255, 255, 255))
im.resize((960, 1280)).save('tracks_preview.png')
json.dump(out, open('tracks.json', 'w'))
