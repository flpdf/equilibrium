"""Testes do gerenciador de impulsionamento: decisão por regras e adaptadores em dry-run."""
import copy
import json
import urllib.request
from datetime import datetime
from pathlib import Path

import pytest

import impulsionar as imp
from ads import meta, tiktok

RAIZ = Path(__file__).parent.parent
CONFIG = json.loads((RAIZ / "config" / "ads.json").read_text(encoding="utf-8"))
AGORA = datetime.fromisoformat("2026-11-12T12:00:00-03:00")
HIST = {"gasto_por_dia": {}, "gasto_por_post": {}, "ativos": [], "criados": []}


def post(id, views=5000, eng=0.08, canal="chefao", plat="instagram", h="10", tags=(), **kw):
    n = int(views * eng)
    p = {"id": id, "canal": canal, "plataforma": plat, "url": f"https://x/{id}",
         "publicado_em": f"2026-11-12T{h}:00:00-03:00", "views": views, "likes": n,
         "comentarios": 0, "compartilhamentos": 0, "salvos": 0, "seguidores_ganhos": 0, "tags": list(tags)}
    p.update(kw)
    return p


def cfg(**mud):
    c = copy.deepcopy(CONFIG)
    c.update(mud)
    return c


def ids(ds):
    return [d.post_id for d in ds]


def test_post_que_passa_e_poucos_posts_usam_so_minimos():
    ds = imp.decidir([post("a"), post("b", views=1200)], HIST, CONFIG, AGORA)
    assert set(ids(ds)) == {"a", "b"}  # menos de 3 posts: só os mínimos
    d = ds[0]
    assert d.plataforma == "instagram" and d.duracao_dias == 2 and d.orcamento >= 10


def test_abaixo_do_minimo():
    assert imp.decidir([post("a", views=500)], HIST, CONFIG, AGORA) == []
    assert imp.decidir([post("a", eng=0.01)], HIST, CONFIG, AGORA) == []


def test_fora_da_janela():
    assert imp.decidir([post("a", publicado_em="2026-11-10T10:00:00-03:00")], HIST, CONFIG, AGORA) == []


def test_tag_proibida():
    assert imp.decidir([post("a", tags=["Venda"])], HIST, CONFIG, AGORA) == []


def test_canal_e_plataforma_inativos():
    assert imp.decidir([post("a", canal="alerta-sp")], HIST, CONFIG, AGORA) == []
    c = cfg()
    c["plataformas"]["instagram"]["ativo"] = False
    assert imp.decidir([post("a")], HIST, c, AGORA) == []


def test_orcamento_diario_esgotado():
    h = {**HIST, "gasto_por_dia": {"2026-11-12": 25.0}}  # restam 5 < min 10
    assert imp.decidir([post("a")], h, CONFIG, AGORA) == []


def test_orcamento_semanal_limita():
    h = {**HIST, "gasto_por_dia": {"2026-11-08": 140.0}}  # restam 10 na semana
    ds = imp.decidir([post("a")], h, CONFIG, AGORA)
    assert [d.orcamento for d in ds] == [10.0]


def test_max_posts_por_dia():
    ms = [post("p0"), post("p1", canal="se-acontecesse"), post("p2", plat="tiktok")]
    ds = imp.decidir(ms, {**HIST}, cfg(orcamento_diario_total=100.0), AGORA)
    assert len(ds) == 2  # max_posts_por_dia = 2
    h = {**HIST, "criados": [{"post_id": "x", "criado_em": "2026-11-12T08:00:00-03:00"}]}
    assert len(imp.decidir(ms, h, cfg(orcamento_diario_total=100.0), AGORA)) == 1


def test_post_ja_impulsionado():
    h = {**HIST, "ativos": [{"post_id": "a", "plataforma": "instagram"}]}
    assert imp.decidir([post("a")], h, CONFIG, AGORA) == []
    h = {**HIST, "gasto_por_post": {"a": 10.0}}
    assert imp.decidir([post("a")], h, CONFIG, AGORA) == []


def test_percentil_com_3_ou_mais_posts_filtra():
    ms = [post("a", views=2000), post("b", views=3000), post("c", views=4000),
          post("d", views=5000), post("e", views=9000)]
    assert ids(imp.decidir(ms, HIST, CONFIG, AGORA)) == ["e"]  # só o topo passa em p80


def test_percentil_com_menos_de_3_posts_nao_filtra():
    ms = [post("a", views=2000), post("b", views=9000)]
    assert set(ids(imp.decidir(ms, HIST, CONFIG, AGORA))) == {"a", "b"}


def test_arredondamento_multiplos_de_5_e_limites():
    ms = [post("a", views=7000, eng=0.10), post("b", views=3000, eng=0.05)]
    ds = imp.decidir(ms, HIST, cfg(orcamento_diario_total=47.0, orcamento_semanal_total=300.0), AGORA)
    assert ds
    for d in ds:
        assert d.orcamento % 5 == 0 and 10 <= d.orcamento <= 40
    assert sum(d.orcamento for d in ds) <= 47.0
    assert ids(ds) == sorted(ids(ds), key=lambda i: -next(d.pontuacao for d in ds if d.post_id == i))


def test_orcamento_max_por_post():
    ds = imp.decidir([post("a")], HIST, cfg(orcamento_diario_total=100.0, orcamento_semanal_total=500.0), AGORA)
    assert ds[0].orcamento == 40.0


def test_extra_copia_midia_e_auth_code():
    ds = imp.decidir([post("a", midia_id="123", auth_code="XYZ")], HIST, CONFIG, AGORA)
    assert ds[0].extra == {"url": "https://x/a", "midia_id": "123", "auth_code": "XYZ"}


def test_exemplo_fixture():
    ms = json.loads((RAIZ / "tests/fixtures/metricas_exemplo.json").read_text(encoding="utf-8"))
    ds = imp.decidir(ms, HIST, CONFIG, AGORA)
    assert ids(ds) == ["ch-ig-4", "sa-tt-2"]


# ---- avaliar_ativos

def test_avaliar_cpm():
    a = [{"post_id": "a", "plataforma": "tiktok", "gasto": 20.0, "impressoes": 1000, "seguidores_ganhos": 0},
         {"post_id": "b", "plataforma": "tiktok", "gasto": 10.0, "impressoes": 1000, "seguidores_ganhos": 0}]
    ps = imp.avaliar_ativos(a, CONFIG)
    assert [p.post_id for p in ps] == ["a"] and ps[0].valor == 20.0 and "cpm" in ps[0].motivo


def test_avaliar_custo_por_seguidor():
    a = [{"post_id": "a", "plataforma": "instagram", "gasto": 30.0, "impressoes": 10000, "seguidores_ganhos": 10},
         {"post_id": "b", "plataforma": "instagram", "gasto": 10.0, "impressoes": 10000, "seguidores_ganhos": 50},
         {"post_id": "c", "plataforma": "instagram", "gasto": 0.5, "impressoes": 10000, "seguidores_ganhos": 0},
         {"post_id": "d", "plataforma": "instagram", "gasto": 5.0, "impressoes": 10000, "seguidores_ganhos": 0}]
    ps = imp.avaliar_ativos(a, CONFIG)
    assert [p.post_id for p in ps] == ["a", "d"] and ps[0].valor == 3.0  # d: gasto sem seguidor
    # TikTok (objetivo visualizações) não é cobrado por seguidor
    assert imp.avaliar_ativos([{**a[0], "plataforma": "tiktok"}], CONFIG) == []


# ---- adaptadores (dry-run, sem rede)

@pytest.fixture
def sem_rede(monkeypatch):
    def falha(*a, **k):
        raise AssertionError("chamada de rede em dry-run")
    monkeypatch.setattr(urllib.request, "urlopen", falha)


DEC = {"post_id": "a", "plataforma": "instagram", "canal": "chefao", "orcamento": 20.0,
       "duracao_dias": 2, "motivo": "", "pontuacao": 1.0, "extra": {"midia_id": "179", "auth_code": "AC"}}


def test_meta_dry_run(sem_rede, capsys):
    r = meta.criar(DEC, "seguidores", AGORA, confirmar=False)
    out = capsys.readouterr().out
    assert r["dry_run"] and r["ids"] == {}
    for trecho in ("OUTCOME_ENGAGEMENT", "PAUSED", '"daily_budget": 1000', "source_instagram_media_id",
                   '"179"', "BR", "age_max", "end_time", "/v21.0/"):
        assert trecho in out
    assert "access_token" not in out.lower()


def test_meta_objetivo_visualizacoes():
    assert meta.payload_campanha(DEC, "visualizacoes")["objective"] == "OUTCOME_AWARENESS"
    p = meta.payload_conjunto(DEC, "seguidores", "c1", AGORA)
    assert p["daily_budget"] == 1000 and p["targeting"]["geo_locations"] == {"countries": ["BR"]}
    assert p["end_time"].startswith("2026-11-14")


def test_tiktok_dry_run(sem_rede, capsys):
    r = tiktok.criar({**DEC, "plataforma": "tiktok"}, "visualizacoes", AGORA, confirmar=False)
    out = capsys.readouterr().out
    assert r["dry_run"] and r["ids"] == {}
    for trecho in ("tt_video/authorize/", '"auth_code": "AC"', "VIDEO_VIEWS", "location_ids",
                   "schedule_end_time", "AUTH_CODE", "BUDGET_MODE_DAY", '"budget": 10.0'):
        assert trecho in out


def test_real_sem_variaveis_falha_sem_rede(sem_rede, monkeypatch):
    from ads.comum import AdsError
    for v in meta.VARS + tiktok.VARS:
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(AdsError, match="META_ACCESS_TOKEN"):
        meta.criar(DEC, "seguidores", AGORA, confirmar=True)


def test_cli_executar_dry_run_padrao_e_confirmo(sem_rede, tmp_path, capsys):
    f = tmp_path / "decisoes.json"
    f.write_text(json.dumps([DEC]), encoding="utf-8")
    assert imp.main(["executar", str(f), "--historico", str(tmp_path / "h.json")]) == 0
    assert not (tmp_path / "h.json").exists()
    assert imp.main(["executar", str(f), "--executar"]) == 2


def test_meta_ids_por_canal(sem_rede, capsys):
    cfg = json.loads((RAIZ / "config" / "ads.json").read_text(encoding="utf-8"))
    meta.criar(DEC, "seguidores", AGORA, confirmar=False, config=cfg)
    out = capsys.readouterr().out
    assert '"instagram_user_id": "17841472492442815"' in out and '"page_id": "1506404455885952"' in out
    contas = {c: meta.contas_do_canal({"canal": c}, cfg, exigir=True)["ig_user_id"]
              for c in ("chefao", "se-acontecesse", "alerta-sp")}
    assert contas == {"chefao": "17841472492442815", "se-acontecesse": "17841453394645080",
                      "alerta-sp": "17841428163246077"}


def test_meta_canal_sem_ids_exige_ambiente(monkeypatch):
    from ads.comum import AdsError
    monkeypatch.delenv("META_PAGE_ID", raising=False)
    monkeypatch.delenv("META_IG_USER_ID", raising=False)
    with pytest.raises(AdsError, match="novo"):
        meta.contas_do_canal({"canal": "novo"}, {"canais": {}}, exigir=True)


def test_codigo_post():
    for url in ("https://www.instagram.com/reel/DQx1_a-B/", "https://instagram.com/chefaodostreinos/reel/DQx1_a-B?igsh=1",
                "https://www.instagram.com/p/DQx1_a-B/", "https://www.instagram.com/reels/DQx1_a-B/"):
        assert meta.codigo_post(url) == "DQx1_a-B"
    assert meta.codigo_post("https://tiktok.com/@x/video/1") is None


def test_preencher_midia_ids_casa_pelo_shortcode():
    cfg = json.loads((RAIZ / "config" / "ads.json").read_text(encoding="utf-8"))
    chamadas = []

    def listar(ig, token):
        chamadas.append(ig)
        return [{"id": "999", "permalink": "https://www.instagram.com/reel/ABC/"}]

    posts = [{"id": "a", "canal": "chefao", "plataforma": "instagram", "url": "https://www.instagram.com/reel/ABC/?x=1"},
             {"id": "b", "canal": "chefao", "plataforma": "instagram", "url": "https://www.instagram.com/reel/ZZZ/"},
             {"id": "c", "canal": "chefao", "plataforma": "instagram", "midia_id": "1", "url": ""},
             {"id": "d", "canal": "chefao", "plataforma": "tiktok", "url": ""}]
    assert meta.preencher_midia_ids(posts, cfg, "t", listar=listar) == ["b"]
    assert posts[0]["midia_id"] == "999" and posts[2]["midia_id"] == "1" and "midia_id" not in posts[3]
    assert chamadas == ["17841472492442815"]  # uma consulta por conta


def test_meta_sem_midia_id_falha_antes_da_rede(sem_rede):
    from ads.comum import AdsError
    sem = {**DEC, "extra": {}}
    with pytest.raises(AdsError, match="midia_id"):
        meta.criar(sem, "seguidores", AGORA, confirmar=True)


def test_executar_pendente_nao_derruba_as_outras(sem_rede, tmp_path, capsys, monkeypatch):
    for v in ("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "TIKTOK_ACCESS_TOKEN", "TIKTOK_ADVERTISER_ID"):
        monkeypatch.setenv(v, "x")
    criados = []
    monkeypatch.setattr(tiktok, "criar", lambda d, *a, **k: criados.append(d["post_id"]) or
                        {"post_id": d["post_id"], "plataforma": "tiktok", "dry_run": True})
    f = tmp_path / "d.json"
    f.write_text(json.dumps([{**DEC, "extra": {}}, {**DEC, "post_id": "b", "plataforma": "tiktok"}]))
    rc = imp.main(["executar", str(f), "--executar", "--confirmo", "--historico", str(tmp_path / "h.json")])
    assert rc == 1 and criados == ["b"]
    assert "PENDENTE a (instagram)" in capsys.readouterr().err
