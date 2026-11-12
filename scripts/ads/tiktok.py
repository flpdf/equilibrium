"""Adaptador TikTok (Spark Ads) para a Marketing API v1.3, só com urllib.

O post precisa de um código de autorização Spark Ads (`auth_code`) gerado pelo Felipe no
app; ele vem em `extra.auth_code` da decisão (copiado de `auth_code` em metricas.json).
Fluxo: /tt_video/authorize/ -> campanha -> grupo de anúncios -> anúncio.
Variáveis: TIKTOK_ACCESS_TOKEN, TIKTOK_ADVERTISER_ID.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from ads.comum import AdsError, chamar, mostrar, variaveis

BASE = "https://business-api.tiktok.com/open_api/v1.3"
VARS = ["TIKTOK_ACCESS_TOKEN", "TIKTOK_ADVERTISER_ID"]
LOCATION_ID_BRASIL = "3469034"

# objetivo da plataforma (config) -> (objective_type, optimization_goal, billing_event)
OBJETIVOS = {
    "visualizacoes": ("VIDEO_VIEWS", "ENGAGED_VIEW", "CPV"),
    "alcance": ("REACH", "REACH", "CPM"),
}


def _nome(d: dict[str, Any]) -> str:
    return f"eq-{d['canal']}-{d['post_id']}"


def _hora(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def payload_autorizacao(d: dict[str, Any], adv: str) -> dict[str, Any]:
    return {"advertiser_id": adv, "auth_code": d.get("extra", {}).get("auth_code") or "<auth_code do vídeo>"}


def payload_campanha(d: dict[str, Any], adv: str, objetivo: str) -> dict[str, Any]:
    obj, _, _ = OBJETIVOS[objetivo]
    return {
        "advertiser_id": adv, "campaign_name": _nome(d), "objective_type": obj,
        "budget_mode": "BUDGET_MODE_INFINITE", "operation_status": "DISABLE",
    }


def payload_grupo(d: dict[str, Any], adv: str, objetivo: str, campanha_id: str, agora: datetime) -> dict[str, Any]:
    _, meta, cobranca = OBJETIVOS[objetivo]
    dias = d["duracao_dias"]
    return {
        "advertiser_id": adv, "campaign_id": campanha_id, "adgroup_name": _nome(d),
        "placement_type": "PLACEMENT_TYPE_NORMAL", "placements": ["PLACEMENT_TIKTOK"],
        "location_ids": [LOCATION_ID_BRASIL],
        "budget_mode": "BUDGET_MODE_DAY", "budget": round(d["orcamento"] / dias, 2),
        "schedule_type": "SCHEDULE_START_END",
        "schedule_start_time": _hora(agora), "schedule_end_time": _hora(agora + timedelta(days=dias)),
        "optimization_goal": meta, "billing_event": cobranca,
        "bid_type": "BID_TYPE_NO_BID", "pacing": "PACING_MODE_SMOOTH",
        "operation_status": "DISABLE",
    }


def payload_anuncio(d: dict[str, Any], adv: str, grupo_id: str, item_id: str) -> dict[str, Any]:
    return {
        "advertiser_id": adv, "adgroup_id": grupo_id,
        "creatives": [{
            "ad_name": _nome(d), "ad_format": "SINGLE_VIDEO",
            "identity_type": "AUTH_CODE", "tiktok_item_id": item_id,
        }],
        "operation_status": "DISABLE",
    }


def _post(caminho: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
    resp = chamar(f"{BASE}/{caminho}", json.dumps(payload).encode(),
                  {"Content-Type": "application/json", "Access-Token": token})
    if resp.get("code") not in (0, "0"):  # a API do TikTok responde 200 com code != 0 em erro
        raise AdsError(f"TikTok/{caminho}: {resp.get('message', resp)} (code {resp.get('code')})")
    return resp.get("data") or {}


def criar(d: dict[str, Any], objetivo: str, agora: datetime, confirmar: bool) -> dict[str, Any]:
    env = variaveis(VARS, exigir=confirmar)
    adv, token = env["TIKTOK_ADVERTISER_ID"], env["TIKTOK_ACCESS_TOKEN"]
    if objetivo not in OBJETIVOS:
        raise AdsError(f"TikTok: objetivo '{objetivo}' não suportado ({', '.join(OBJETIVOS)})")
    if confirmar and not d.get("extra", {}).get("auth_code"):
        raise AdsError(f"Post {d['post_id']}: sem auth_code Spark Ads; gere no app do TikTok e ponha em metricas.json")
    ids: dict[str, str] = {}

    def passo(etapa: str, caminho: str, payload: dict[str, Any], chave: str) -> None:
        if not confirmar:
            mostrar(f"TikTok {etapa}", f"/open_api/v1.3/{caminho}", payload)
            return
        data = _post(caminho, payload, token)
        if chave not in data:
            raise AdsError(f"TikTok/{etapa}: resposta sem {chave}: {json.dumps(data)[:200]}")
        ids[etapa] = str(data[chave])

    passo("autorizacao", "tt_video/authorize/", payload_autorizacao(d, adv), "item_id")
    passo("campanha", "campaign/create/", payload_campanha(d, adv, objetivo), "campaign_id")
    passo("grupo", "adgroup/create/",
          payload_grupo(d, adv, objetivo, ids.get("campanha", "<campaign_id>"), agora), "adgroup_id")
    passo("anuncio", "ad/create/",
          payload_anuncio(d, adv, ids.get("grupo", "<adgroup_id>"), ids.get("autorizacao", "<item_id>")), "ad_ids")
    return {
        "post_id": d["post_id"], "plataforma": "tiktok", "canal": d["canal"],
        "orcamento": d["orcamento"], "duracao_dias": d["duracao_dias"],
        "criado_em": agora.isoformat(), "dry_run": not confirmar, "ids": ids,
    }
