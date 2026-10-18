"""Interactive local publishing backend. Run: python publisher.py"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
MAX_PDF_BYTES = 100 * 1024 * 1024


class PublishError(Exception):
    """An actionable error that can be shown without a traceback."""


def run(args, root=ROOT, capture=True):
    result = subprocess.run(args, cwd=root, text=True, encoding='utf-8', errors='replace',
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None)
    if result.returncode:
        detail = (result.stderr or result.stdout or '').strip()
        raise PublishError(f'{args[0]} failed. {detail}')
    return (result.stdout or '').strip()


def git(*args, root=ROOT):
    return run(['git', *args], root)


def slug(text):
    plain = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    result = re.sub(r'[^a-z0-9]+', '-', plain.lower()).strip('-')[:90].rstrip('-')
    if not result or result.upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))}:
        raise PublishError('Use a title containing letters or numbers that can form a valid filename.')
    return result


def safe_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise PublishError('A destination points outside the project.')
    return path


def validate_pdf(source):
    if not source.is_file() or source.suffix.lower() != '.pdf':
        raise PublishError('Choose an existing PDF file. Export Word documents to PDF first.')
    if source.stat().st_size >= MAX_PDF_BYTES:
        raise PublishError('The PDF must be smaller than 100 MB for GitHub.')
    with source.open('rb') as stream:
        if not stream.read(1024).lstrip().startswith(b'%PDF-'):
            raise PublishError('This file does not have a PDF header.')


def validate_year(value):
    if value and not re.fullmatch(r'(19|20|21)\d{2}', value):
        raise PublishError('Enter a four-digit publication year between 1900 and 2199, or leave it blank if unknown.')
    return value


@dataclass
class Submission:
    source: Path
    title: str
    summary: str
    topic: str
    year: str
    page_path: str
    new_page_title: str = ''
    parent_path: str = ''


def update_catalogue(root, entry):
    """Only update catalogue/source files in the isolated preview copy."""
    validate_pdf(entry.source)
    validate_year(entry.year)
    if not entry.title.strip() or not entry.summary.strip():
        raise PublishError('A title and short summary are required.')
    if entry.topic not in {'Finance', 'Technology', 'Equity research'}:
        raise PublishError('Choose a supported research topic.')
    if entry.topic in {'Finance','Technology'}:
        if not entry.year:
            raise PublishError('Finance and technology papers need a year for the year-based archive.')
        section='Finance/Papers' if entry.topic=='Finance' else 'Tech'
        expected=f'Repository of Research/{section}/{entry.year}/{entry.year}.html'
        if entry.page_path!=expected:
            raise PublishError('The destination collection must match the paper’s publication year.')
    data = json.loads((root / 'content.json').read_text(encoding='utf-8'))
    identifier = slug(entry.title)
    if any(p['id'] == identifier or p['title'].casefold() == entry.title.casefold() for p in data['papers']):
        raise PublishError('A document with this title or identifier already exists. Nothing was overwritten.')
    page = next((p for p in data['pages'] if p['path'] == entry.page_path), None)
    if page is None:
        parent = next((p for p in data['pages'] if p['path'] == entry.parent_path), None)
        if not parent or not entry.new_page_title:
            raise PublishError('The new collection needs a title and an existing parent collection.')
        target = safe_path(root, entry.page_path)
        template = safe_path(root / 'templates', entry.page_path)
        if target.exists() or template.exists():
            raise PublishError('This collection address is already in use.')
        # Clone the original retro layout, adjusting its breadcrumb for any depth.
        original = (root / 'templates/Repository of Research/repo.html').read_text(encoding='utf-8')
        back = quote(os.path.relpath(root / entry.parent_path, target.parent).replace('\\', '/'), safe='/')
        original = re.sub(r'<a href="\.\./index.html" class="back-link">.*?</a>',
                          lambda _: f'<a href="{back}" class="back-link">&lt;-- Back to {escape(parent["title"])}</a>', original)
        original = original.replace('repository of research', escape(entry.new_page_title))
        original = re.sub(r'<div class="menu">.*?</div>', '<div class="menu"></div>', original, flags=re.S)
        template.parent.mkdir(parents=True, exist_ok=True)
        template.write_text(original, encoding='utf-8', newline='\n')
        page = {'path': entry.page_path, 'title': entry.new_page_title, 'links': [], 'documents': []}
        data['pages'].append(page)
        parent['links'].append([entry.page_path, entry.new_page_title])
    relative = (Path(page['path']).parent / identifier / f'{identifier}.pdf').as_posix()
    target = safe_path(root, relative)
    if target.exists() or any(p['path'].casefold() == relative.casefold() for p in data['papers']):
        raise PublishError('The destination filename is already in use. Nothing was overwritten.')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(entry.source, target)
    data['papers'].append({'id': identifier, 'path': relative, 'title': entry.title.strip(),
                           'topic': entry.topic, 'year': entry.year, 'summary': entry.summary.strip()})
    page['documents'].append(relative)
    (root / 'content.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return relative


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}


@contextmanager
def prepare(entry, root=ROOT):
    """Build and validate away from the live working tree; failed previews change nothing."""
    with TemporaryDirectory(prefix='portfolio-publisher-') as temporary:
        stage = Path(temporary) / 'site'
        shutil.copytree(root, stage, ignore=shutil.ignore_patterns('.git', 'tmp', '__pycache__', '.venv', 'venv', '.publisher.lock', 'debug.log'), symlinks=True)
        if any(p.is_symlink() for p in stage.rglob('*')):
            raise PublishError('The project contains symbolic links; use ordinary files for publishing.')
        before = inventory(stage)
        destination = update_catalogue(stage, entry)
        run([sys.executable, '-X', 'utf8', 'scripts/build.py'], stage)
        print(run([sys.executable, '-X', 'utf8', 'scripts/check.py'], stage))
        after = inventory(stage)
        changes = sorted(name for name in after if after[name] != before.get(name))
        yield stage, changes, before, destination


def apply_preview(stage, changes, before, root=ROOT):
    """Apply validated files, restoring prior bytes if a write fails."""
    for name in changes:
        if digest(safe_path(root, name)) != before.get(name):
            raise PublishError(f'{name} changed while the preview was built. Run the app again.')
    backup = {}
    try:
        for name in changes:
            target = safe_path(root, name)
            backup[name] = target.read_bytes() if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.publisher-tmp')
            try:
                shutil.copyfile(safe_path(stage, name), temporary)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
    except BaseException:
        for name, content in backup.items():
            target = safe_path(root, name)
            if content is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(content)
        raise


def publication_target(root=ROOT, refresh=True):
    if git('status', '--porcelain', root=root):
        raise PublishError('There are uncommitted changes. Commit or stash them before publishing, or choose Save locally. This prevents unrelated work from entering the upload commit.')
    branch = git('branch', '--show-current', root=root)
    if not branch:
        raise PublishError('Check out a branch before publishing.')
    remote = git('remote', 'get-url', '--push', 'origin', root=root)
    if refresh:
        print('Checking GitHub and the current branch…')
        git('fetch', 'origin', f'refs/heads/{branch}', root=root)
        if git('rev-parse', 'HEAD', root=root) != git('rev-parse', 'FETCH_HEAD', root=root):
            raise PublishError('The local and GitHub branches differ. Sync them first; the app will not merge, reset, or force-push your work.')
    return branch, remote


def commit_and_push(changes, title, branch, root=ROOT):
    # Only explicit files from the validated preview are staged.
    git('add', '--', *changes, root=root)
    git('commit', '--only', '-m', f'Add research: {title}', '--', *changes, root=root)
    commit = git('rev-parse', '--short', 'HEAD', root=root)
    try:
        git('push', 'origin', f'HEAD:refs/heads/{branch}', root=root)
    except PublishError as error:
        raise PublishError(f'Your files are saved and committed as {commit}, but the push failed. Fix the connection or authentication, then run: git push origin HEAD:refs/heads/{branch}\n{error}') from error
    return commit


def ask(label, default='', required=False):
    while True:
        value = input(label + (f' [{default}]' if default else '') + ': ').strip() or default
        if value or not required:
            return value
        print('Please enter a value.')


def choose(label, options):
    print('\n' + label)
    for index, option in enumerate(options, 1):
        print(f'  {index}. {option}')
    while True:
        answer = ask('Choose a number', required=True)
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print('Choose one of the listed numbers.')


def wizard(root=ROOT):
    data = json.loads((root / 'content.json').read_text(encoding='utf-8'))
    print('\nRESEARCH PUBLISHER\nAdd a PDF without editing HTML. Press Ctrl+C at any time to cancel.\n')
    while True:
        source = Path(ask('PDF file path (you can drag a file into this window)', required=True).strip('"').strip("'")).expanduser().resolve()
        try:
            validate_pdf(source)
            break
        except PublishError as error:
            print(error)
    title = ask('Paper/report title', source.stem.replace('_', ' '), required=True)
    summary = ask('Short summary (one or two sentences)', required=True)
    topic = ['Finance', 'Technology', 'Equity research'][choose('Research type', ['Finance paper', 'Technology paper', 'Equity research report'])]
    while True:
        try:
            answer = ask('Publication year (enter ? if unknown)', str(date.today().year))
            year = validate_year('' if answer == '?' else answer)
            break
        except PublishError as error:
            print(error)
    parent_path = new_title = ''
    if topic in {'Finance','Technology'}:
        if not year:
            raise PublishError('Finance and technology papers need a year for the year-based archive.')
        section='Finance/Papers' if topic=='Finance' else 'Tech'
        page_path = f'Repository of Research/{section}/{year}/{year}.html'
        if not any(p['path'] == page_path for p in data['pages']):
            new_title = f'{topic} papers · {year}'
            parent_path = 'Repository of Research/Finance/Papers/years.html' if topic=='Finance' else 'Repository of Research/Tech/tech.html'
    else:
        prefix = 'Repository of Research/Finance/Equity Research/'
        pages = [p for p in data['pages'] if p['path'].startswith(prefix)]
        index = choose('Destination collection', [p['title'] for p in pages] + ['Create a new collection…'])
        if index < len(pages):
            page_path = pages[index]['path']
        else:
            parent = pages[choose('Place the new collection under', [p['title'] for p in pages])]
            new_title = ask('New collection name', required=True)
            parent_path = parent['path']
            identifier = slug(new_title)
            page_path = (Path(parent_path).parent / identifier / f'{identifier}.html').as_posix()
    return Submission(source, title, summary, topic, year, page_path, new_title, parent_path)


@contextmanager
def lock(root=ROOT):
    target = root / '.publisher.lock'
    try:
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise PublishError('Another publishing session is running. If an earlier session crashed, remove .publisher.lock after confirming it has stopped.') from error
    try:
        os.write(descriptor, str(os.getpid()).encode())
        os.close(descriptor)
        yield
    finally:
        target.unlink(missing_ok=True)


def main():
    try:
        with lock():
            entry = wizard()
            with prepare(entry) as (stage, changes, before, destination):
                print(f'\nREADY TO SAVE\nTitle: {entry.title}\nTopic: {entry.topic}\nYear: {entry.year or "Unknown"}\nCollection: {entry.new_page_title or entry.page_path}\nPDF: {destination}\nSummary: {entry.summary}\n\nFiles to update ({len(changes)}):')
                for name in changes:
                    print('  ' + name)
                action = choose('Next step', ['Save locally', 'Save, commit, and push to GitHub', 'Cancel'])
                if action == 2:
                    print('Cancelled. No project files were changed.')
                    return 0
                if action == 1:
                    branch, remote = publication_target()
                    print(f'\nDestination: {remote}\nBranch: {branch}')
                    if ask('Publish this validated update? Type yes to continue').lower() != 'yes':
                        print('Cancelled. No project files were changed.')
                        return 0
                    # Recheck the working tree after the review, before writing.
                    latest_branch, latest_remote = publication_target(refresh=False)
                    if (latest_branch, latest_remote) != (branch, remote):
                        raise PublishError('The branch or remote changed during review. Run the app again.')
                apply_preview(stage, changes, before)
                if action == 1:
                    commit = commit_and_push(changes, entry.title, branch)
                    print(f'\nPublished commit {commit}. GitHub Pages will update according to your repository’s deployment settings.')
                else:
                    print('\nSaved locally. To preview: python -m http.server 8000\nOpen http://localhost:8000/research.html')
        return 0
    except (KeyboardInterrupt, EOFError):
        print('\nStopped. Any completed save or commit is retained.')
        return 130
    except (PublishError, OSError, ValueError) as error:
        print(f'\nCould not finish: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
