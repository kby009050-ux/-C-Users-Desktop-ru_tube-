#!/usr/bin/env python3
import os, io, json, urllib.request, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
DATA=json.loads("{\"images\":[\"https://ai-thumbnails.s3.amazonaws.com/editor/61402b72-0864-488c-b915-52340caa9510/f82c0a0a-965b-4c82-ae6c-f788e87e50c1.jpeg\",\"https://ai-thumbnails.s3.amazonaws.com/editor/61402b72-0864-488c-b915-52340caa9510/7ab9509a-92f9-46c4-8e9e-65e93c4a767e.jpeg\",\"https://ai-thumbnails.s3.amazonaws.com/editor/61402b72-0864-488c-b915-52340caa9510/f06f03aa-63cd-4ef8-8d53-ba84557b9f77.jpeg\",\"https://ai-thumbnails.s3.amazonaws.com/editor/61402b72-0864-488c-b915-52340caa9510/3c597c32-2e2c-418e-bee2-b666579eebe0.jpeg\",\"https://ai-thumbnails.s3.amazonaws.com/editor/61402b72-0864-488c-b915-52340caa9510/73907797-ecb9-4a03-b133-bdfa81f36449.jpeg\"],\"audio\":\"https://assets.vidiq.com/voiceovers/61402b72-0864-488c-b915-52340caa9510/900c81de-0a03-4de1-8cf7-26be6202cc4a.mp3\",\"scenes\":[0,0,1,1,2,2,3,3,3,4,4,4,4,4,4,4],\"durations\":[5.407347,4.989388,4.127347,4.832653,2.690612,2.925714,3.082449,7.235918,3.004082,4.205714,4.04898,3.787755,2.586122,4.284082,5.407347,1.410612],\"lines\":[\"주인을 버린 건 사람이었지만,\\n끝까지 사람을 믿은 건 강아지였습니다.\",\"비가 쏟아지던 날,\\n한 여자는 강아지를 길에 버리고 떠났습니다.\",\"강아지는 차가 사라진 방향을\\n하염없이 바라봤습니다.\",\"하루가 지나고, 또 하루가 지나도\\n그 자리를 떠나지 않았습니다.\",\"그때 한 할머니가 다가왔습니다.\",\"아가야… 너도 버림받았니?\",\"할머니는 매일 강아지를 찾아왔습니다.\",\"사실 할머니도 얼마 전,\\n평생을 함께한 가족을 떠나보낸 뒤\\n혼자 남겨진 사람이었습니다.\",\"어느 날 할머니가 조용히 말했습니다.\",\"나는 이제…\\n아무도 기다리지 않으려고 했는데.\",\"강아지가 할머니의 손에\\n작은 얼굴을 기댔습니다.\",\"할머니는 강아지를 꼭 끌어안고 울었습니다.\",\"너는 나를 기다렸구나…\",\"그날, 강아지는 새로운 주인을\\n만난 게 아니었습니다.\",\"서로를 기다리던 외로운 할머니와 강아지는\\n마침내 가족이 되었습니다.\",\"루사연이었습니다.\"]}")
OUT=os.environ.get("OUTPUT_FILE","lusayeon_anime_story_full.mp4")
W,H,FPS=540,960,12
SPEED=1.25
def get(url, path):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=80) as r,open(path,"wb") as f:
        f.write(r.read())
for i,url in enumerate(DATA["images"]):
    get(url,f"/tmp/scene_{i}.jpg")
get(DATA["audio"],"/tmp/story.mp3")
font_candidates=[
"/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
"/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
"/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
fpath=next((x for x in font_candidates if os.path.isfile(x)),font_candidates[-1])
header_font=ImageFont.truetype(fpath,30)
caption_font=ImageFont.truetype(fpath,33)
small_font=ImageFont.truetype(fpath,25)
def cover(im):
    iw,ih=im.size
    scale=max(W/iw,H/ih)
    im=im.resize((math.ceil(iw*scale),math.ceil(ih*scale)),Image.Resampling.LANCZOS)
    x=(im.width-W)//2;y=(im.height-H)//2
    return im.crop((x,y,x+W,y+H)).convert("RGB")
imgs=[cover(Image.open(f"/tmp/scene_{i}.jpg")) for i in range(len(DATA["images"]))]
def center_text(draw,text,y,font,stroke=3):
    lines=text.split("\n")
    for item in lines:
        bbox=draw.textbbox((0,0),item,font=font,stroke_width=stroke)
        width=bbox[2]-bbox[0]
        draw.text(((W-width)//2,y),item,font=font,fill="white",stroke_width=stroke,stroke_fill="#131724")
        y+=43
def render(img, caption, sec, idx, end=False):
    n=max(1,round(sec*FPS))
    for j in range(n):
        t=j/max(1,n-1)
        # Subtle image pan-and-zoom while preserving full vertical canvas
        zoom=1.015+0.035*t
        zw,zh=round(W*zoom),round(H*zoom)
        scaled=img.resize((zw,zh),Image.Resampling.BILINEAR)
        xp=round((zw-W)*(0.55 if idx%2 else 0.42)); yp=round((zh-H)*0.48)
        fr=scaled.crop((xp,yp,xp+W,yp+H))
        d=ImageDraw.Draw(fr,"RGBA")
        d.rounded_rectangle((60,25,W-60,83),radius=18,fill=(6,7,17,178))
        hb=d.textbbox((0,0),"루사연 | 애니사연",font=header_font)
        d.text(((W-(hb[2]-hb[0]))//2,33),"루사연 | 애니사연",font=header_font,fill="white",stroke_width=2,stroke_fill="#111111")
        if end:
            d.rounded_rectangle((32,738,W-32,858),radius=25,fill=(4,7,12,165))
            center_text(d,"공감되셨다면\n구독과 좋아요 부탁드립니다.",761,small_font,2)
        else:
            lines=caption.split("\n")
            boxh=60+len(lines)*43
            top=H-90-boxh
            d.rounded_rectangle((18,top,W-18,H-75),radius=20,fill=(0,0,0,150))
            center_text(d,caption,top+24,caption_font,3)
        yield fr.tobytes()
# video-only file first, then mux with time-scaled female voice
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0","-c:v","libx264","-preset","veryfast","-crf","25","-pix_fmt","yuv420p","/tmp/noaudio.mp4"]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for idx,(duration,line,scene) in enumerate(zip(DATA["durations"],DATA["lines"],DATA["scenes"])):
    for b in render(imgs[scene],line,duration/SPEED,idx):
        p.stdin.write(b)
for b in render(imgs[4],"",2.4,16,True):
    p.stdin.write(b)
p.stdin.close()
if p.wait()!=0: raise RuntimeError("Video render failed")
mux=["ffmpeg","-hide_banner","-loglevel","error","-y","-i","/tmp/noaudio.mp4","-i","/tmp/story.mp3","-filter_complex","[1:a]atempo=1.25,apad=pad_dur=3[a]","-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",OUT]
subprocess.run(mux,check=True)
print(OUT,os.path.getsize(OUT))
