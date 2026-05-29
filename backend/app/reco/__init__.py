"""Recommendation slice — explainable, human-in-the-loop career suggestions.

Implements spec.md §3.7 (FR-60..63), §8 CP-5 (human-in-the-loop) & CP-6
(rationale always present), ADR-012 (AI governance). The engine
(``app.reco.engine``) is a pure, deterministic, bias-clean function; the
service persists proposals that are never effective until a human confirms.
"""
