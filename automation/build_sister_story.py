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
    data=json.loads("{\"scenes\":[{\"text\":\"새언니, 우리 오빠랑 결혼했으면 이 정도는 당연히 해야 하는 거 아니야?\",\"speaker\":\"sister\",\"image_index\":0},{\"text\":\"결혼하고 나서 시누이는 주말마다 예고도 없이 저희 집에 찾아왔습니다.\",\"speaker\":\"narrator\",\"image_index\":1},{\"text\":\"밥을 차려주면 맛이 없다고 불평하고, 먹고 난 그릇조차 치우지 않았습니다. 그러던 어느 날이었습니다.\",\"speaker\":\"narrator\",\"image_index\":2},{\"text\":\"새언니, 내일 친구들 데리고 올 테니까 음식 좀 준비해 놔. 배달 음식 말고 직접 만들어.\",\"speaker\":\"sister\",\"image_index\":3},{\"text\":\"기가 막혀서 한마디 했습니다.\",\"speaker\":\"narrator\",\"image_index\":4},{\"text\":\"아가씨, 여기가 식당이에요?\",\"speaker\":\"narrator\",\"image_index\":4},{\"text\":\"우리 오빠 집인데 내가 마음대로 오지도 못해?\",\"speaker\":\"sister\",\"image_index\":3},{\"text\":\"아가씨 오빠 집이기도 하지만 제 집이기도 해요. 그리고 아가씨 친구들 밥은 아가씨가 차리세요.\",\"speaker\":\"narrator\",\"image_index\":4},{\"text\":\"그날 이후 시누이는 저에게 싸가지 없는 새언니라고 소문을 내고 다녔습니다. 하지만 저는 오히려 마음이 편해졌습니다.\",\"speaker\":\"narrator\",\"image_index\":5},{\"text\":\"배려를 당연하게 여기는 사람에게는 더 이상 배려할 필요가 없습니다. 가족이라는 이유로 무례함까지 참아줄 필요는 없으니까요.\",\"speaker\":\"narrator\",\"image_index\":6}],\"images\":[\"Rude younger Korean sister-in-law with long auburn hair and green blouse points arrogantly at married woman with black bob and cream sweater in modern apartment\",\"Younger sister-in-law enters uninvited through modern steel apartment door, married woman surprised\",\"Sister-in-law sneers at home cooked Korean meal, dirty dishes on table, married woman looks exhausted\",\"Arrogant sister-in-law lounging on couch demanding food, holding smartphone, disdainful expression\",\"Married woman calmly but firmly confronts sister-in-law in living room, determined eyes, sister-in-law shocked\",\"Sister-in-law angrily gossiping on smartphone outdoors, alone\",\"Married woman alone peacefully drinking tea by sunny apartment window, serene expression\"]}")
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    scenes=data["scenes"]
    scenes.extend([{"text":"오늘의 이야기에 공감하셨다면, 구독과 좋아요로 함께해 주세요.","speaker":"narrator","image_index":len(data["images"])-1},{"text":"루사연이었습니다.","speaker":"narrator","image_index":len(data["images"])-1}])
    key=os.environ.get("GEMINI_API_KEY")
    if not key:raise RuntimeError("GEMINI_API_KEY missing from GitHub Actions secrets")
    image_client=genai.Client(api_key=key,http_options=types.HttpOptions(api_version="v1beta"))
    # Fix both characters in one original master drawing before generating 10 new frames.
    master=WORK/"character_master.jpg"
    master_prompt="Premium theatrical hand-drawn Japanese 2D action-drama cel anime character reference, intricate expressive irises, sharp ink contours, layered hair strands, dramatic angular shadows, two distinct adult Korean women, married narrator age 34 black chin-length bob cream sweater, rude younger sister-in-law age 27 long auburn hair green blouse, modern Korean apartment, cinematic light, refined ink lines, no text, vertical 9:16."
    print("Generating shared character identity master",flush=True)
    image_from_gemini(image_client,master_prompt,master)
    # Generate ten completely new images using that precise reference image
    relevant=list(range(len(data["images"])))
    images=[]
    for n,refidx in enumerate(relevant):
        p=WORK/f"art_{n:02d}.jpg"
        prompt="Premium hand-drawn Japanese theatrical 2D action-drama anime, sharply defined black ink contours, intricate luminous irises, detailed hair strands, strong angular cel shadows, dramatic rim lighting, saturated jewel tones, elaborate hand-painted backgrounds, dynamic cinematic composition, no pastel cartoon or simplified illustration, consistent two adult women from reference, contemporary Korean apartment and clothing, no text, no 3D, vertical 9:16. "+data["images"][refidx]
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
        synthesize_gemini(text,"Kore" if speaker=="sister" else "Aoede",str(wav))
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
    headline1="시누이가 저를"
    headline2="가정부로 생각합니다"
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
