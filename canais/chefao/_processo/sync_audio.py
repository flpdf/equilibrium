"""Encaixa as 10 falas da narração no início de cada cena.
uso: python3 sync_audio.py narracao.mp3 words.json saida.wav
words.json = lista de palavras do ElevenLabs Scribe [{"text","start","end"},...] (como veio do transcribe).
As falas são separadas pelo maior intervalo entre palavras: a fala N termina na palavra que fecha com . ! ou ? (as 10 falas do roteiro)."""
import json,subprocess,sys
mp3,wj,out=sys.argv[1:4]
words=[w for w in json.load(open(wj)) if not (w["text"].startswith("[") and w["text"].endswith("]"))]
lines=[];cur=[]
for w in words:
    cur.append(w)
    if w["text"].rstrip().endswith((".","!","?")) and not w["text"].rstrip().endswith("..."): lines.append(cur);cur=[]
if cur: lines.append(cur)
# o roteiro tem 10 falas; se uma fala tiver 2 frases (ex: "Pronto. Agachamento desbloqueado!"), junte pelo número de falas pedido
script=json.load(open("narration.json"))["lines"]
want=len(script)
# junta frases para bater com as falas do roteiro, comparando nº de palavras
import re
def nw(s): return len([x for x in re.sub(r"\[[^\]]*\]","",s).split() if x])
merged=[];i=0
for s in script:
    target=nw(s);grp=[]
    while i<len(lines) and len(grp)<target: grp+=lines[i];i+=1
    merged.append(grp)
assert len(merged)==want and all(merged), f"falas {len(merged)} != {want}"
scenes=[0.0,3.4,7.2,10.4,13.6,16.8,20.0,23.2,26.4,29.6]
cuts=[0.0]
for a,b in zip(merged,merged[1:]): cuts.append((a[-1]["end"]+b[0]["start"])/2)
dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",mp3]).decode())
cuts.append(dur)
parts=[];lab=""
for i in range(want):
    a,b=cuts[i],cuts[i+1];L=b-a;slot=(scenes[i+1] if i+1<len(scenes) else 33.0)-scenes[i]
    tempo=max(1.0,min(1.25,L/(slot-0.1)))  # acelera até 25% se a fala não couber na cena
    d=int((scenes[i]+(0.05 if i else 0))*1000)
    f=f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS"+(f",atempo={tempo:.3f}" if tempo>1.0 else "")
    Lo=L/tempo
    f+=f",afade=t=in:d=0.01,afade=t=out:st={max(0,Lo-0.03):.3f}:d=0.03,adelay={d}|{d}[s{i}]"
    parts.append(f);lab+=f"[s{i}]"
    print(f"fala {i+1}: {L:.2f}s na cena de {slot:.1f}s" + (f" (acelerada {tempo:.2f}x)" if tempo>1 else ""))
fc=";".join(parts)+";"+lab+f"amix=inputs={want}:normalize=0:duration=longest,apad=whole_dur=37,loudnorm=I=-14:TP=-1.5:LRA=11[o]"
subprocess.run(["timeout","120","ffmpeg","-y","-v","error","-i",mp3,"-filter_complex",fc,"-map","[o]","-ar","44100","-ac","2","-t","37",out],check=True)
print("ok",out)
