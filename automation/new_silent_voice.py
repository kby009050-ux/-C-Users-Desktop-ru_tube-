"""Create one entirely new Korean narration for the source video 16651.mp4, NOT the unrelated money story."""
import os,sys,time,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gemini_tts import synthesize_gemini
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"automation"/"new_voice"
OUT.mkdir(parents=True,exist_ok=True)
scenes=[
  [
    "female",
    "주인을 버린 건 사람이었지만, 끝까지 사람을 믿은 건 이 강아지였습니다.",
    "Emotional Korean female storyteller, natural gentle tone, powerful short opening hook, not overacting."
  ],
  [
    "female",
    "비가 쏟아지던 날, 한 여자는 강아지를 길가에 버리고 떠났습니다.",
    "Korean female narrator, softly sorrowful, clear pronunciation, not dramatic."
  ],
  [
    "female",
    "강아지는 차가 사라진 방향을 하염없이 바라봤습니다.",
    "Subdued gentle female narration, slight pause after sentence."
  ],
  [
    "female",
    "하루가 지나고, 또 하루가 지나도 그 자리를 떠나지 않았습니다.",
    "Kindly female voice, touching natural pauses, restrained sadness."
  ],
  [
    "female",
    "그때 한 할머니가 조심스럽게 다가왔습니다.",
    "Gentle warm female Korean narrator, calm natural voice."
  ],
  [
    "female",
    "아가야… 너도 버림받았니?",
    "A Korean grandmother late 70s speaking to a small dog, soft warm compassionate and naturally intimate tone, not theatrical."
  ],
  [
    "female",
    "할머니는 매일 따뜻한 밥과 물을 가져왔습니다.",
    "Gentle friendly Korean female narrator, soft smile in voice."
  ],
  [
    "female",
    "사실 할머니도 얼마 전, 평생을 함께한 가족을 떠나보내고 혼자 남겨졌습니다.",
    "Emotional but restrained female storytelling, intimate."
  ],
  [
    "female",
    "어느 날, 할머니가 울먹이며 말했습니다.",
    "Tender female narrator, subtle sorrow."
  ],
  [
    "female",
    "나는 이제… 아무도 기다리지 않으려고 했는데.",
    "Old Korean grandmother with natural gentle grief, breathy and understated, only the exact words."
  ],
  [
    "female",
    "그때 강아지가 할머니의 손에 조용히 얼굴을 기댔습니다.",
    "Korean female narrator, warm hopeful tone."
  ],
  [
    "female",
    "할머니는 강아지를 꼭 끌어안고 말없이 울었습니다.",
    "Gentle heartfelt Korean narrator, warm but not melodramatic."
  ],
  [
    "female",
    "그날 두 외로운 존재는 마침내 서로의 가족이 되었습니다.",
    "Uplifting and tender feminine Korean narrator, calm warm hope."
  ],
  [
    "female",
    "루사연이었습니다.",
    "Warm casual Korean female host sign-off, friendly relaxed gentle voice, no anger and no dramatic emphasis."
  ]
]

for i,(sp,text,style) in enumerate(scenes):
 p=OUT/f"voice_{i:02d}.wav"
 print("TTS",i,flush=True)
 synthesize_gemini(text,"Charon" if sp=="male" else "Aoede",str(p),style=style)
 time.sleep(7)
manifest=[{"speaker":sp,"text":txt,"file":f"voice_{i:02d}.wav"} for i,(sp,txt,_) in enumerate(scenes)]
(OUT/"script.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
