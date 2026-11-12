# Vídeo de produto a partir de foto (recorte + vetor + cenário IA)

O rótulo nunca passa pela IA de vídeo (deforma texto e logo). Fluxo testado (Memo Life, 06/11/2026, 55 créditos):
1. Foto: recorte o produto sozinho em alta (PIL; prints de celular vêm em 1188×2576). Fundo liso, produto inteiro.
2. Recorte com fundo transparente, local e grátis: `rembg` com `new_session('isnet-general-use')` (o modelo padrão é lento). Corte pelo bbox do alfa (> 40). Confira sobre fundo colorido.
3. Vetor (SVG), local: `vtracer.convert_image_to_svg_py(png, svg, colormode='color', hierarchical='stacked', mode='spline', filter_speckle=6, color_precision=5, layer_difference=24)`. Vira ilustração flat (texto miúdo some). Uso que funcionou: "desenho se montando" com cairosvg acumulando os `<path>` em ~40 passos (curva `(i/N)**1.6`) e fusão para a foto real.
4. Cenários IA sem o produto, câmera parada: "empty pedestal… locked-off static camera, no camera movement" e `negativePrompt` "bottle, product, text, logo, camera movement". Câmera parada é o que faz o recorte pertencer à cena.
5. Composição em Python (PIL + numpy → ffmpeg): produto sobre os clipes com sombra elíptica desfocada, entrada deslizando, zoom lento, chips de texto, tela final. Molde: `C:\Users\amori\Downloads\memo-life\processo\compose_produto.py`.
6. Roteiro que funcionou (17 s): gancho com pessoa → produto entra → desenho vetorial se monta e vira a foto → produto no pedestal com ingredientes → "60 cápsulas · 500 mg" + "garanta o seu no link". Rodapé fixo com o aviso legal.
7. Suplemento: só composição, quantidade e rotina. Nada de efeito ("melhora memória", "mais foco"): ANVISA proíbe alegação terapêutica e o TikTok Shop derruba. Rodapé: "Suplemento alimentar. Não substitui uma alimentação equilibrada."
