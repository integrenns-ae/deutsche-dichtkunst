#!/usr/bin/env python3
"""Build the skills-only OpenAI ZIP from an explicit file list (stdlib only)."""
import json
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    required = [
        '.codex-plugin/plugin.json', 'assets/icon.png', 'README.md',
        'LICENSE', 'PRIVACY.md',
    ]
    files = [root / name for name in required]
    for folder in ('skills', 'examples', 'docs', 'evals', 'scripts'):
        files.extend(p for p in (root / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix not in ('.pyc', '.pyo') and p.name != '.DS_Store')
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing file or symbolic link: {path}')
        path.resolve().relative_to(root)
    output = root.parent / 'output' / f"{manifest['name']}-{manifest['version']}-openai.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            entry = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2026, 10, 22, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    print(output)


if __name__ == '__main__':
    main()
