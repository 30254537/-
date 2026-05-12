"""Command-line interface for MixMind DJ."""
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel

from mixmind import __version__
from mixmind import database as db
from mixmind.scanner import iter_audio_files, extract_tags
from mixmind.analyzer import analyze_file
from mixmind.classifier import classify_track
from mixmind.dedupe import find_duplicates
from mixmind.preferences import train_preference_model, recommend as ai_recommend, find_similar
from mixmind.playlist import generate_setlist, export_m3u8
from mixmind.exporter import export_rekordbox_xml, export_serato_crate

console = Console()


def _banner():
    console.print(Panel.fit(
        "[bold magenta]MixMind DJ[/bold magenta] [dim]v{}[/dim]\n"
        "[cyan]AI music management for DJs[/cyan]".format(__version__),
        border_style="magenta",
    ))


@click.group()
@click.version_option(__version__)
def cli():
    """MixMind DJ — AI-powered music library management."""
    db.init_db()


@cli.command()
@click.argument("folder", type=click.Path(exists=True))
@click.option("--analyze/--no-analyze", default=True, help="Analyze audio after scan.")
@click.option("--skip-existing", is_flag=True, default=True, help="Skip already-analyzed tracks.")
def scan(folder, analyze, skip_existing):
    """Scan a folder and add audio files to the library."""
    _banner()
    folder = str(Path(folder).resolve())
    console.print(f"[cyan]Scanning:[/cyan] {folder}")

    files = list(iter_audio_files(folder))
    console.print(f"[green]Found[/green] [bold]{len(files)}[/bold] audio files")

    if not files:
        return

    added = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning metadata...", total=len(files))
        for fp in files:
            try:
                tags = extract_tags(fp)
                db.upsert_track(tags)
                added += 1
            except Exception as e:
                console.print(f"[red]!! {fp}: {e}[/red]")
            progress.update(task, advance=1)

    console.print(f"[green]Added / updated {added} tracks.[/green]")

    if analyze:
        console.print("\n[cyan]Starting audio analysis...[/cyan]")
        _do_analysis(skip_existing=skip_existing)


def _do_analysis(skip_existing: bool = True):
    """Run audio analysis on pending tracks."""
    if skip_existing:
        pending = [t for t in db.find_tracks(limit=100000) if not t.get("bpm")]
    else:
        pending = db.find_tracks(limit=100000)

    if not pending:
        console.print("[yellow]No tracks to analyze.[/yellow]")
        return

    console.print(f"[cyan]Analyzing[/cyan] [bold]{len(pending)}[/bold] tracks...")

    ok = 0
    failed = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing audio...", total=len(pending))
        for track in pending:
            try:
                result = analyze_file(track["path"])
                if "error" in result:
                    failed += 1
                    progress.update(task, advance=1, description=f"[red]{result['error'][:40]}[/red]")
                    continue

                # Classify genre from features
                merged = {**track, **result}
                result["genre_ai"] = classify_track(merged)

                db.update_track(track["id"], result)
                ok += 1
            except Exception as e:
                failed += 1
                console.print(f"[red]!! {track['filename']}: {e}[/red]")
            progress.update(task, advance=1)

    console.print(f"[green]Analyzed {ok}[/green]  [red]Failed {failed}[/red]")


@cli.command()
@click.option("--skip-existing/--force", default=True, help="Re-analyze all tracks if --force.")
def analyze(skip_existing):
    """Run audio analysis on tracks in the library."""
    _banner()
    _do_analysis(skip_existing=skip_existing)


@cli.command()
def stats():
    """Show library statistics."""
    _banner()
    s = db.get_stats()
    console.print(f"\n[bold]Total tracks:[/bold] {s['total_tracks']}")
    console.print(f"[bold]Analyzed:[/bold] {s['analyzed']}")
    console.print(f"[bold]Total duration:[/bold] {s['total_hours']} hours")
    console.print(f"[bold green]Liked:[/bold green] {s['liked']}    "
                  f"[bold red]Disliked:[/bold red] {s['disliked']}")
    console.print(f"[bold]Duplicate tracks:[/bold] {s['duplicates']}")

    if s["genres"]:
        t = Table(title="Top Genres", header_style="magenta")
        t.add_column("Genre")
        t.add_column("Count", justify="right")
        for row in s["genres"][:15]:
            t.add_row(row["genre_ai"], str(row["c"]))
        console.print(t)

    if s["moods"]:
        t = Table(title="Mood Distribution", header_style="magenta")
        t.add_column("Mood")
        t.add_column("Count", justify="right")
        for row in s["moods"]:
            t.add_row(row["mood_label"], str(row["c"]))
        console.print(t)


@cli.command()
@click.option("--genre", help="Filter by genre.")
@click.option("--mood", help="Filter by mood (chill/warmup/groove/peak/intense).")
@click.option("--bpm-min", type=float)
@click.option("--bpm-max", type=float)
@click.option("--camelot", help="Filter by Camelot key, e.g. 8A.")
@click.option("--query", "-q", help="Search by artist/title.")
@click.option("--limit", default=30, type=int)
def list(genre, mood, bpm_min, bpm_max, camelot, query, limit):
    """List tracks in the library."""
    tracks = db.find_tracks(
        query=query, genre=genre, mood=mood,
        bpm_min=bpm_min, bpm_max=bpm_max, camelot=camelot, limit=limit,
    )
    if not tracks:
        console.print("[yellow]No tracks match.[/yellow]")
        return
    t = Table(header_style="magenta")
    t.add_column("ID", style="dim")
    t.add_column("Artist")
    t.add_column("Title")
    t.add_column("BPM", justify="right")
    t.add_column("Key")
    t.add_column("Energy", justify="right")
    t.add_column("Genre")
    t.add_column("Mood")
    t.add_column("★", justify="center")
    for tr in tracks:
        rating_display = {-1: "[red]✗[/red]", 0: "", 1: "[green]♥[/green]", 2: "[bold green]♥♥[/bold green]"}.get(tr.get("rating") or 0, "")
        t.add_row(
            str(tr["id"]),
            (tr.get("artist") or "")[:25],
            (tr.get("title") or "")[:35],
            f"{tr.get('bpm') or '-'}",
            tr.get("camelot") or "-",
            f"{tr.get('energy') or '-'}",
            tr.get("genre_ai") or "-",
            tr.get("mood_label") or "-",
            rating_display,
        )
    console.print(t)


def _resolve_track(search: str):
    """Resolve a search string to a track record."""
    if search.isdigit():
        return db.get_track(int(search))
    tracks = db.find_tracks(query=search, limit=5)
    if len(tracks) == 1:
        return tracks[0]
    if len(tracks) == 0:
        return None
    # Disambiguate
    console.print("[yellow]Multiple matches, showing first:[/yellow]")
    for t in tracks:
        console.print(f"  [{t['id']}] {t.get('artist')} - {t.get('title')}")
    return tracks[0]


@cli.command()
@click.argument("search")
@click.option("--love", is_flag=True, help="Rate as LOVE (2) instead of like (1).")
def like(search, love):
    """Mark a track as liked (learn your taste)."""
    track = _resolve_track(search)
    if not track:
        console.print(f"[red]Track not found: {search}[/red]")
        sys.exit(1)
    db.set_rating(track["id"], 2 if love else 1)
    symbol = "♥♥" if love else "♥"
    console.print(f"[green]{symbol}[/green] {track.get('artist')} - {track.get('title')}")


@cli.command()
@click.argument("search")
def dislike(search):
    """Mark a track as disliked (AI will avoid similar ones)."""
    track = _resolve_track(search)
    if not track:
        console.print(f"[red]Track not found: {search}[/red]")
        sys.exit(1)
    db.set_rating(track["id"], -1)
    console.print(f"[red]✗[/red] {track.get('artist')} - {track.get('title')}")


@cli.command()
def train():
    """Train the AI preference model on your likes/dislikes."""
    _banner()
    result = train_preference_model()
    if not result["trained"]:
        console.print(f"[yellow]{result['reason']}[/yellow]")
        return
    console.print(f"[green]Model trained:[/green] mode={result.get('mode')}  "
                  f"liked={result['liked']}  disliked={result['disliked']}")
    if "score" in result:
        console.print(f"[dim]Training accuracy: {result['score']:.3f}[/dim]")


@cli.command("recommend")
@click.option("--limit", default=20, type=int)
def recommend_cmd(limit):
    """Recommend tracks based on your taste."""
    _banner()
    results = ai_recommend(limit=limit)
    if not results:
        console.print("[yellow]No recommendations — like some tracks first.[/yellow]")
        return
    t = Table(title="Recommended for you", header_style="magenta")
    t.add_column("ID", style="dim")
    t.add_column("Artist")
    t.add_column("Title")
    t.add_column("BPM", justify="right")
    t.add_column("Key")
    t.add_column("Energy", justify="right")
    t.add_column("Genre")
    t.add_column("Score", justify="right")
    for tr in results:
        t.add_row(
            str(tr["id"]),
            (tr.get("artist") or "")[:25],
            (tr.get("title") or "")[:35],
            f"{tr.get('bpm') or '-'}",
            tr.get("camelot") or "-",
            f"{tr.get('energy') or '-'}",
            tr.get("genre_ai") or "-",
            f"{tr.get('similarity_score', 0):.3f}",
        )
    console.print(t)


# Click reserves `recommend` as attr name but our module defines same — alias
cli.commands["recommend"] = cli.commands.pop("recommend-cmd")


@cli.command()
@click.argument("search")
@click.option("--limit", default=20, type=int)
def similar(search, limit):
    """Find tracks similar to a given one."""
    track = _resolve_track(search)
    if not track:
        console.print(f"[red]Track not found: {search}[/red]")
        sys.exit(1)

    results = find_similar(track["id"], limit=limit)
    console.print(f"\n[bold]Similar to:[/bold] {track.get('artist')} - {track.get('title')}\n")
    t = Table(header_style="magenta")
    t.add_column("Artist")
    t.add_column("Title")
    t.add_column("BPM", justify="right")
    t.add_column("Key")
    t.add_column("Genre")
    t.add_column("Sim", justify="right")
    for tr in results:
        t.add_row(
            (tr.get("artist") or "")[:25],
            (tr.get("title") or "")[:35],
            f"{tr.get('bpm') or '-'}",
            tr.get("camelot") or "-",
            tr.get("genre_ai") or "-",
            f"{tr.get('similarity_score', 0):.3f}",
        )
    console.print(t)


@cli.command()
def dedupe():
    """Find and group duplicate/version tracks."""
    _banner()
    n_groups, n_tracks = find_duplicates()
    console.print(f"[green]Found {n_groups} duplicate groups[/green] covering {n_tracks} tracks.")

    if n_groups == 0:
        return

    groups = db.find_duplicate_groups()
    for g in groups[:20]:
        console.print(f"\n[bold]Group #{g[0]['duplicate_group_id']}[/bold]")
        for t in g:
            mb = (t.get("filesize") or 0) / (1024 * 1024)
            console.print(
                f"  [{t['id']}] {t.get('artist')} - {t.get('title')}  "
                f"[dim]({mb:.1f} MB, {t.get('bpm') or '-'} BPM)[/dim]"
            )
    if len(groups) > 20:
        console.print(f"\n[dim]...and {len(groups) - 20} more groups[/dim]")


@cli.command()
@click.option("--duration", "-d", default=60, type=int, help="Target duration in minutes.")
@click.option("--style", "-s",
              type=click.Choice(["warmup", "peak-time", "after-hours", "festival", "journey"]),
              default="journey")
@click.option("--genre", help="Filter by genre.")
@click.option("--bpm-min", type=float)
@click.option("--bpm-max", type=float)
@click.option("--out", "-o", help="Export to .m3u8 file.")
@click.option("--name", help="Save to library as named playlist.")
def playlist(duration, style, genre, bpm_min, bpm_max, out, name):
    """Generate an AI-curated setlist."""
    _banner()
    bpm_range = (bpm_min, bpm_max) if (bpm_min or bpm_max) else None
    setlist = generate_setlist(
        duration_minutes=duration,
        curve=style,
        genre=genre,
        bpm_range=bpm_range,
    )
    if not setlist:
        console.print("[yellow]No tracks available for this setlist.[/yellow]")
        return

    total_sec = sum(t.get("duration") or 300 for t in setlist)
    t = Table(title=f"Setlist — {style} — ~{total_sec // 60} min", header_style="magenta")
    t.add_column("#", justify="right", style="dim")
    t.add_column("Artist")
    t.add_column("Title")
    t.add_column("BPM", justify="right")
    t.add_column("Key")
    t.add_column("Energy", justify="right")
    for i, tr in enumerate(setlist, 1):
        t.add_row(
            str(i),
            (tr.get("artist") or "")[:25],
            (tr.get("title") or "")[:35],
            f"{tr.get('bpm') or '-'}",
            tr.get("camelot") or "-",
            f"{tr.get('energy') or '-'}",
        )
    console.print(t)

    if out:
        export_m3u8(setlist, out)
        console.print(f"[green]Exported to:[/green] {out}")

    if name:
        pid = db.save_playlist(name, [tr["id"] for tr in setlist])
        console.print(f"[green]Saved as playlist:[/green] {name} (id={pid})")


@cli.command()
@click.argument("search")
def info(search):
    """Show full info for a single track."""
    track = _resolve_track(search)
    if not track:
        console.print(f"[red]Not found: {search}[/red]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold magenta]{track.get('artist') or '?'}[/bold magenta] - "
        f"[bold]{track.get('title') or '?'}[/bold]",
        border_style="magenta",
    ))
    rows = [
        ("Path", track["path"]),
        ("Duration", f"{(track.get('duration') or 0):.1f} sec"),
        ("BPM", f"{track.get('bpm')}  [conf {track.get('bpm_confidence')}]"),
        ("Key", f"{track.get('key_name')}  ({track.get('camelot')})  [conf {track.get('key_confidence')}]"),
        ("Energy", f"{track.get('energy')}/10"),
        ("Loudness", f"{track.get('loudness')} LUFS  (true peak {track.get('true_peak')} dBFS)"),
        ("Brightness", f"{track.get('brightness')}"),
        ("Danceability", f"{track.get('danceability')}"),
        ("Genre (AI)", track.get("genre_ai") or "-"),
        ("Genre (tag)", track.get("genre_tag") or "-"),
        ("Mood", track.get("mood_label") or "-"),
        ("Rating", str(track.get("rating") or 0)),
        ("Intro ends", f"{track.get('intro_end')} sec"),
        ("First drop", f"{track.get('first_drop')} sec"),
        ("Breakdown", f"{track.get('breakdown')} sec"),
        ("Outro start", f"{track.get('outro_start')} sec"),
    ]
    for k, v in rows:
        console.print(f"[bold cyan]{k:15}[/bold cyan] {v}")


@cli.command()
@click.option("--out", "-o", default="mixmind_export.xml", help="Output XML path.")
@click.option("--liked-only", is_flag=True, help="Only export liked tracks.")
@click.option("--with-playlists", is_flag=True, default=True, help="Include saved playlists.")
def export_rekordbox(out, liked_only, with_playlists):
    """Export library + playlists to Rekordbox XML format."""
    _banner()
    tracks = db.find_tracks(rating=1 if liked_only else None, limit=100000)
    if not tracks:
        console.print("[yellow]No tracks to export.[/yellow]")
        return
    playlists = None
    if with_playlists:
        playlists = {}
        for pl in db.get_playlists():
            pl_tracks = db.get_playlist_tracks(pl["id"])
            playlists[pl["name"]] = [t["id"] for t in pl_tracks]
    path = export_rekordbox_xml(tracks, out, playlists=playlists)
    console.print(f"[green]Exported[/green] {len(tracks)} tracks to [cyan]{path}[/cyan]")
    console.print("[dim]Import in rekordbox: Preferences > Advanced > rekordbox xml[/dim]")


if __name__ == "__main__":
    cli()
