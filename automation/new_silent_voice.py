"""Create one entirely new Korean narration for the source video 16651.mp4, NOT the unrelated money story."""
import os,sys,time,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gemini_tts import synthesize_gemini
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"automation"/"new_voice"
OUT.mkdir(parents=True,exist_ok=True)
scenes=[
("female","평생 자식을 위해 살았던 한 엄마가 있었습니다.","Gentle mature Korean female storyteller, calm natural emotional delivery."),
("female","그런데 어느 날, 아들은 차가운 눈빛으로 엄마를 바라보았습니다.","Soft subdued narrative, clear gentle everyday Korean."),
("male","엄마, 이제 우리 인생에 간섭하지 마세요.","Adult Korean man, straightforward and cold but not yelling, natural conversational diction."),
("female","내가 너한테 그렇게 짐이었니?","Korean mother late 50s, hurt but quietly asking her son, very natural restrained voice, do not cry theatrically."),
("female","그 말 한마디에, 엄마는 아무 말도 할 수 없었습니다.","Soft storyteller, sadness, measured and natural."),
("female","그동안 아끼고 사랑했던 시간들이, 한순간에 낯설어졌습니다.","Intimate soft narration, clear articulate Korean."),
("female","엄마는 조용히 가방을 챙겼습니다. 그리고 집을 나섰습니다.","Quiet subdued storytelling, gentle natural tone."),
("female","아들은 마지막까지 엄마를 붙잡지 않았습니다.","Intimate sorrowful narrative, do not shout."),
("female","뒤돌아보지 않은 건, 사랑이 없어서가 아니었습니다.","Gentle understanding, unforced emotion."),
("female","이제는 자신을 위한 삶을 살아보기로 한 것이었습니다.","Hopeful but restrained and emotional."),
("female","루사연이었습니다.","A gently smiling Korean female host signing off, warm casual normal conversational tone, no anger, no emphasis or theatrical drama. Only this text.")
]
for i,(sp,text,style) in enumerate(scenes):
 p=OUT/f"voice_{i:02d}.wav"
 print("TTS",i,flush=True)
 synthesize_gemini(text,"Charon" if sp=="male" else "Aoede",str(p),style=style)
 time.sleep(7)
manifest=[{"speaker":sp,"text":txt,"file":f"voice_{i:02d}.wav"} for i,(sp,txt,_) in enumerate(scenes)]
(OUT/"script.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
