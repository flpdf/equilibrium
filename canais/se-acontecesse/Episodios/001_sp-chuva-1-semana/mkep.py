import json
SUN={}
day={"storm":0,"rain":0,"wet":0}
B=[]
def beat(t0,t1,cam,env,**k):
    b={"t":[t0,t1],"cam":cam,"env":env}; b.update(k); B.append(b)
# 0 gancho
beat(0,4.2,[[-180,330,-560],[0,0,120],45,[-130,250,-420],[0,0,160],45],{**day,"fogNear":700,"fogFar":3800},
  title='E se São Paulo<br>não parasse de <em>chover</em><br>por 1 semana?',fx={"hand":0})
# 1 manhã normal
beat(4.2,8.2,[[-13.6,1.7,-34],[-10.5,5,60],40,[-13.6,1.7,-27],[-10.5,5,66],40],{**day},timer='+0',gauge=[0,0],
  cap='Segunda-feira, 7h. Um dia normal em São Paulo.',people=[{"crowd":{"n":16,"xs":[-15.2,-16.4,-19.8],"z0":-24,"z1":75,"stand":0.2}}])
# 2 nuvens chegando (timelapse)
beat(8.2,12.4,[[-6,34,-60],[0,22,200],50,[-6,34,-54],[0,24,200],50],{"storm":0,"rain":0,"wet":0},env2={"storm":0.95,"rain":0.35,"wet":0.3},
  timer='+0',gauge=[0,1],cap='Às 7h, começa a chover.<br>E não para mais.',fx={"cloud":25,"flash":[3.6],"hand":0.02})
# 3 +1 hora
beat(12.4,17.4,[[-13.6,1.7,-12],[-10.5,4.5,80],40,[-13.6,1.7,-4],[-10.5,4.5,88],40],{"storm":1,"rain":1,"wet":0.85},timer='+1 HORA',gauge=[1,7],
  stat={"v":1154,"suf":" mm","s":"a chuva de novembro a março,<br>em 7 dias"},cap='Cinco meses de chuva,<br>comprimidos em uma semana.',people=[{"crowd":{"n":10,"xs":[-15.4,-16.6],"z0":-14,"z1":80,"walks":["Running","HoldingWalk","CarefulWalk"],"speed":2.6}}])
# 4 alerta no celular
beat(17.4,21.6,[[-12,1.7,-4],[-3,4.5,88],40,[-12,1.7,-2],[-3,4.5,90],40],{"storm":1,"rain":1,"wet":0.9},timer='+2 HORAS',gauge=[7,14],
  cap='Todos os celulares da cidade<br>tocam ao mesmo tempo.',fx={"overlay":"phone","blur":9,"dim":0.55})
# 5 +6 horas, água na rua
beat(21.6,26.4,[[-11.5,0.55,-8],[-2,1.6,60],42,[-11.5,0.5,-2],[-2,1.6,66],42],{"storm":1,"rain":1,"wet":1,"waterY":0.08},env2={"waterY":0.16},timer='+6 HORAS',gauge=[14,41],
  stat={"n":"7 mm","s":"por hora. Toda hora.<br>Sem nenhuma pausa."},cap='Não é uma tempestade.<br>É uma chuva que não acaba.',fx={"traffic":0.5})
# 6 +1 dia
beat(26.4,31.4,[[-6,30,-80],[0,0,40],46,[-5,24,-60],[0,0,50],46],{"storm":1,"rain":1,"wet":1,"waterY":0.3},env2={"waterY":0.42},timer='+1 DIA',gauge=[41,165],
  stat={"v":165,"suf":" mm","s":"em 24h: mais que o pior dia<br>da história de SP (151,8 mm, 1988)"},cap='E amanhã tem mais.<br>E depois também.',fx={"traffic":0.15,"stall":0.42,"flash":[1.2],"shake":0})
# 7 marginal transborda
beat(31.4,36.6,[[-4012,30,-170],[-4000,-3,90],46,[-4010,26,-140],[-4000,-3,100],46],{"storm":1,"rain":1,"wet":1,"water":"river","waterY":-2.6,"fogNear":120,"fogFar":1400},env2={"waterY":0.75},timer='+1 DIA',gauge=[165,200],
  cap='Tietê e Pinheiros saem do leito.<br>As marginais viram rio.',fx={"traffic":1,"shadow":160})
# 8 morro
beat(36.6,41.8,[[4000-150,62,-150],[4000+10,46,90],46,[4000-135,58,-130],[4000+10,46,95],46],{"storm":1,"rain":1,"wet":1,"fogNear":150,"fogFar":1600},timer='+2 DIAS',gauge=[200,330],
  stat={"v":185,"suf":" mil","s":"moradias em área de risco<br>de deslizamento na cidade"},cap='O solo encharcado<br>começa a ceder.',fx={"slide":[0,1],"slideAt":1.3,"shake":0.6,"shakeAt":2.2,"shadow":200})
# 9 árvore na fiação (anoitecendo)
beat(41.8,46.4,[[9,2.4,24],[-17,5.5,44],46,[8,2.4,27],[-17,5.5,44],46],{"storm":1,"rain":1,"wet":1,"night":0.65,"lit":0.5,"waterY":0.45},timer='+2 DIAS',gauge=[330,360],
  cap='Árvores caem sobre a fiação.',fx={"tree":{"pos":[-18.6,0.2,42],"at":1.0,"ang":-1.25,"dir":1,"spark":[-17,7.6,42]},"flash":[1.85,2.3],"flashK":0.8,"lampsOffAt":2.0,"blackAfter":0.85,"traffic":0,"stall":0.45,"shake":0.5,"shakeAt":1.9})
# 10 apagão (aérea noturna)
beat(46.4,51.6,[[-320,430,-720],[0,0,200],48,[-280,390,-640],[0,0,220],48],{"storm":0.85,"rain":0.8,"wet":1,"night":1,"lit":0.55,"blackR":0,"fogNear":500,"fogFar":2600,"blackC":[60,250],"waterY":0.5},env2={"blackR":1100},
  timer='+3 DIAS',gauge=[360,495],stat={"v":2.1,"dec":1,"suf":" milhões","s":"de imóveis ficaram sem luz<br>em um único temporal (2023)"},cap='Bairros inteiros apagam.',fx={"flash":[4.2],"hand":0})
# 11 voos
beat(51.6,56.2,[[-12,1.7,-4],[-3,4.5,88],40,[-12,1.7,-2],[-3,4.5,90],40],{"storm":1,"rain":1,"wet":1,"night":0.3,"waterY":0.6},timer='+4 DIAS',gauge=[495,580],
  cap='Congonhas fecha.<br>Ônibus e trens param.',fx={"overlay":"board","blur":10,"dim":0.45})
# 12 mercado
beat(56.2,61.0,[[0,1.7,-6000-34],[0,1.6,-6000+30],44,[0,1.7,-6000-28],[0,1.6,-6000+30],44],{"storm":1,"rain":0,"wet":0.6,"waterY":0.04,"lamps":True},timer='+4 DIAS',gauge=[580,660],
  cap='A Ceagesp alaga.<br>A comida para de chegar.',fx={"fill":0.12,"shadow":60,"hand":0.03})
# 13 água acima dos carros
beat(61.0,66.6,[[-12,2.4,-14],[-3,1.5,60],42,[-12,2.4,-6],[-3,1.5,66],42],{"storm":1,"rain":1,"wet":1,"waterY":1.0},env2={"waterY":1.45},timer='+5 DIAS',gauge=[660,825],
  cap='Nas ruas baixas, a água<br>passa do teto dos carros.',fx={"traffic":0,"stall":1.4,"float":1,"flash":[3.8]})
# 14 régua 1,15 m
beat(66.6,72.6,[[-5.2,1.75,-2],[-6.2,1.0,12],38,[-5.4,1.7,0.5],[-6.2,1.0,12],38],{"storm":1,"rain":1,"wet":1,"waterY":1.15},timer='+6 DIAS',gauge=[825,990],
  stat={"n":"1,15 m","s":"se nada escoasse, a água<br>cobriria a cidade até aqui"},cap='1.154 mm de chuva = uma lâmina<br>de 1,15 m sobre toda a capital.',
  fx={"overlay":"ruler","ruler":{"base":[-5.1,0.0,12],"h":1.15},"traffic":0,"stall":1.15,"float":0.6},people=[{"char":"Leonard","anim":"LookingAround","pos":[-6.2,0.0,12.4],"rot":3.0},{"char":"Kate","anim":"Terrified","pos":[-10.5,0.0,20],"rot":2.6}])
# 15 volume total (aérea)
beat(72.6,78.4,[[-260,300,-520],[0,0,160],46,[-170,240,-380],[0,0,190],46],{"storm":1,"rain":0.9,"wet":1,"waterY":1.6,"fogNear":300,"fogFar":2200},timer='+6 DIAS',gauge=[990,1100],
  stat={"n":"1,76 bilhão","s":"de m³ de água sobre a capital", "size":118},cap='Daria para encher 700 mil<br>piscinas olímpicas.',fx={"traffic":0,"stall":1.6,"float":1,"flash":[2.5]})
# 16 céu abre
beat(78.4,83.6,[[-5,34,-120],[0,6,120],44,[-4,28,-95],[0,6,140],44],{"storm":0.95,"rain":0.9,"wet":1,"waterY":1.2},env2={"storm":0.25,"rain":0,"waterY":0.9},timer='+7 DIAS',gauge=[1100,1154],
  cap='No sétimo dia, o céu abre.',fx={"traffic":0,"stall":1.0,"float":0.3,"cloud":6})
# 17 represa
beat(83.6,90.0,[[-40,46,6000-160],[0,-6,6000+250],50,[20,40,6000-120],[0,-6,6000+250],50],{"storm":0.1,"rain":0,"wet":0.3,"water":"dam","waterY":-19,"fogNear":900,"fogFar":5200,"refl":0.55},env2={"waterY":-1.5},timer='+1 MÊS',gauge=[1154,1154],
  stat={"n":"1,8×","s":"o volume do Sistema Cantareira,<br>que abastece quase metade da Grande SP"},cap='Em 2014, ele secou até o volume morto.<br>Essa semana o encheria quase 2 vezes.',fx={"shadow":400})
# 18 um ano depois
beat(90.0,95.0,[[-13.6,1.7,44],[-10.5,5,-60],40,[-13.6,1.7,38],[-10.5,5,-66],40],{**day},timer='+1 ANO',gauge=[0,0],
  cap='A cidade seca. Mas a pergunta fica:<br>ela estaria pronta?',people=[{"crowd":{"n":16,"xs":[-15.4,-16.6,-19.6],"z0":-60,"z1":46,"stand":0.2}}])
# 19 CTA
beat(95.0,100.0,[[-220,280,-460],[0,40,200],46,[-200,260,-420],[0,40,220],46],{"storm":0.2,"rain":0,"wet":0,"exposure":0.9,"fogNear":700,"fogFar":3800},fx={"overlay":"cta","sun":[-0.7,0.18,0.6],"hand":0,"blur":5,"dim":0.5},fadeOut=0.6)
EP={"dur":100,"timerLabel":"SEM PARAR DE CHOVER","gaugeMax":1154,"gaugeRec":151.8,"beats":B}
json.dump(EP,open('episodio.json','w'),ensure_ascii=False,indent=1)
print(len(B))
