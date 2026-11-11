# E Se Fosse Real — kit de simulação 3D

Canal de vídeos "E se…" (80–110 s, sem narração): cenas 3D low-poly com dados reais, relógio da simulação ("+1 HORA", "+3 DIAS"), estatística grande no topo, frase em itálico e trilha + efeitos.

## Pastas
- `_kit/` → motor (three.js): `sim.html` (player do episódio), `kit/engine.js` (render, luz, pós), `kit/city.js` (cidade procedural, ruas, árvores cúbicas, postes, fiação, carros), `kit/weather.js` (céu, chuva, enchente com reflexo, raio), `kit/sets.js` (morro com casas e deslizamento, marginal/rio, represa, mercado), `kit/people.js` (personagens Mixamo + animações), `kit/hud.css` (tipografia e telas: celular, painel de voos, régua, CTA), `render_sim.js` (render em partes), `audio_mix.py` (mixagem de trilha, leitos e efeitos), `still.js` (quadros de conferência).
- `Base/Personagens/` → 20 personagens Mixamo em GLB (T-pose, textura 768 px; convertidos com `_kit/convert.html` + `convert.js`). Os FBX originais (20–80 MB cada) ficam em `C:\Users\amori\Downloads\EFR_mixamo\chars`.
- `Base/Animacoes/` → 32 animações Mixamo (FBX sem pele, Y Bot, 30 fps; andar no lugar).
- `Base/Sons/` → efeitos e trilhas Mixkit (licença gratuita Mixkit).
- `Episodios/NNN_slug/` → `mkep.py` gera `episodio.json` (cenas, câmeras, textos, dados) + `som.json` (mixagem) + vídeo final e kit de post.

## Como renderizar um episódio
1. Copie `_kit/` para uma pasta de trabalho, `npm install`, ponha `Base/Personagens/*.glb` em `assets/mixamo/glb`, `Base/Animacoes` em `assets/mixamo/anims` e `Base/Sons` em `assets/audio`.
2. `python3 mkep.py` (gera `episodio.json`).
3. Conferir: `node still.js "[2,15,30]" teste`.
4. Render: `node render_sim.js 0 50 parts/p1 "?s=0.6" & node render_sim.js 50 100 parts/p2 "?s=0.6"` e junte com ffmpeg.
5. Som: `python3 audio_mix.py episodio.json som.json som.wav`.
