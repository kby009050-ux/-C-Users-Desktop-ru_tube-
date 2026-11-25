"""Gemini-only 2D anime short, per-line Aoede/Charon voice and timed captions."""
import io, json, os, subprocess, sys, time, wave, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from google import genai
from google.genai import types

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gemini_tts import synthesize_gemini

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/"automation"/"build"
OUT=ROOT/"automation"/"outputs"
W,H=540,960
FPS=18
RATE=1.0

def ffmpeg(*args):
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)

def duration(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())

def font(size):
    for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc","/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf","C:/Windows/Fonts/malgunbd.ttf"]:
        if Path(f).exists():return ImageFont.truetype(f,size)
    raise RuntimeError("Korean font missing")

def image_from_gemini(client, prompt, output, reference=None):
    model=os.environ.get("GEMINI_IMAGE_MODEL","gemini-3.1-flash-image")
    for attempt in range(5):
        try:
            res=client.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=Path(reference).read_bytes(),mime_type="image/jpeg"),prompt] if reference else prompt,
                config=types.GenerateContentConfig(response_modalities=["IMAGE","TEXT"]))
            for part in res.candidates[0].content.parts:
                if getattr(part,"inline_data",None) and part.inline_data.data:
                    raw=part.inline_data.data
                    if isinstance(raw,str):
                        import base64
                        raw=base64.b64decode(raw)
                    im=Image.open(io.BytesIO(raw)).convert("RGB")
                    im.save(output,quality=91)
                    return
            raise RuntimeError("Gemini image response did not contain artwork")
        except Exception as e:
            if not any(code in str(e) for code in ("429","RESOURCE_EXHAUSTED","503","UNAVAILABLE")) or attempt==4:raise
            time.sleep(30*(attempt+1))

def crop(im):
    iw,ih=im.size
    scale=max(W/iw,H/ih)
    nw,nh=math.ceil(iw*scale),math.ceil(ih*scale)
    im=im.resize((nw,nh),Image.Resampling.LANCZOS)
    return im.crop(((nw-W)//2,(nh-H)//2,(nw+W)//2,(nh+H)//2))

def wrapped(draw,text,face,maxw):
    out=[]
    for sentence in text.split("\n"):
        words=sentence.split()
        cur=""
        for word in words:
            trial=(cur+" "+word).strip()
            if draw.textbbox((0,0),trial,font=face)[2]>maxw and cur:
                out.append(cur);cur=word
            else:cur=trial
        if cur:out.append(cur)
    return out

def make_frame(raw, caption, speaker, dest, idx, end=False):
    im=crop(Image.open(raw).convert("RGB")).convert("RGBA")
    shade=Image.new("RGBA",im.size,(0,0,0,0))
    d=ImageDraw.Draw(shade)
    d.rounded_rectangle((14,22,218,59),radius=10,fill=(7,7,19,118))
    name="루사연 | 애니사연"
    titlefont=font(19)
    b=d.textbbox((0,0),name,font=titlefont)
    d.text((24,28),name,font=titlefont,fill="#FFFFFF",stroke_width=1,stroke_fill="#080812")
    if not end:
        face=font(33)
        lines=wrapped(d,caption,face,W-68)
        # shrink long scenes to fit above the bottom-safe area
        if len(lines)>5:
            face=font(29);lines=wrapped(d,caption,face,W-68)
        lineheight=45 if len(lines)<6 else 40
        panelheight=32+lineheight*len(lines)
        top=min(H-126-panelheight,662)
        d.rounded_rectangle((20,top,W-20,top+panelheight),radius=18,fill=(0,0,0,166))
        for i,line in enumerate(lines):
            b=d.textbbox((0,0),line,font=face,stroke_width=2)
            x=(W-(b[2]-b[0]))//2
            d.text((x,top+15+i*lineheight),line,font=face,fill="#FFFFFF",stroke_width=2,stroke_fill="#13141D")
    else:
        # Last spoken phrase and CTA start in the SAME frame as Aoede says 루사연이었습니다.
        title="루사연이었습니다."
        face=font(33)
        bb=d.textbbox((0,0),title,font=face)
        d.text(((W-(bb[2]-bb[0]))//2,698),title,font=face,fill="#FFFFFF",stroke_width=3,stroke_fill="#1A1428")
        note="공감되셨다면\n구독 & 좋아요."
        for i,line in enumerate(note.split("\n")):
            f=font(28); b=d.textbbox((0,0),line,font=f)
            d.text(((W-(b[2]-b[0]))//2,765+i*43),line,font=f,fill="white",stroke_width=2,stroke_fill="#101010")
    im=Image.alpha_composite(im,shade).convert("RGB")
    im=ImageEnhance.Contrast(im).enhance(1.08)
    im=ImageEnhance.Sharpness(im).enhance(1.15)
    im.save(dest,quality=95)

def main():
    data=json.loads("{\"scenes\":[{\"text\":\"내가 태어난 날, 아빠는 기뻐하지 않았습니다. 아들이 아닌 또 딸이었으니까요.\",\"speaker\":\"narrator\",\"image_index\":0},{\"text\":\"딸만 다섯인 집의 막내. 아빠는 막내라고 버릇이 나빠진다며 유독 저에게 엄격하셨습니다.\",\"speaker\":\"narrator\",\"image_index\":1},{\"text\":\"어린 나도 사랑받고 싶었는데… 그렇게 서운함은 미움이 되었습니다.\",\"speaker\":\"narrator\",\"image_index\":2},{\"text\":\"아빠가 없는 세상에서 살면 마음이 편할 줄 알았습니다. 그런데 아빠는 너무 일찍 떠나셨습니다.\",\"speaker\":\"narrator\",\"image_index\":3},{\"text\":\"나이가 들수록 이상하게도 아빠와 함께했던 어린 시절이 자꾸만 떠오릅니다.\",\"speaker\":\"narrator\",\"image_index\":4},{\"text\":\"그때는 왜 그렇게 미웠을까요. 이제는 미워하고 싶어도 미워할 아빠가 없습니다.\",\"speaker\":\"narrator\",\"image_index\":5},{\"text\":\"아빠… 다시 어린 시절로 돌아갈 수 있다면 한 번만 꼭 안아보고 싶습니다.\",\"speaker\":\"narrator\",\"image_index\":6}],\"images\":[\"Korean mother holding newborn daughter, four older daughters nearby, father looks disappointed, nostalgic modest Korean home\",\"Father sternly scolds little daughter, she looks down, no violence\",\"Little daughter alone by window with tears, dusk\",\"Adult daughter in black mourning clothes looking at framed portrait of father, restrained grief\",\"Warm childhood memory of father and little daughter walking together beneath autumn trees, golden light\",\"Adult daughter holding old photograph of father at night, tears\",\"Dreamlike memory of adult daughter embracing father, warm sunset, bittersweet\"]}")
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    scenes=data["scenes"]
    scenes.append({"text":"루사연이었습니다.","speaker":"narrator","image_index":len(data["images"])-1})
    key=os.environ.get("GEMINI_API_KEY")
    if not key:raise RuntimeError("GEMINI_API_KEY missing from GitHub Actions secrets")
    image_client=genai.Client(api_key=key,http_options=types.HttpOptions(api_version="v1beta"))
    # Fix both characters in one original master drawing before generating 10 new frames.
    master=WORK/"character_master.jpg"
    master_prompt="Premium theatrical hand-drawn Japanese 2D action-drama cel anime character reference, intricate expressive irises, sharp ink contours, layered hair strands, dramatic angular shadows, Korean father age 40 short black hair simple brown sweater, little daughter age 7 black bob cream dress, adult version of daughter age 30 same eyes and black hair. Nostalgic warm light, refined ink lines, no text, vertical 9:16."
    print("Generating shared character identity master",flush=True)
    image_from_gemini(image_client,master_prompt,master)
    # Generate ten completely new images using that precise reference image
    relevant=list(range(len(data["images"])))
    images=[]
    for n,refidx in enumerate(relevant):
        p=WORK/f"art_{n:02d}.jpg"
        prompt="Premium hand-drawn Japanese theatrical 2D action-drama anime, sharply defined black ink contours, intricate luminous irises, detailed hair strands, strong angular cel shadows, dramatic rim lighting, saturated jewel tones, elaborate hand-painted backgrounds, dynamic cinematic composition, no pastel cartoon or simplified illustration, consistent father and daughter from reference, no text, no 3D, vertical 9:16. "+data["images"][refidx]
        print("Generating Gemini 2D anime scene",n,flush=True)
        image_from_gemini(image_client,prompt,p,reference=master)
        images.append(p)
        time.sleep(4)
    image_client.close()
    mapped=[scene["image_index"] for scene in scenes]
    clips=[];voices=[]
    for idx,scene in enumerate(scenes):
        text=scene["text"]
        speaker=scene["speaker"]
        voice="Charon" if speaker in ("son","male") else "Aoede"
        wav=WORK/f"voice_{idx:02d}.wav"
        png=WORK/f"caption_{idx:02d}.png"
        mp4=WORK/f"clip_{idx:02d}.mp4"
        synthesize_gemini(text,"Aoede",str(wav))
        make_frame(images[mapped[idx]],text,speaker,png,idx,end=(idx==len(scenes)-1))
        target=duration(wav)/RATE
        ffmpeg("-loop","1","-framerate",str(FPS),"-i",png,"-i",wav,
               "-filter_complex",f"[1:a]atempo={RATE}[a]",
               "-map","0:v","-map","[a]","-t",f"{target:.4f}",
               "-vf",f"scale={W}:{H},zoompan=z='min(zoom+0.0007,1.10)':d=1:s={W}x{H}:fps={FPS}",
               "-c:v","libx264","-preset","ultrafast","-crf","25","-pix_fmt","yuv420p",
               "-c:a","aac","-b:a","128k","-ar","24000","-ac","1","-movflags","+faststart",mp4)
        clips.append(mp4);voices.append(wav)
    # Build a strong opening headline overlay for the first three seconds, no heavy black panel.
    hook=WORK/"hook.png"
    canvas=Image.new("RGBA",(W,H),(0,0,0,0))
    hd=ImageDraw.Draw(canvas)
    headline1="아들이 아니어서"
    headline2="미움받았던 딸"
    hf=font(41)
    for k,line in enumerate((headline1,headline2)):
        bx=hd.textbbox((0,0),line,font=hf,stroke_width=3)
        hd.text(((W-(bx[2]-bx[0]))/2,285+k*61),line,font=hf,fill="#FFFFFF" if k==0 else "#FFF0A3",
                stroke_width=4,stroke_fill="#111022")
    canvas.save(hook)
    concat=WORK/"videos.txt"
    concat.write_text("".join("file '"+str(f.resolve())+"'\n" for f in clips))
    raw=WORK/"ungraded.mp4"
    ffmpeg("-f","concat","-safe","0","-i",concat,"-c","copy","-movflags","+faststart",raw)
    ffmpeg("-i",raw,"-loop","1","-i",hook,"-t",f"{duration(raw):.3f}",
           "-filter_complex","[0:v][1:v]overlay=0:0:enable='between(t,0,3)'[v]",
           "-map","[v]","-map","0:a","-c:v","libx264","-preset","veryfast","-crf","21",
           "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",OUT/"ru_sayeon_shorts.mp4")
    audios=WORK/"audios.txt"
    audios.write_text("".join("file '"+str(f.resolve())+"'\n" for f in voices))
    ffmpeg("-f","concat","-safe","0","-i",audios,"-c:a","pcm_s16le",OUT/"ru_sayeon_voice.wav")
    print("SUCCESS MP4:",OUT/"ru_sayeon_shorts.mp4",flush=True)

if __name__=="__main__":
    main()
