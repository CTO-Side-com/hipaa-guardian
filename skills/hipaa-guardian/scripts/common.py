"""Local, offline helpers for HIPAA Guardian. No network I/O."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONTROLS_PATH = BASE / 'references' / 'controls.json'
VALID_STATUSES = {'verified', 'partially_verified', 'failed', 'not_applicable', 'insufficient_evidence'}
VALID_SEVERITIES = {'critical', 'high', 'medium', 'low'}
VALID_EVIDENCE_TYPES = {'code', 'test', 'configuration', 'operational', 'contract', 'policy', 'external_report'}


def today():
    return datetime.now(timezone.utc).date().isoformat()


def load_json(path):
    with Path(path).open('r', encoding='utf-8') as f:
        return json.load(f)


def load_controls():
    doc = load_json(CONTROLS_PATH)
    ids = [x['id'] for x in doc['controls']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate control identifiers in control library')
    return doc


def write_json(path, document, overwrite=True):
    path = Path(path).expanduser()
    if path.is_symlink():
        raise ValueError(f'Refusing to write to symlink: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = 'w' if overwrite else 'x'
    with path.open(mode, encoding='utf-8') as f:
        json.dump(document, f, indent=2, ensure_ascii=True)
        f.write('\n')


def redact(value, limit=800):
    """Basic scrubbing for every output format, NOT a substitute for reviewer checking for PHI."""
    import re
    # Scrub before cutting, so an identifier straddling the limit cannot leak a prefix; lone surrogates
    # from JSON escapes would otherwise crash UTF-8 and PDF writers downstream.
    text = str(value or '').encode('utf-8', 'replace').decode('utf-8')
    text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_IDENTIFIER]', text)
    def hide_long_number(match):
        candidate = match.group(0)
        digits = re.sub(r'\D', '', candidate)
        return '[REDACTED_NUMBER]' if len(digits) >= 10 else candidate
    text = re.sub(r'(?<!\w)\+?\d[\d .()-]{8,}\d\b', hide_long_number, text)
    return text.replace('\n', ' ').replace('\r', ' ')[:limit]


def output_path(directory, name):
    path = Path(directory) / name
    if path.is_symlink():
        raise ValueError(f'Refusing to write to symlink: {path}')
    return path


def safe_text(value, limit=800):
    """Redacted text escaped for Markdown tables."""
    return redact(value, limit).replace('|', '\\|')


# Spreadsheet and tracker importers evaluate cells starting with these (OWASP CSV injection).
FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def csv_safe(value, limit=300):
    clean = redact(value, limit)
    return "'" + clean if clean.startswith(FORMULA_PREFIXES) else clean
