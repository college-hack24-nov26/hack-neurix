"""
HomeCare+ — database-driven symptom matching.

Replaces the hard-coded 57-disease list as the offline analyzer: it scores all
~347 diseases in PostgreSQL using the `disease_symptoms` table.

Scoring (per disease)
    coverage  = weight of the disease's symptoms the user matched / total weight of its symptoms
    precision = how many of the user's symptoms the disease explains / symptoms entered
    score     = 0.6 * coverage + 0.4 * precision          (same blend as the old analyzer)
Symptom weights are IDF values (see seeding.recompute_symptom_weights), so a rare,
specific symptom such as "Koplik spots" counts far more than "fever".

Input is matched to the symptom catalogue by (1) exact slug, (2) substring either
way ("severe chest pain" <-> "chest pain"), (3) pg_trgm similarity for typos.
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Disease

logger = logging.getLogger(__name__)

Q_EXACT, Q_CONTAINS, Q_FUZZY = 1.0, 0.7, 0.6
MAX_PARTIAL_PER_INPUT = 50


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


async def resolve_input_symptoms(db: AsyncSession, inputs: List[str]) -> List[Dict[int, float]]:
    """For each user-entered symptom return {symptom_id: match_quality}."""
    resolved: List[Dict[int, float]] = []
    for raw in inputs:
        norm, slug = _norm(raw), _slug(raw)
        found: Dict[int, float] = {}
        if not norm:
            resolved.append(found)
            continue

        rows = (await db.execute(
            text("""
                SELECT id, slug, lower(name) AS lname
                  FROM symptoms
                 WHERE slug = :slug
                    OR lower(name) LIKE :like ESCAPE '\\'
                    OR :norm LIKE '%' || lower(name) || '%'
            """),
            {"slug": slug, "like": f"%{_escape_like(norm)}%", "norm": norm},
        )).all()

        partial = []
        for sid, sslug, lname in rows:
            if sslug == slug:
                found[sid] = Q_EXACT
            else:
                partial.append((abs(len(lname) - len(norm)), sid))
        partial.sort()
        for _, sid in partial[:MAX_PARTIAL_PER_INPUT]:
            found.setdefault(sid, Q_CONTAINS)

        if not found:      # typo tolerance, e.g. "headche"
            fuzzy = (await db.execute(
                text("""
                    SELECT id, similarity(name, :norm) AS sim
                      FROM symptoms
                     WHERE name % :norm
                  ORDER BY sim DESC LIMIT 3
                """),
                {"norm": norm},
            )).all()
            for sid, sim in fuzzy:
                if sim >= 0.45:
                    found[sid] = Q_FUZZY

        resolved.append(found)
    return resolved


def _followup_adjust(prob: float, follow_up: Dict[str, Any]) -> float:
    severity_str = str(follow_up.get("severity", ""))
    if "Severe" in severity_str or "Critical" in severity_str:
        prob = min(100, prob * 1.2)
    elif "Mild" in severity_str:
        prob = max(5, prob * 0.8)
    if "More than a week" in str(follow_up.get("duration", "")):
        prob = min(100, prob * 1.15)
    return prob


async def predict_from_db(
    db: AsyncSession,
    symptoms: List[str],
    follow_up: Optional[Dict[str, Any]] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    follow_up = follow_up or {}
    inputs = [s for s in symptoms if s and s.strip()]
    if not inputs:
        return []

    per_input = await resolve_input_symptoms(db, inputs)
    matched_ids = sorted({sid for m in per_input for sid in m})
    if not matched_ids:
        return []

    # every symptom of every disease that has at least one matched symptom
    rows = (await db.execute(
        text("""
            SELECT ds.disease_id, ds.symptom_id, ds.weight
              FROM disease_symptoms ds
             WHERE ds.disease_id IN (
                   SELECT disease_id FROM disease_symptoms WHERE symptom_id = ANY(:ids))
        """).bindparams(bindparam("ids", value=matched_ids)),
    )).all()

    by_disease: Dict[int, List[tuple]] = defaultdict(list)
    for did, sid, weight in rows:
        by_disease[did].append((sid, weight))

    n_inputs = len(inputs)
    scored = []
    for did, syms in by_disease.items():
        total_w = sum(w for _, w in syms) or 1.0
        matched_w = 0.0
        for sid, w in syms:
            best = max((m.get(sid, 0.0) for m in per_input), default=0.0)
            matched_w += w * best
        credits = []
        sym_ids = {sid for sid, _ in syms}
        for m in per_input:
            credits.append(max((q for sid, q in m.items() if sid in sym_ids), default=0.0))
        precision = sum(credits) / n_inputs
        coverage = matched_w / total_w
        prob = _followup_adjust((coverage * 0.6 + precision * 0.4) * 100, follow_up)
        hits = sum(1 for c in credits if c > 0)
        if hits == 0:
            continue
        scored.append((did, round(min(prob, 100)), hits, coverage))

    # best probability first; ties -> more inputs explained -> broader coverage
    scored.sort(key=lambda t: (-t[1], -t[2], -t[3]))
    top = scored[:limit]
    if not top:
        return []

    diseases = {
        d.id: d for d in (await db.execute(select(Disease).where(Disease.id.in_([t[0] for t in top])))).scalars()
    }

    results = []
    for did, prob, hits, _ in top:
        d = diseases[did]
        specialist = d.specialist or "General Physician"
        precautions = list(d.precautions or []) or [
            f"Consult a {specialist} for a proper diagnosis",
            "Seek urgent medical care if symptoms worsen suddenly",
        ]
        results.append({
            "disease_id":       d.id,
            "slug":             d.slug,
            "name":             d.name,
            "icd_code":         d.icd_code or "",
            "probability":      prob,
            "severity":         d.severity_score or 50,
            "severity_level":   d.severity or "Moderate",
            "specialist":       specialist,
            "precautions":      precautions,
            "home_remedies":    list(d.home_remedies or []),
            "medications":      list(d.medications or []),
            "matched_symptoms": hits,
            "recommendations":  precautions,
            "description":      d.overview or f"{d.name} — consult a {specialist} for accurate diagnosis.",
        })
    return results
