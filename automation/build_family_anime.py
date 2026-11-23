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

def image_from_gemini(client, prompt, output, reference=None):
    model=os.environ.get("GEMINI_IMAGE_MODEL","gemini-3.1-flash-image")
    for attempt in range(3):
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
        # Last spoken phrase and CTA start in the SAME frame as Aoede says 루사연이었습니다.
        title="루사연이었습니다."
        face=font(33)
        bb=d.textbbox((0,0),title,font=face)
        d.text(((W-(bb[2]-bb[0]))//2,698),title,font=face,fill="#FFFFFF",stroke_width=3,stroke_fill="#1A1428")
        note="공감되셨다면\n구독과 좋아요 부탁드립니다."
        for i,line in enumerate(note.split("\n")):
            f=font(28); b=d.textbbox((0,0),line,font=f)
            d.text(((W-(b[2]-b[0]))//2,765+i*43),line,font=f,fill="white",stroke_width=2,stroke_fill="#101010")
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
    # Fix both characters in one original master drawing before generating 10 new frames.
    master=WORK/"character_master.jpg"
    master_prompt=(
        "A single beautiful frame from a high-budget original Japanese 2D action drama anime, "
        "modern Korean apartment with exactly ONE dark grey metal entrance door and electronic keypad lock, "
        "clear two recognizable character faces: Korean mother age 58, elegant delicate anime eyes, "
        "SHORT dark brown CHIN-LENGTH BOB haircut subtly grey at temples, burgundy cardigan, NO earrings; "
        "handsome adult Korean son age 35 with SHORT tidy black hair and navy jacket. "
        "Both shown in single frame with beautiful meticulously clean 2D CEL ANIME drawing, "
        "professional character design as polished as Demon-Slayer-like Japanese anime, "
        "extraordinary detailed graceful eyes and refined faces, crisp ink lines and vivid painterly backgrounds. "
        "ABSOLUTELY no historical elements, no sliding doors, no shoji, no paper screen, no comic panels, "
        "no text, no logos, no 3D, no photo, only modern Korean apartment, vertical 9:16."
    )
    print("Generating shared character identity master",flush=True)
    image_from_gemini(image_client,master_prompt,master)
    # Generate ten completely new images using that precise reference image
    relevant=[0,1,2,3,4,5,6,7,8,9]
    images=[]
    for n,refidx in enumerate(relevant):
        p=WORK/f"art_{n:02d}.jpg"
        prompt=(
            "Preserve EXACT same characters and anime art style from the reference photo. "
            "Mother MUST have SHORT CHIN-LENGTH dark brown BOB, subtle grey highlights, burgundy cardigan, "
            "NO earrings, NO jewelry; age 58, gorgeous mature 2D Japanese anime face, delicate large luminous eyes. "
            "Son ALWAYS with same neat short black side-part hair, navy jacket, handsome anime face age 35. "
            "Modern contemporary Seoul apartment with ONE ordinary grey STEEL entrance door, white walls and "
            "digital keypad lock, NEVER shoji paper screens or wooden sliding doors or extra nested doors. "
            "If hospital scene: modern hospital bed and monitors, mother SAME BOB and cardigan. "
            "Beautiful crisp highly polished JAPANESE 2D ANIME animation screenshot, Demon-Slayer-like "
            "beautiful clean expressive character design, precisely inked delicate line art, exquisite "
            "face anatomy and natural expressive eyes, high end cel shaded jewel tones and luminous cinematic "
            "dramatic lighting. SINGLE continuous scene, vertical 9:16, no panels or composites, "
            "NO text, NO subtitles, NO logo, NO photography, NO 3D, NO watercolor. "
            "Follow this exact storytelling event: "+data["images"][refidx]
        )
        print("Generating Gemini 2D anime scene",n,flush=True)
        image_from_gemini(image_client,prompt,p,reference=master)
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
        # Original new TTS for every mother line and calm closing, not pitch/speed altered old acting.
        if speaker=="mother" or idx==len(scenes)-1:
            if idx==len(scenes)-1:
                style=("Warm casual Korean woman host closing an intimate personal story, gentle friendly "
                       "conversational delivery, neutral and relaxed with falling sentence ending, "
                       "no anger, no dramatic emphasis, no sternness. Only say the exact phrase.")
            elif idx==5:
                style=("Korean mother aged 58, feeling ill, quietly and naturally telling son she is sick, "
                       "intimate everyday Korean speaking voice, understated fatigue, no affected acting.")
            else:
                style=("Realistic ordinary Korean mother in her late 50s. Natural conversation with her son, "
                       "very restrained emotional sadness and calm conviction, genuinely conversational "
                       "familiar everyday phrasing, small meaningful pauses, clear fluid diction. "
                       "Never shout, never play anger, never stiffly declaim, never sob theatrically.")
            print("Fresh Gemini Aoede voice for mother or calm closing",idx,flush=True)
            synthesize_gemini(text,voice,str(wav),style=style)
        else:
            original=ROOT/"automation"/"prebuilt"/"build"/f"voice_{idx:02d}.wav"
            if not original.is_file(): raise FileNotFoundError(str(original))
            import shutil
            shutil.copyfile(original,wav)
            print("Preserved original narrator/son voice",idx,flush=True)
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
    headline1="매달 돈만 요구하던 아들"
    headline2="엄마는 번호를 바꿨습니다"
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
