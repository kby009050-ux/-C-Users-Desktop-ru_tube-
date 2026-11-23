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
RATE=1.25

def ffmpeg(*args):
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)

def duration(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())

def font(size):
    for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc","/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf","C:/Windows/Fonts/malgunbd.ttf"]:
        if Path(f).exists():return ImageFont.truetype(f,size)
    raise RuntimeError("Korean font missing")

def image_from_gemini(client, prompt, output):
    model=os.environ.get("GEMINI_IMAGE_MODEL","gemini-3.1-flash-image")
    for attempt in range(3):
        try:
            res=client.models.generate_content(
                model=model,
                contents=prompt,
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
            if ("429" not in str(e) and "RESOURCE_EXHAUSTED" not in str(e)) or attempt==2:raise
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
        d.rounded_rectangle((20,748,W-20,873),radius=18,fill=(0,0,0,170))
        note="공감되셨다면\n구독과 좋아요 부탁드립니다."
        for i,line in enumerate(note.split("\n")):
            f=font(28); b=d.textbbox((0,0),line,font=f)
            d.text(((W-(b[2]-b[0]))//2,764+i*43),line,font=f,fill="white",stroke_width=2,stroke_fill="#101010")
    im=Image.alpha_composite(im,shade).convert("RGB")
    im=ImageEnhance.Contrast(im).enhance(1.08)
    im=ImageEnhance.Sharpness(im).enhance(1.15)
    im.save(dest,quality=95)

def main():
    data=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    scenes=data["scenes"]
    key=os.environ.get("GEMINI_API_KEY")
    if not key:raise RuntimeError("GEMINI_API_KEY missing from GitHub Actions secrets")
    image_client=genai.Client(api_key=key,http_options=types.HttpOptions(api_version="v1beta"))
    # Six original hand-drawn Gemini art frames, re-used with scene-dependent pans
    relevant=[0,1,2,3,4,5,6,7,8,9]
    images=[]
    for n,refidx in enumerate(relevant):
        p=WORK/f"art_{n:02d}.jpg"
        prompt=(
            "Recreate the polished, lovely, razor-sharp hand drawn 2D Japanese anime art style of the REFERENCE VIDEO described here. "
            "Reference: a classic high-budget Japanese period-drama anime SCREENSHOT of elegant young women, delicate beautiful symmetrical anime faces, luminous detailed anime eyes with fine long lashes, thin precise inked brows, refined small anime noses and small lips, gracefully flowing ink-black hair with individual perfectly inked locks, exquisite traditional fabrics and colored highlights, rich high-end layered cel animation painting. "
            "A BEAUTIFUL high quality Japanese television anime frame, remarkably crisp, meticulously clean character drawing, "
            "perfect anime proportions with gorgeous detailed eyes and glossy multidimensional hair, soft warm facial shadows but STRONG clean anime outlines, high-resolution 2D illustration, delicate cinematic lighting, detailed yet harmonious background interior architecture, vivid refined palette. "
            "The STYLE IS JAPANESE SHONEN DARK-FANTASY ANIME LIKE DEMON SLAYER VISUALS, adapted to modern Korean emotional family drama. "
            "Not historical costumes, do not copy any famous character. "
            "Create totally original characters whose drawings are AS BEAUTIFUL, AS CLEAR, AS DETAILED and AS AUTHENTICALLY JAPANESE ANIME as the female actors in the supplied reference video. "
            "For the protagonist, use an elegant 60-year-old Korean mother, graceful face with refined wrinkles, luminous distinct Japanese anime eyes, beautifully shaped silver-gray hair neatly tied back, rich burgundy cardigan. "
            "The son is a handsome 35-year-old man with beautifully drawn expressive Japanese anime eyes, neat ink-black hair and navy jacket. "
            "An emotional movie scene; sincere vivid intense facial expressions, sophisticated direction and correct anatomy. "
            "Crisp extremely fine lines, polished digital 2D CEL animation with subtle hard shadow shapes and beautiful color grading. "
            "NO sketchy black heavy borders, no grotesque exaggerated anatomy, NO oil paint or painterly realism, no watercolor, no pastel illustration, no 3D, no semi-realistic faces, no western cartoon, no collage, no text or captions, no panels, no watermark. "
            "Full-bleed single vertical 9:16 Japanese 2D anime screenshot. "
            "Depict this very specific emotional moment: "+data["images"][refidx]
        )
        print("Generating Gemini 2D anime scene",n,flush=True)
        image_from_gemini(image_client,prompt,p)
        images.append(p)
        time.sleep(4)
    image_client.close()
    mapped=[0,1,2,1,3,3,2,4,4,5,6,6,7,7,7,7,8,8,9,9,9]
    clips=[];voices=[]
    for idx,scene in enumerate(scenes):
        text=scene["text"]
        speaker=scene["speaker"]
        voice="Charon" if speaker in ("son","male") else "Aoede"
        wav=WORK/f"voice_{idx:02d}.wav"
        png=WORK/f"caption_{idx:02d}.png"
        mp4=WORK/f"clip_{idx:02d}.mp4"
        # Reuse the already-successful Gemini Aoede/Charon recordings for this exact script.
        # They are obtained from the prior successful GitHub Actions artifact.
        original=ROOT/"automation"/"prebuilt"/"build"/f"voice_{idx:02d}.wav"
        if not original.is_file():
            raise FileNotFoundError("Missing previously generated Gemini voice: "+str(original))
        import shutil
        shutil.copyfile(original,wav)
        print("Reused original Gemini voice",idx,voice,flush=True)
        make_frame(images[mapped[idx]],text,speaker,png,idx)
        target=duration(wav)/RATE
        ffmpeg("-loop","1","-framerate",str(FPS),"-i",png,"-i",wav,
               "-filter_complex",f"[1:a]atempo={RATE}[a]",
               "-map","0:v","-map","[a]","-t",f"{target:.4f}",
               "-vf",f"scale={W}:{H},zoompan=z='min(zoom+0.0007,1.10)':d=1:s={W}x{H}:fps={FPS}",
               "-c:v","libx264","-preset","ultrafast","-crf","25","-pix_fmt","yuv420p",
               "-c:a","aac","-b:a","128k","-ar","24000","-ac","1","-movflags","+faststart",mp4)
        clips.append(mp4);voices.append(wav)
    # Short 2 second text-only CTA at end; spoken ending remains in last narrated scene.
    tail=WORK/"end.png"; tailmp4=WORK/"end.mp4"
    make_frame(images[-1],"","narrator",tail,99,True)
    ffmpeg("-loop","1","-i",tail,"-t","2","-vf",f"scale={W}:{H},fps={FPS}","-c:v","libx264","-preset","ultrafast","-crf","25","-pix_fmt","yuv420p","-f","mp4",tailmp4)
    # Build a strong opening headline overlay for the first three seconds, no heavy black panel.
    hook=WORK/"hook.png"
    canvas=Image.new("RGBA",(W,H),(0,0,0,0))
    hd=ImageDraw.Draw(canvas)
    headline1="매달 돈만 요구하던 아들"
    headline2="엄마는 번호를 바꿨습니다"
    hf=font(41)
    for k,line in enumerate((headline1,headline2)):
        bx=hd.textbbox((0,0),line,font=hf,stroke_width=3)
        hd.text(((W-(bx[2]-bx[0]))/2,285+k*61),line,font=hf,fill="#FFFFFF" if k==0 else "#FFF0A3",
                stroke_width=4,stroke_fill="#111022")
    canvas.save(hook)
    # All sections encoded consistently; concat with audio present in every scene.
    # silent CTA AAC for seamless concat
    tailav=WORK/"end_av.mp4"
    ffmpeg("-i",tailmp4,"-f","lavfi","-t","2","-i","anullsrc=r=24000:cl=mono","-map","0:v","-map","1:a","-t","2","-c:v","copy","-c:a","aac","-b:a","128k",tailav)
    clips.append(tailav)
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
