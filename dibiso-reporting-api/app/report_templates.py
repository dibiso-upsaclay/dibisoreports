"""
Admin-managed report templates: named BiSO layouts (ordered sections, each with an ordered list of graphics)
that users pick from when generating a report.
"""
import json
import re
import sqlite3
import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .users import DATABASE_PATH

# Graphics that can be placed in BiSO sections. Keys are the figure names produced by dibisoreporting
# (see Biso.available_figures()). "inputs" lists the report form fields the graphic needs.
BISO_GRAPHICS: List[Dict] = [
    {"id": "works_type",                    "label": "Typologie de la production scientifique"},
    {"id": "journals_hal",                  "label": "Liste des revues (HAL)"},
    {"id": "conferences",                   "label": "Liste des conférences"},
    {"id": "books",                         "label": "Liste des ouvrages"},
    {"id": "chapters",                      "label": "Liste des chapitres"},
    {"id": "open_access_works",             "label": "Articles en accès ouvert"},
    {"id": "journals",                      "label": "Revues et voies d'accès (BSO)"},
    {"id": "collaboration_map_world",       "label": "Carte des collaborations internationales"},
    {"id": "collaboration_map_europe",      "label": "Carte des collaborations européennes"},
    {"id": "collaboration_names",           "label": "Collaborations par établissements"},
    {"id": "private_sector_collaborations", "label": "Collaborations secteur privé"},
    {"id": "european_projects",             "label": "Projets européens"},
    {"id": "anr_projects",                  "label": "Projets ANR"},
    {"id": "data",                          "label": "Jeux de données partagés (Datacite)", "inputs": ["ror_id"]},
    {"id": "related_datasets",              "label": "Jeux de données associés aux publications HAL"},
]
_GRAPHICS_BY_ID = {g["id"]: g for g in BISO_GRAPHICS}

DEFAULT_TEMPLATE_NAME = "BiSO"


class TemplateSection(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1)
    graphics: List[str] = []


class TemplateWrite(BaseModel):
    name: str = Field(..., min_length=1)
    enabled: bool = True
    sections: List[TemplateSection]


def validate_sections(sections: List[TemplateSection]) -> List[Dict]:
    """
    Check a template layout and return it as plain dicts. Sections without an id get a new unique one.
    Raises ValueError on invalid layouts.
    """
    if not sections:
        raise ValueError("A template must have at least one section")
    seen_sections, seen_graphics, result = set(), set(), []
    for section in sections:
        title = section.title.strip()
        if not title:
            raise ValueError("Section titles cannot be empty")
        section_id = section.id or f"sec_{uuid.uuid4().hex[:8]}"
        if not re.fullmatch(r"[A-Za-z0-9_]+", section_id) or section_id in seen_sections:
            raise ValueError(f"Invalid or duplicate section id: {section_id}")
        seen_sections.add(section_id)
        for graphic in section.graphics:
            if graphic not in _GRAPHICS_BY_ID:
                raise ValueError(f"Unknown graphic: {graphic}")
            if graphic in seen_graphics:
                raise ValueError(f"Graphic used in several sections: {graphic}")
            seen_graphics.add(graphic)
        result.append({"id": section_id, "title": title, "graphics": list(section.graphics)})
    return result


def required_inputs(sections: List[Dict]) -> List[str]:
    """Return the report form inputs needed by the graphics of a layout."""
    inputs = []
    for section in sections:
        for graphic in section["graphics"]:
            for field in _GRAPHICS_BY_ID.get(graphic, {}).get("inputs", []):
                if field not in inputs:
                    inputs.append(field)
    return inputs


def _row_to_template(row: sqlite3.Row) -> Dict:
    sections = json.loads(row["sections"])
    return {
        "id": row["id"],
        "name": row["name"],
        "report_type": row["report_type"],
        "enabled": bool(row["enabled"]),
        "position": row["position"],
        "sections": sections,
        "required_inputs": required_inputs(sections),
    }


def init_templates_table():
    """Create the templates table and seed it with the default BiSO layout if it is empty."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            report_type TEXT NOT NULL DEFAULT 'biso',
            enabled BOOLEAN DEFAULT TRUE,
            position INTEGER DEFAULT 0,
            sections TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM report_templates")
    if cursor.fetchone()[0] == 0:
        from dibisoreporting import Biso
        cursor.execute(
            "INSERT INTO report_templates (name, report_type, enabled, position, sections) VALUES (?, 'biso', TRUE, 0, ?)",
            (DEFAULT_TEMPLATE_NAME, json.dumps(Biso.default_sections, ensure_ascii=False))
        )
    conn.commit()
    conn.close()


def get_templates(enabled_only: bool = False) -> List[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM report_templates"
    if enabled_only:
        query += " WHERE enabled = 1"
    cursor.execute(query + " ORDER BY position, id")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_template(row) for row in rows]


def get_template(template_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM report_templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_template(row) if row else None


def create_template(name: str, enabled: bool, sections: List[Dict]) -> Dict:
    """Create a template (raises sqlite3.IntegrityError if the name is taken)."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM report_templates")
        position = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO report_templates (name, report_type, enabled, position, sections) VALUES (?, 'biso', ?, ?, ?)",
            (name, enabled, position, json.dumps(sections, ensure_ascii=False))
        )
        template_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return get_template(template_id)


def update_template(template_id: int, name: str, enabled: bool, sections: List[Dict]) -> Optional[Dict]:
    """Update a template (raises sqlite3.IntegrityError if the name is taken)."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE report_templates SET name = ?, enabled = ?, sections = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (name, enabled, json.dumps(sections, ensure_ascii=False), template_id)
        )
        updated = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return get_template(template_id) if updated else None


def delete_template(template_id: int) -> bool:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM report_templates WHERE id = ?", (template_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return bool(deleted)
