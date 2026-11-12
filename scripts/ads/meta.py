"""Adaptador Meta (Instagram) para a Marketing API v21.0, só com urllib.

Fluxo: campanha -> conjunto de anúncios -> criativo (reel existente) -> anúncio.
Sem `confirmar`, nada é enviado: imprime os payloads exatos e não toca a rede.
Variáveis: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID (act_123).
Página e Instagram vêm de config/ads.json (canais.<canal>.meta); META_PAGE_ID e
META_IG_USER_ID no ambiente só servem de reserva para canal sem esse bloco.
"""
from __future__ import annotations

import json
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Any

from ads.comum import AdsError, chamar, mostrar, variaveis

VERSAO = "v21.0"
BASE = f"https://graph.facebook.com/{VERSAO}"
VARS = ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]
RESERVA = ["META_PAGE_ID", "META_IG_USER_ID"]

# objetivo da plataforma (config) -> (objective, optimization_goal)
OBJETIVOS = {
    "seguidores": ("OUTCOME_ENGAGEMENT", "PROFILE_VISIT"),
    "visualizacoes": ("OUTCOME_AWARENESS", "THRUPLAY"),
}


def _nome(d: dict[str, Any]) -> str:
    return f"eq-{d['canal']}-{d['post_id']}"


def payload_campanha(d: dict[str, Any], objetivo: str) -> dict[str, Any]:
    obj, _ = OBJETIVOS[objetivo]
    return {
        "name": _nome(d),
        "objective": obj,
        "status": "PAUSED",  # nasce pausada; ativar é decisão manual no Ads Manager
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
    }


def payload_conjunto(d: dict[str, Any], objetivo: str, campanha_id: str, agora: datetime) -> dict[str, Any]:
    _, meta = OBJETIVOS[objetivo]
    dias = d["duracao_dias"]
    return {
        "name": _nome(d),
        "campaign_id": campanha_id,
        "daily_budget": round(d["orcamento"] / dias * 100),  # centavos
        "billing_event": "IMPRESSIONS",
        "optimization_goal": meta,
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "targeting": {
            "geo_locations": {"countries": ["BR"]},
            "age_min": 18,
            "age_max": 45,
            "publisher_platforms": ["instagram"],
            "instagram_positions": ["stream", "reels"],
        },
        "start_time": agora.isoformat(),
        "end_time": (agora + timedelta(days=dias)).isoformat(),
        "status": "PAUSED",
    }


def contas_do_canal(d: dict[str, Any], config: dict[str, Any] | None, exigir: bool) -> dict[str, str]:
    """Página e Instagram do canal: config/ads.json primeiro, ambiente como reserva."""
    bloco = ((config or {}).get("canais", {}).get(d["canal"]) or {}).get("meta") or {}
    if bloco.get("page_id") and bloco.get("ig_user_id"):
        return {"page_id": str(bloco["page_id"]), "ig_user_id": str(bloco["ig_user_id"])}
    try:
        env = variaveis(RESERVA, exigir=exigir)
    except AdsError:
        raise AdsError(f"Canal {d['canal']}: sem canais.{d['canal']}.meta em config/ads.json "
                       "e sem META_PAGE_ID/META_IG_USER_ID no ambiente") from None
    return {"page_id": env["META_PAGE_ID"], "ig_user_id": env["META_IG_USER_ID"]}


def payload_criativo(d: dict[str, Any], contas: dict[str, str]) -> dict[str, Any]:
    midia = d.get("extra", {}).get("midia_id") or "<midia_id do reel>"
    return {
        "name": _nome(d),
        "object_story_spec": {
            "page_id": contas["page_id"],
            "instagram_user_id": contas["ig_user_id"],
        },
        "source_instagram_media_id": midia,
    }


def payload_anuncio(d: dict[str, Any], conjunto_id: str, criativo_id: str) -> dict[str, Any]:
    return {
        "name": _nome(d),
        "adset_id": conjunto_id,
        "creative": {"creative_id": criativo_id},
        "status": "PAUSED",
    }


def _post(caminho: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
    campos = {k: v if isinstance(v, str) else json.dumps(v) for k, v in payload.items()}
    campos["access_token"] = token
    corpo = urllib.parse.urlencode(campos).encode()
    return chamar(f"{BASE}/{caminho}", corpo, {"Content-Type": "application/x-www-form-urlencoded"})


def _id(resp: dict[str, Any], etapa: str) -> str:
    if "id" not in resp:
        raise AdsError(f"Meta/{etapa}: resposta sem id: {json.dumps(resp)[:200]}")
    return str(resp["id"])


def codigo_post(url: str) -> str | None:
    """Shortcode do link do Instagram (/reel/X/, /reels/X/, /p/X/, /tv/X/)."""
    m = re.search(r"instagram\.com/(?:[^/?#]+/)?(?:reels?|p|tv)/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def listar_midias(ig_user_id: str, token: str, limite: int = 50) -> list[dict[str, Any]]:
    """Mídias recentes da conta (id, permalink, timestamp). Exige instagram_basic no token."""
    q = urllib.parse.urlencode({"fields": "id,permalink,timestamp,media_product_type",
                                "limit": limite, "access_token": token})
    return chamar(f"{BASE}/{ig_user_id}/media?{q}", None, {}).get("data", [])


def preencher_midia_ids(posts: list[dict[str, Any]], config: dict[str, Any], token: str,
                        listar=listar_midias) -> list[str]:
    """Põe `midia_id` nos posts de Instagram que não têm, casando o shortcode do `url`
    com o permalink das mídias da conta do canal. Devolve os ids que ficaram sem par."""
    faltam = [p for p in posts if p.get("plataforma") == "instagram" and not p.get("midia_id")]
    cache: dict[str, dict[str, str]] = {}
    sem_par = []
    for p in faltam:
        codigo = codigo_post(p.get("url", ""))
        try:
            ig = contas_do_canal(p, config, exigir=True)["ig_user_id"]
        except AdsError:
            sem_par.append(p.get("id", "?"))
            continue
        if ig not in cache:
            cache[ig] = {c: str(m["id"]) for m in listar(ig, token)
                         if (c := codigo_post(m.get("permalink", "")))}
        if codigo and codigo in cache[ig]:
            p["midia_id"] = cache[ig][codigo]
        else:
            sem_par.append(p.get("id", "?"))
    return sem_par


def criar(d: dict[str, Any], objetivo: str, agora: datetime, confirmar: bool,
          config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cria (ou simula) o anúncio. Devolve o registro para o historico_ads.json."""
    if confirmar and not d.get("extra", {}).get("midia_id"):
        raise AdsError(f"Post {d['post_id']}: sem midia_id do reel; rode `impulsionar.py midia` "
                       "ou ponha midia_id em metricas.json")
    env = variaveis(VARS, exigir=confirmar)
    contas = contas_do_canal(d, config, exigir=confirmar)
    conta = env["META_AD_ACCOUNT_ID"]
    ph = lambda n: f"<{n}>"  # noqa: E731
    etapas = [
        ("campanha", f"{conta}/campaigns", payload_campanha(d, objetivo)),
        ("conjunto", f"{conta}/adsets", None),
        ("criativo", f"{conta}/adcreatives", payload_criativo(d, contas)),
        ("anuncio", f"{conta}/ads", None),
    ]
    ids: dict[str, str] = {}
    for etapa, caminho, payload in etapas:
        if etapa == "conjunto":
            payload = payload_conjunto(d, objetivo, ids.get("campanha", ph("campanha_id")), agora)
        elif etapa == "anuncio":
            payload = payload_anuncio(d, ids.get("conjunto", ph("conjunto_id")), ids.get("criativo", ph("criativo_id")))
        if not confirmar:
            mostrar(f"Meta {etapa}", f"/{VERSAO}/{caminho}", payload)
            continue
        ids[etapa] = _id(_post(caminho, payload, env["META_ACCESS_TOKEN"]), etapa)
    return {
        "post_id": d["post_id"], "plataforma": "instagram", "canal": d["canal"],
        "orcamento": d["orcamento"], "duracao_dias": d["duracao_dias"],
        "criado_em": agora.isoformat(), "dry_run": not confirmar, "ids": ids,
    }
