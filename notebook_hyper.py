import marimo

__generated_with = "0.19.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Nonogram Solver Benchmarker

    Benchmark different commits of the nonogram solver across puzzles.
    """)
    return


@app.cell(hide_code=True)
def _():
    import subprocess
    import sqlite3
    import json
    import re
    import sys
    from pathlib import Path
    from datetime import datetime
    import pandas as pd
    import plotly.express as px
    import matplotlib.pyplot as plt
    return Path, datetime, json, pd, plt, re, sqlite3, subprocess, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Extract Commits
    """)
    return


@app.cell(hide_code=True)
def _(mo, subprocess):
    GITHUB_URL = "https://github.com/schicho/nonogram-solver/"

    def get_remote_branches(url: str) -> list[str]:
        """Fetch branch names from a remote repository."""
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--heads", url],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                branches = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        # Format: <hash>\trefs/heads/<branch_name>
                        ref = line.split("\t")[1]
                        branch = ref.replace("refs/heads/", "")
                        branches.append(branch)
                return sorted(branches)
        except Exception:
            pass
        return ["main", "master"]  # Fallback defaults

    branches = get_remote_branches(GITHUB_URL)

    branch_dropdown = mo.ui.dropdown(
        options=branches,
        value="develop" if branches else "main",
        label="Branch"
    )
    overwrite_switch = mo.ui.switch(label="Overwrite existing commits", value=False)

    mo.hstack([branch_dropdown, overwrite_switch], gap=2, justify="start")
    return GITHUB_URL, branch_dropdown, overwrite_switch


@app.cell(hide_code=True)
def _(mo):
    extracted_commits_folder_input = mo.ui.text(
        value="./download_extracted_commits",
        label="Download Folder",
        full_width=True,
    )
    extracted_commits_folder_input
    return (extracted_commits_folder_input,)


@app.cell(hide_code=True)
def _(
    GITHUB_URL,
    Path,
    branch_dropdown,
    extracted_commits_folder_input,
    mo,
    overwrite_switch,
    run_extract,
    subprocess,
    sys,
):
    COMMIT_DIR = extracted_commits_folder_input.value

    if run_extract.value:
        script = Path("./commit_extractor.py")
        cmd = [
            sys.executable,
            str(script),
            GITHUB_URL,
            COMMIT_DIR,
            "--branch", branch_dropdown.value,
        ]
        if overwrite_switch.value:
            cmd.append("--overwrite")

        with mo.redirect_stdout():
            print(f"Running commit_extractor.py on branch '{branch_dropdown.value}'...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        with mo.redirect_stdout():
            print("STDOUT:")
            print(result.stdout)
            print("----------------------------------------------------")
            print("STDERR:")
            print(result.stderr)
    return


@app.cell(hide_code=True)
def _(mo):
    run_extract = mo.ui.run_button(label="Extract commits")
    run_extract
    return (run_extract,)


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Configuration
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    commits_folder_input = mo.ui.text(
        value="./extracted_commits",
        label="Commits Folder",
        full_width=True,
    )

    puzzles_folder_input = mo.ui.text(
        value="./puzzles/repo",
        label="Puzzles Folder",
        full_width=True,
    )

    db_path_input = mo.ui.text(
        value="./benchmark_results.db",
        label="Database Path",
        full_width=True,
    )

    mo.vstack([
        commits_folder_input,
        puzzles_folder_input,
        db_path_input,
    ])
    return commits_folder_input, db_path_input, puzzles_folder_input


@app.cell(hide_code=True)
def _(mo):
    compiler_input = mo.ui.text(
        value="gcc",
        label="Compiler",
        full_width=True,
    )
    cflags_input = mo.ui.text(
        value="-Wall -pedantic -std=c99 -O2 -flto=auto",
        label="CFLAGS",
        full_width=True,
    )
    ldflags_input = mo.ui.text(
        value="-flto=auto",
        label="LDFLAGS (for linking)",
        full_width=True,
    )

    mo.vstack([compiler_input, cflags_input, ldflags_input])
    return cflags_input, compiler_input, ldflags_input


@app.cell(hide_code=True)
def _(mo):
    repetitions_input = mo.ui.slider(
        start=1,
        stop=100,
        value=100,
        label="Repetitions per puzzle (hyperfine runs)",
        show_value=True,
    )
    warmup_input = mo.ui.slider(
        start=0,
        stop=10,
        value=5,
        label="Warmup runs (hyperfine --warmup)",
        show_value=True,
    )
    mo.vstack([repetitions_input, warmup_input])
    return repetitions_input, warmup_input


@app.cell(hide_code=True)
def _(mo):
    benchmark_name_input = mo.ui.text(
        value="",
        label="Benchmark Run Name (optional)",
        placeholder="e.g., 'baseline', 'after-optimization', 'gcc-vs-clang'",
        full_width=True,
    )

    num_runs_input = mo.ui.number(
        value=1,
        start=1,
        stop=20,
        step=1,
        label="Number of runs",
    )

    mo.vstack([benchmark_name_input, num_runs_input])
    return benchmark_name_input, num_runs_input


@app.cell(hide_code=True)
def _(sqlite3):
    def init_database(db_path: str) -> sqlite3.Connection:
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                commit_hash TEXT PRIMARY KEY,
                commit_date TEXT,
                commit_message TEXT,
                commit_url TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                timestamp TEXT,
                compiler TEXT,
                cflags TEXT,
                ldflags TEXT,
                repetitions INTEGER,
                warmup INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark_run_id INTEGER,
                commit_hash TEXT,
                puzzle_name TEXT,
                puzzle_size TEXT,
                puzzle_density INTEGER,
                puzzle_id INTEGER,
                repetition INTEGER,
                time_ns INTEGER,
                time_ms REAL,
                mean_ms REAL,
                stddev_ms REAL,
                median_ms REAL,
                min_ms REAL,
                max_ms REAL,
                user_ms REAL,
                system_ms REAL,
                timestamp TEXT,
                FOREIGN KEY (benchmark_run_id) REFERENCES benchmark_runs(id),
                FOREIGN KEY (commit_hash) REFERENCES commits(commit_hash)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_commit ON runs(commit_hash)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_puzzle ON runs(puzzle_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_benchmark ON runs(benchmark_run_id)
        """)
        conn.commit()
        return conn

    def create_benchmark_run(
        conn: sqlite3.Connection,
        name: str,
        compiler: str,
        cflags: str,
        ldflags: str,
        repetitions: int,
        warmup: int,
    ) -> int:
        """Create a new benchmark run and return its ID."""
        from datetime import datetime

        cursor = conn.execute(
            """
            INSERT INTO benchmark_runs (name, timestamp, compiler, cflags, ldflags, repetitions, warmup)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                datetime.now().isoformat(),
                compiler,
                cflags,
                ldflags,
                repetitions,
                warmup,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_benchmark_runs(db_path: str) -> list[dict]:
        """Get all benchmark runs from the database."""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT br.*, COUNT(r.id) as run_count
                FROM benchmark_runs br
                LEFT JOIN runs r ON br.id = r.benchmark_run_id
                GROUP BY br.id
                ORDER BY br.timestamp DESC
            """)
            runs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return runs
        except Exception:
            return []

    def delete_benchmark_run(db_path: str, run_id: int) -> bool:
        """Delete a benchmark run and all its associated data."""
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                "DELETE FROM runs WHERE benchmark_run_id = ?", (run_id,)
            )
            conn.execute("DELETE FROM benchmark_runs WHERE id = ?", (run_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    return (
        create_benchmark_run,
        delete_benchmark_run,
        get_benchmark_runs,
        init_database,
    )


@app.cell(hide_code=True)
def _(Path, re):
    def parse_puzzle_filename(filename: str) -> dict:
        """Parse puzzle filename like rand_5x5_d8_20.cfg"""
        name = Path(filename).stem

        # Try to parse the format: name_SIZExSIZE_dDENSITY_ID
        pattern = r"^(.+?)_(\d+x\d+)_d(\d+)_(\d+)$"
        match = re.match(pattern, name)

        if match:
            return {
                "name": match.group(1),
                "size": match.group(2),
                "density": int(match.group(3)),
                "id": int(match.group(4)),
            }
        else:
            return {
                "name": name,
                "size": "unknown",
                "density": 0,
                "id": 0,
            }
    return (parse_puzzle_filename,)


@app.cell(hide_code=True)
def _(Path, subprocess):
    REQUIRED_FILES = [
        "solver.c",
        "solver.h",
        "stacks.c",
        "stacks.h",
        "solverio.c",
        "presolver.c",
        "stocks.c",
    ]

    def check_commit_folder(commit_path: Path) -> tuple[bool, list[str]]:
        """Check if a commit folder has all required files."""
        missing = []
        for f in REQUIRED_FILES:
            if not (commit_path / f).exists():
                missing.append(f)
        return len(missing) == 0, missing

    def compile_solver(commit_path: Path, compiler: str, cflags: str, ldflags: str) -> tuple[bool, str]:
        """Compile the nonogram solver in the given commit folder."""
        sources = ["solver.c", "stacks.c", "solverio.c", "presolver.c", "stocks.c"]
        objects = []

        for src in sources:
            obj = src.replace(".c", ".o")
            objects.append(obj)
            cmd = f"{compiler} {cflags} -c {src} -o {obj}"
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=commit_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return False, f"Failed to compile {src}: {result.stderr}"

        obj_str = " ".join(objects)
        cmd = f"{compiler} {ldflags} -o nonograms {obj_str}"
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=commit_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, f"Failed to link: {result.stderr}"

        return True, "Compilation successful"

    def parse_commit_info(commit_path: Path) -> dict:
        """Parse commit_message.txt to extract commit info."""
        info_file = commit_path / "commit_message.txt"
        if not info_file.exists():
            folder_name = commit_path.name
            parts = folder_name.split("_")
            if len(parts) >= 5:
                return {
                    "hash": parts[4] if len(parts) > 4 else folder_name,
                    "date": f"{parts[0]}-{parts[1]}-{parts[2]} {parts[3][:2]}:{parts[3][2:]}" if len(parts) >= 4 else "",
                    "message": "",
                    "url": "",
                }
            return {"hash": folder_name, "date": "", "message": "", "url": ""}

        content = info_file.read_text()
        lines = content.strip().split("\n")

        url = lines[0] if lines else ""
        message = "\n".join(lines[2:]) if len(lines) > 2 else ""

        hash_match = url.split("/commit/")[-1] if "/commit/" in url else ""

        folder_name = commit_path.name
        parts = folder_name.split("_")
        date = f"{parts[0]}-{parts[1]}-{parts[2]} {parts[3][:2]}:{parts[3][2:]}" if len(parts) >= 5 else ""

        return {
            "hash": hash_match,
            "date": date,
            "message": message,
            "url": url,
        }
    return check_commit_folder, compile_solver, parse_commit_info


@app.cell(hide_code=True)
def _(json, subprocess):
    def run_benchmark_batch(
        executable: str,
        puzzle_paths: list[str],
        repetitions: int = 10,
        warmup: int = 3,
    ) -> dict[str, dict]:
        """Run benchmark using hyperfine for multiple puzzles in one call.

        Returns a dict mapping puzzle_path -> {
            "times": [...],  # individual run times in ms
            "mean": float,   # mean time in ms
            "stddev": float, # standard deviation in ms
            "median": float, # median time in ms
            "min": float,    # min time in ms
            "max": float,    # max time in ms
            "user": float,   # user CPU time in ms
            "system": float, # system CPU time in ms
        }
        """
        if not puzzle_paths:
            return {}

        commands = [f"{executable} {p}" for p in puzzle_paths]

        cmd = [
            "hyperfine",
            "--runs",
            str(repetitions),
            "--warmup",
            str(warmup),
            "--export-json",
            "/dev/stdout",
            "--style",
            "none",
            *commands,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                p: {"error": f"Hyperfine failed: {result.stderr}"}
                for p in puzzle_paths
            }

        # Find the last complete JSON object (hyperfine prints incrementally)
        stdout = result.stdout.strip()
        last_json_start = stdout.rfind('{\n  "results":')
        if last_json_start == -1:
            return {
                p: {"error": "No JSON found in hyperfine output"}
                for p in puzzle_paths
            }

        json_str = stdout[last_json_start:]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return {
                p: {"error": f"Failed to parse hyperfine JSON: {e}"}
                for p in puzzle_paths
            }

        results = {}
        for i, benchmark in enumerate(data.get("results", [])):
            puzzle_path = (
                puzzle_paths[i] if i < len(puzzle_paths) else f"unknown_{i}"
            )

            times_s = benchmark.get("times", [])
            times_ms = [t * 1000 for t in times_s]

            results[puzzle_path] = {
                "times": times_ms,
                "mean": (benchmark.get("mean") or 0) * 1000,
                "stddev": (benchmark.get("stddev") or 0) * 1000,
                "median": (benchmark.get("median") or 0) * 1000,
                "min": (benchmark.get("min") or 0) * 1000,
                "max": (benchmark.get("max") or 0) * 1000,
                "user": (benchmark.get("user") or 0) * 1000,
                "system": (benchmark.get("system") or 0) * 1000,
            }

        return results
    return (run_benchmark_batch,)


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(
    IMPORTANT_COMMITS,
    Path,
    check_commit_folder,
    commits_folder_input,
    hide_2013_input,
    hide_invalid_input,
    important_only_input,
    mo,
    parse_commit_info,
):
    def is_important_commit(folder_name: str) -> bool:
        """Check if a folder name contains any of the important commit hashes."""
        for commit_hash in IMPORTANT_COMMITS:
            if commit_hash[0:6] in folder_name:
                return True
        return False


    def get_available_commits():
        commits_path = Path(commits_folder_input.value)
        if not commits_path.exists():
            return []
        commits = []
        for folder in sorted(commits_path.iterdir()):
            if folder.is_dir() and not folder.name.startswith("."):
                is_valid, missing = check_commit_folder(folder)
                info = parse_commit_info(folder)
                commits.append({
                    "folder": folder.name,
                    "path": folder,
                    "valid": is_valid,
                    "missing": missing,
                    "info": info,
                })
        return commits


    available_commits = get_available_commits()
    shown_commits = available_commits

    # hide invalid
    if hide_invalid_input.value:
        shown_commits = [c for c in shown_commits if c["valid"]]

    # hide folders starting with 2013
    if hide_2013_input.value:
        shown_commits = [c for c in shown_commits if not c["folder"].startswith("2013")]

    # show only important commits
    if important_only_input.value:
        shown_commits = [c for c in shown_commits if is_important_commit(c["folder"])]

    commit_options = {
        f"{c['folder']} {'🟩' if c['valid'] else '🟥'}": c['folder']
        for c in shown_commits
    }

    commit_selector = mo.ui.multiselect(
        options=commit_options,
        label="Select Commits to Benchmark",
        value=list(commit_options.keys()) if commit_options else [],
        full_width=True,
    )

    mo.md("## Select Commits") if available_commits else mo.md("## Select Commits\n\n⚠️ No commits found.")
    return commit_selector, shown_commits


@app.cell(hide_code=True)
def _(mo):
    HIDE_INVALID = True
    HIDE_2013 = True
    IMPORTANT_ONLY = True

    IMPORTANT_COMMITS = {
        "467ae19",      # 30.11.25
        "44fd2102f534e2df9a5f5565ef8f6a6641b0c5ed",  # stacks
        "3c9fefd",      # 15.01.2026 Presolver
        "94219d1f938076b8d77c7d82e30a04264c0c9ae7",  # compiler optimization
        "bb5f8964137f6e54b4944e7e584da7b3e01a24f6",  # link time optimization
        "94d7dfee57cff1a2b9ef22b47c1aacc082750095",
        "2a58a480e6e4a995922a8fdb08d3961495a3560b",
        "44e521facae159a3e367554fc0972d7de98db7c7",
        "9af58700a0c438ab76228837f82e9722dbc247ca",
        "5a2549783187c82775451e6d094224cac4d8a8b6",
        "c2160c2a24cb93151b5b574346cc9e67bff3ed21",
    }

    hide_invalid_input = mo.ui.switch(value=HIDE_INVALID, label="Hide invalid")
    hide_2013_input = mo.ui.switch(value=HIDE_2013, label="Hide 2013")
    important_only_input = mo.ui.switch(value=IMPORTANT_ONLY, label="Important only")
    mo.hstack([important_only_input, hide_invalid_input, hide_2013_input], justify="start")
    return (
        IMPORTANT_COMMITS,
        hide_2013_input,
        hide_invalid_input,
        important_only_input,
    )


@app.cell(hide_code=True)
def _(commit_selector, mo):
    mo.vstack([
        commit_selector,
        mo.md("🟩 Valid  🟥 Missing files")
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(Path, mo, parse_puzzle_filename, puzzles_folder_input):
    def get_available_puzzles():
        puzzles_path = Path(puzzles_folder_input.value)
        if not puzzles_path.exists():
            return []

        puzzles = []
        for f in sorted(puzzles_path.glob("*.cfg")):
            info = parse_puzzle_filename(f.name)
            puzzles.append({
                "file": f.name,
                "path": f,
                **info,
            })
        return puzzles

    available_puzzles = get_available_puzzles()
    puzzle_options = {p["file"]: p["file"] for p in available_puzzles}

    puzzle_selector = mo.ui.multiselect(
        options=puzzle_options,
        label="Select Puzzles",
        value=list(puzzle_options.values())[:5] if puzzle_options else [],
        full_width=True,
    )

    mo.md("## Select Puzzles") if available_puzzles else mo.md("## Select Puzzles\n\n⚠️ No puzzles found.")
    return (available_puzzles,)


@app.cell(hide_code=True)
def _(available_puzzles, mo):
    unique_names = sorted(set(p["name"] for p in available_puzzles))
    unique_sizes = sorted(set(p["size"] for p in available_puzzles))
    unique_densities = sorted(set(p["density"] for p in available_puzzles))
    unique_ids = sorted(set(p["id"] for p in available_puzzles))

    name_filter = mo.ui.multiselect(
        options={n: n for n in unique_names},
        value=unique_names,
        label="Name",
    )
    size_filter = mo.ui.multiselect(
        options={s: s for s in unique_sizes},
        value=unique_sizes,
        label="Size",
    )
    density_filter = mo.ui.multiselect(
        options={str(d): d for d in unique_densities},
        value=[str(d) for d in unique_densities],
        label="Density",
    )
    id_filter = mo.ui.multiselect(
        options={str(i): i for i in unique_ids},
        value=[str(i) for i in unique_ids],
        label="ID",
    )

    mo.hstack([name_filter, size_filter, density_filter, id_filter])
    return density_filter, id_filter, name_filter, size_filter


@app.cell(hide_code=True)
def _(
    available_puzzles,
    density_filter,
    id_filter,
    mo,
    name_filter,
    size_filter,
):
    filtered_puzzles = [
        p["file"] for p in available_puzzles
        if p["name"] in name_filter.value
        and p["size"] in size_filter.value
        and p["density"] in density_filter.value
        and p["id"] in id_filter.value
    ]

    mo.md(f"**{len(filtered_puzzles)} puzzles** match the filter")
    return (filtered_puzzles,)


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Run Benchmark
    """)
    return


@app.cell(hide_code=True)
def _(commit_selector, filtered_puzzles, mo):
    mo.hstack([mo.vstack(["Commits", commit_selector.value]), mo.vstack(["Puzzles", filtered_puzzles])])
    return


@app.cell(hide_code=True)
def _(
    commit_selector,
    filtered_puzzles,
    mo,
    num_runs_input,
    repetitions_input,
    warmup_input,
):
    _num_runs = len(commit_selector.value) * len(filtered_puzzles) * repetitions_input.value
    _num_runs += warmup_input.value * len(commit_selector.value) * len(filtered_puzzles)
    run_button = mo.ui.run_button(label=f"Run Benchmark | {_num_runs:,} runs | {num_runs_input.value} time(s)")
    store_in_db_input = mo.ui.switch(
        value=True,
        label="Store in DB",
    )
    mo.hstack([run_button, store_in_db_input], justify="start", gap=2)
    return run_button, store_in_db_input


@app.cell(hide_code=True)
def _(
    Path,
    available_puzzles,
    benchmark_name_input,
    cflags_input,
    check_commit_folder,
    commit_selector,
    commits_folder_input,
    compile_solver,
    compiler_input,
    create_benchmark_run,
    datetime,
    db_path_input,
    filtered_puzzles,
    init_database,
    ldflags_input,
    mo,
    num_runs_input,
    parse_commit_info,
    puzzles_folder_input,
    repetitions_input,
    run_benchmark_batch,
    run_button,
    store_in_db_input,
    warmup_input,
):
    DEBUG = True
    use_db = store_in_db_input.value

    benchmark_results = []
    current_benchmark_run_id = None

    if run_button.value and commit_selector.value and filtered_puzzles:
        import time as bench_time

        total_start = bench_time.perf_counter()

        conn = None
        try:
            conn = init_database(db_path_input.value) if use_db else None
            if conn:
                conn.execute("PRAGMA busy_timeout = 5000")

            commits_path = Path(commits_folder_input.value)
            puzzles_path = Path(puzzles_folder_input.value)

            total_commits = len(commit_selector.value)

            # Multiple runs loop
            base_run_name = benchmark_name_input.value.strip()
            num_runs = int(num_runs_input.value)

            for run_idx in range(1, num_runs + 1):
                # Determine run name with suffix
                if num_runs > 1:
                    run_name = f"{base_run_name}-{run_idx}" if base_run_name else f"run-{run_idx}"
                else:
                    run_name = base_run_name or f"Run {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                if DEBUG:
                    print(f"[DEBUG] Starting run {run_idx}/{num_runs}: {run_name}")

                # Create a new benchmark run entry
                if use_db:
                    current_benchmark_run_id = create_benchmark_run(
                        conn,
                        run_name,
                        compiler_input.value,
                        cflags_input.value,
                        ldflags_input.value,
                        repetitions_input.value,
                        warmup_input.value,
                    )

                with mo.status.progress_bar(total=total_commits, title=f"Run {run_idx}/{num_runs}: {run_name}") as bar:
                    for folder_name in commit_selector.value:
                        commit_start = bench_time.perf_counter()
                        commit_path = commits_path / folder_name

                        is_valid, missing = check_commit_folder(commit_path)
                        if not is_valid:
                            if DEBUG:
                                print(f"[DEBUG] Skipping {folder_name}: missing {missing}")
                            bar.update(increment=1, subtitle=f"Skipping {folder_name}")
                            continue

                        info = parse_commit_info(commit_path)

                        if use_db:
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO commits (commit_hash, commit_date, commit_message, commit_url)
                                VALUES (?, ?, ?, ?)
                                """,
                                (info["hash"], info["date"], info["message"], info["url"]),
                            )

                        compile_start = bench_time.perf_counter()
                        success, msg = compile_solver(
                            commit_path,
                            compiler_input.value,
                            cflags_input.value,
                            ldflags_input.value,
                        )
                        if DEBUG:
                            print(f"[DEBUG] Compile {folder_name}: {bench_time.perf_counter() - compile_start:.2f}s")

                        if not success:
                            if DEBUG:
                                print(f"[DEBUG] Compilation failed: {msg}")
                            bar.update(increment=1, subtitle=f"Compile failed: {folder_name}")
                            continue

                        executable = str(commit_path / "nonograms")

                        # Build list of full puzzle paths
                        puzzle_paths = [str(puzzles_path / pf) for pf in filtered_puzzles]

                        bar.update(increment=0, subtitle=f"{folder_name} · running hyperfine on {len(puzzle_paths)} puzzles...")

                        hyperfine_start = bench_time.perf_counter()
                        batch_results = run_benchmark_batch(
                            executable,
                            puzzle_paths,
                            repetitions_input.value,
                            warmup_input.value,
                        )
                        if DEBUG:
                            print(f"[DEBUG] Hyperfine {folder_name} ({len(puzzle_paths)} puzzles, {repetitions_input.value} reps each): {bench_time.perf_counter() - hyperfine_start:.2f}s")

                        runs_to_insert = []

                        for puzzle_file in filtered_puzzles:
                            puzzle_path = str(puzzles_path / puzzle_file)
                            puzzle_info = next((p for p in available_puzzles if p["file"] == puzzle_file), {})

                            metrics = batch_results.get(puzzle_path, {})

                            if "error" in metrics:
                                if DEBUG:
                                    print(f"[DEBUG] Error {puzzle_file}: {metrics['error']}")
                                continue

                            times_ms = metrics.get("times", [])

                            for rep, time_ms in enumerate(times_ms, 1):
                                time_ns = int(time_ms * 1_000_000)

                                if use_db:
                                    runs_to_insert.append(
                                        (
                                            current_benchmark_run_id,
                                            info["hash"],
                                            puzzle_file,
                                            puzzle_info.get("size", "unknown"),
                                            puzzle_info.get("density", 0),
                                            puzzle_info.get("id", 0),
                                            rep,
                                            time_ns,
                                            time_ms,
                                            metrics.get("mean", 0),
                                            metrics.get("stddev", 0),
                                            metrics.get("median", 0),
                                            metrics.get("min", 0),
                                            metrics.get("max", 0),
                                            metrics.get("user", 0),
                                            metrics.get("system", 0),
                                            datetime.now().isoformat(),
                                        )
                                    )

                                benchmark_results.append(
                                    {
                                        "benchmark_run_id": current_benchmark_run_id,
                                        "commit": folder_name,
                                        "commit_hash": info["hash"][:8],
                                        "puzzle": puzzle_file,
                                        "size": puzzle_info.get("size", "unknown"),
                                        "density": puzzle_info.get("density", 0),
                                        "rep": rep,
                                        "time_ms": time_ms,
                                        "mean_ms": metrics.get("mean", 0),
                                        "stddev_ms": metrics.get("stddev", 0),
                                        "median_ms": metrics.get("median", 0),
                                        "min_ms": metrics.get("min", 0),
                                        "max_ms": metrics.get("max", 0),
                                        "user_ms": metrics.get("user", 0),
                                        "system_ms": metrics.get("system", 0),
                                    }
                                )

                        if use_db and runs_to_insert:
                            db_start = bench_time.perf_counter()
                            conn.executemany(
                                """
                                INSERT INTO runs (
                                    benchmark_run_id, commit_hash, puzzle_name, puzzle_size, puzzle_density, puzzle_id,
                                    repetition, time_ns, time_ms, mean_ms, stddev_ms, median_ms, min_ms, max_ms,
                                    user_ms, system_ms, timestamp
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                runs_to_insert,
                            )
                            conn.commit()
                            if DEBUG:
                                print(f"[DEBUG] DB insert ({len(runs_to_insert)} rows): {bench_time.perf_counter() - db_start:.3f}s")

                        if DEBUG:
                            print(f"[DEBUG] Commit {folder_name} total: {bench_time.perf_counter() - commit_start:.2f}s")

                        bar.update(increment=1, subtitle=f"{folder_name} · done")

                    bar.update(increment=0, subtitle="Done")

            if DEBUG:
                print(f"[DEBUG] Total ({num_runs} runs): {bench_time.perf_counter() - total_start:.2f}s")

        finally:
            if conn is not None:
                conn.close()
    return (benchmark_results,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Results
    """)
    return


@app.cell(hide_code=True)
def _(benchmark_results, mo, pd):
    df_benchmark_results = pd.DataFrame(benchmark_results)
    mo.ui.table(df_benchmark_results) if benchmark_results else mo.md("No benchmark results to display.")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Historical Data
    """)
    return


@app.cell(hide_code=True)
def _(btn_refresh_benchmark_selector, db_path_input, get_benchmark_runs, mo):
    def get_benchmark_run_selector():
        stored_runs = get_benchmark_runs(db_path_input.value)
        if stored_runs:
            run_options = {
                f"#{r['id']}: {r['name']} ({r['timestamp'][:16]}) - {r['run_count']} results": r['id']
                for r in stored_runs
            }
            benchmark_run_selector = mo.ui.multiselect(
                options=run_options,
                label="Select Benchmark Runs to Plot",
                value=[list(run_options.keys())[0]] if run_options else [],
                full_width=True,
            )
        else:
            benchmark_run_selector = mo.ui.multiselect(
                options={},
                label="Select Benchmark Runs to Plot",
                value=[],
                full_width=True,
            )
        return benchmark_run_selector, stored_runs

    # Always create the selector (refresh button just triggers re-evaluation)
    benchmark_run_selector, stored_runs = get_benchmark_run_selector()

    # Reference the button to create reactivity (when clicked, cell re-runs)
    btn_refresh_benchmark_selector

    mo.vstack([
        mo.md("### Select Benchmark Runs"),
        benchmark_run_selector
    ])
    return benchmark_run_selector, stored_runs


@app.cell(hide_code=True)
def _(mo):
    btn_refresh_benchmark_selector = mo.ui.run_button(label="Refresh Benchmark Runs Selector")
    btn_refresh_benchmark_selector
    return (btn_refresh_benchmark_selector,)


@app.cell(hide_code=True)
def _(mo):
    sort_by_time_switch = mo.ui.switch(label="Sort commits by avg time", value=False)

    date_start = mo.ui.date(label="From", value="2025-11-01")
    date_end = mo.ui.date(label="To", value=None)

    max_improve_pct = mo.ui.number(label="Max improve (%)", value=500, start=0, stop=1000)
    max_worsen_pct = mo.ui.number(label="Max worsen (%)", value=500, start=0, stop=1000)

    btn_show_plots = mo.ui.run_button(label="Show Plots")

    mo.vstack([
        mo.hstack([date_start, date_end, sort_by_time_switch], gap=2, justify="start"),
        mo.hstack([max_improve_pct, max_worsen_pct], gap=2, justify="start"),
        btn_show_plots,
    ])
    return (
        btn_show_plots,
        date_end,
        date_start,
        max_improve_pct,
        max_worsen_pct,
        sort_by_time_switch,
    )


@app.cell(hide_code=True)
def _(
    benchmark_run_selector,
    date_end,
    date_start,
    db_path_input,
    max_improve_pct,
    max_worsen_pct,
    mo,
    pd,
    plt,
    sort_by_time_switch,
    sqlite3,
):
    # Line graph + Table

    def load_benchmark_data(db_path: str, run_ids: list[int]) -> pd.DataFrame:
        """Load benchmark data for selected runs from the database."""
        if not run_ids:
            return pd.DataFrame()
        conn = sqlite3.connect(db_path)
        placeholders = ",".join("?" * len(run_ids))
        query = f"""
            SELECT 
                r.benchmark_run_id,
                br.name as run_name,
                r.commit_hash,
                c.commit_date,
                c.commit_message,
                r.puzzle_name,
                r.puzzle_size,
                r.puzzle_density,
                r.repetition,
                r.time_ms
            FROM runs r
            JOIN benchmark_runs br ON r.benchmark_run_id = br.id
            JOIN commits c ON r.commit_hash = c.commit_hash
            WHERE r.benchmark_run_id IN ({placeholders})
        """
        df = pd.read_sql_query(query, conn, params=run_ids)
        conn.close()
        return df

    def show_graph():
        selected_run_ids = benchmark_run_selector.value if benchmark_run_selector.value else []
        df_historical = load_benchmark_data(db_path_input.value, selected_run_ids)
        if not df_historical.empty:
            # Parse commit_date for filtering
            df_historical["commit_date_parsed"] = pd.to_datetime(
                df_historical["commit_date"].str[:10]
            )
            # Filter by date range
            if date_start.value is not None:
                df_historical = df_historical[
                    df_historical["commit_date_parsed"] >= pd.to_datetime(date_start.value)
                ]
            if date_end.value is not None:
                df_historical = df_historical[
                    df_historical["commit_date_parsed"] <= pd.to_datetime(date_end.value)
                ]
            if df_historical.empty:
                return mo.md("No data in selected date range."), pd.DataFrame()

            # Group by run and commit, keep commit_date and commit_message for sorting
            avg_time = df_historical.groupby(
                ["benchmark_run_id", "run_name", "commit_hash", "commit_date", "commit_message"]
            )["time_ms"].mean().reset_index()

            # Compute global average time per commit (across all runs) for sorting
            commit_avg = avg_time.groupby("commit_hash")["time_ms"].mean().reset_index()
            commit_avg.columns = ["commit_hash", "global_avg_time"]

            # Build a reference table of commits
            commit_order = (
                avg_time[["commit_hash", "commit_date", "commit_message"]]
                .drop_duplicates()
                .merge(commit_avg, on="commit_hash")
            )

            # Sort by avg time or by date
            if sort_by_time_switch.value:
                commit_order = commit_order.sort_values("global_avg_time", ascending=False)
            else:
                commit_order = commit_order.sort_values("commit_date")
            commit_order = commit_order.reset_index(drop=True)
            commit_order["x"] = commit_order.index

            # Filter commits based on percentage change from previous point PER BENCHMARK RUN
            if max_improve_pct.value is not None or max_worsen_pct.value is not None:
                valid_commits_per_run = []

                for run_id in avg_time["benchmark_run_id"].unique():
                    run_data = avg_time[avg_time["benchmark_run_id"] == run_id].copy()
                    # Merge with commit order to get sorting position
                    run_data = run_data.merge(commit_order[["commit_hash", "x"]], on="commit_hash")
                    run_data = run_data.sort_values("x").reset_index(drop=True)

                    # Calculate percentage change from previous commit for this run
                    run_data["prev_time"] = run_data["time_ms"].shift(1)
                    run_data["pct_change"] = (
                        (run_data["time_ms"] - run_data["prev_time"]) 
                        / run_data["prev_time"]
                    ) * 100

                    # First commit has no previous, always keep it
                    mask = pd.Series([True] * len(run_data))

                    # Max improve: filter out commits that improved MORE than max_improve_pct
                    if max_improve_pct.value is not None:
                        mask &= (run_data["pct_change"].isna()) | (run_data["pct_change"] >= -max_improve_pct.value)

                    # Max worsen: filter out commits that worsened MORE than max_worsen_pct
                    if max_worsen_pct.value is not None:
                        mask &= (run_data["pct_change"].isna()) | (run_data["pct_change"] <= max_worsen_pct.value)

                    valid_commits_per_run.append(set(run_data[mask]["commit_hash"].tolist()))

                # Only keep commits that are valid across ALL runs
                if valid_commits_per_run:
                    valid_commits = set.intersection(*valid_commits_per_run)
                else:
                    valid_commits = set()

                avg_time = avg_time[avg_time["commit_hash"].isin(valid_commits)]
                commit_order = commit_order[commit_order["commit_hash"].isin(valid_commits)].reset_index(drop=True)
                commit_order["x"] = commit_order.index

            if avg_time.empty:
                return mo.md("No data remaining after applying percentage bounds filter."), pd.DataFrame()

            if sort_by_time_switch.value:
                # Only commit hash when sorted by time
                commit_order["label"] = commit_order["commit_hash"].str[:8]
            else:
                # Date + commit hash when chronological
                commit_order["label"] = (
                    pd.to_datetime(commit_order["commit_date"].str[:10])
                    .dt.strftime("%m-%d")
                    + " "
                    + commit_order["commit_hash"].str[:8]
                )

            # Merge x positions back into avg_time
            avg_time = avg_time.merge(commit_order[["commit_hash", "x"]], on="commit_hash")

            # Create two subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

            # Plot 1: Individual benchmark runs
            for run_id in avg_time["benchmark_run_id"].unique():
                run_data = avg_time[avg_time["benchmark_run_id"] == run_id].sort_values("x")
                run_fullname = run_data["run_name"].iloc[0]
                ax1.plot(
                    run_data["x"],
                    run_data["time_ms"],
                    marker="o",
                    linestyle="-",
                    label=f"#{run_id}: {run_fullname}",
                )

            ax1.set_ylabel("Avg Time (ms)")
            ax1.set_title("Average Execution Time per Commit (Individual Runs)")
            ax1.legend(loc="best")

            # Plot 2: Average across all runs
            avg_across_runs = avg_time.groupby(["commit_hash", "x"])["time_ms"].mean().reset_index()
            avg_across_runs = avg_across_runs.sort_values("x")

            ax2.plot(
                avg_across_runs["x"],
                avg_across_runs["time_ms"],
                marker="o",
                linestyle="-",
                color="black",
                linewidth=2,
                label="Average of all runs",
            )

            # Set x-tick labels
            ax2.set_xticks(commit_order["x"])
            ax2.set_xticklabels(commit_order["label"], rotation=45, ha="right")
            ax2.set_xlabel("Commit (sorted by avg time)" if sort_by_time_switch.value else "Commit (chronological)")
            ax2.set_ylabel("Avg Time (ms)")
            ax2.set_title("Average Execution Time per Commit (Mean Across All Runs)")
            ax2.legend(loc="best")

            plt.tight_layout()

            # Build table dataframe with speedup info
            commit_table = commit_order[["commit_hash", "commit_date", "commit_message", "global_avg_time"]].copy()
            commit_table["prev_time"] = commit_table["global_avg_time"].shift(1)
            commit_table["speedup_pct"] = ((commit_table["prev_time"] - commit_table["global_avg_time"]) / commit_table["prev_time"] * 100).round(2)
            commit_table = commit_table.rename(columns={
                "commit_hash": "Commit Hash",
                "commit_date": "Date",
                "commit_message": "Message",
                "global_avg_time": "Time (ms)",
                "prev_time": "Prev Time (ms)",
                "speedup_pct": "Speedup (%)"
            })
            commit_table["Time (ms)"] = commit_table["Time (ms)"].round(3)
            commit_table["Prev Time (ms)"] = commit_table["Prev Time (ms)"].round(3)

            return fig, commit_table
        else:
            return mo.md("No historical data to display. Select benchmark runs above."), pd.DataFrame()
    return (show_graph,)


@app.cell(hide_code=True)
def _(
    benchmark_run_selector,
    db_path_input,
    mo,
    pd,
    plt,
    sort_by_time_switch,
    sqlite3,
):
    # Boxplot
    def load_benchmark_data_boxplot(db_path: str, run_ids: list[int]) -> pd.DataFrame:
        """Load benchmark data for selected runs from the database."""
        if not run_ids:
            return pd.DataFrame()
        conn = sqlite3.connect(db_path)
        placeholders = ",".join("?" * len(run_ids))
        query = f"""
            SELECT 
                r.benchmark_run_id,
                br.name as run_name,
                r.commit_hash,
                c.commit_date,
                r.puzzle_name,
                r.time_ms
            FROM runs r
            JOIN benchmark_runs br ON r.benchmark_run_id = br.id
            JOIN commits c ON r.commit_hash = c.commit_hash
            WHERE r.benchmark_run_id IN ({placeholders})
        """
        df = pd.read_sql_query(query, conn, params=run_ids)
        conn.close()
        return df

    def show_boxplot():
        selected_run_ids = benchmark_run_selector.value if benchmark_run_selector.value else []
        df_historical = load_benchmark_data_boxplot(db_path_input.value, selected_run_ids)
        if not df_historical.empty:
            # Compute average time per commit for sorting
            commit_avg = df_historical.groupby("commit_hash")["time_ms"].mean().reset_index()
            commit_avg.columns = ["commit_hash", "global_avg_time"]
            # Build commit order reference
            commit_order = (
                df_historical[["commit_hash", "commit_date"]]
                .drop_duplicates()
                .merge(commit_avg, on="commit_hash")
            )
            # Sort by avg time or by date
            if sort_by_time_switch.value:
                commit_order = commit_order.sort_values("global_avg_time", ascending=False)
            else:
                commit_order = commit_order.sort_values("commit_date")
            commit_order = commit_order.reset_index(drop=True)
            commit_order["x"] = commit_order.index
            # Create labels
            if sort_by_time_switch.value:
                commit_order["label"] = commit_order["commit_hash"].str[:8]
            else:
                commit_order["label"] = (
                    pd.to_datetime(commit_order["commit_date"].str[:10])
                    .dt.strftime("%m-%d")
                    + " "
                    + commit_order["commit_hash"].str[:8]
                )
            # Create ordered list of commits for boxplot
            ordered_commits = commit_order["commit_hash"].tolist()

            # Get unique run IDs and assign colors
            unique_runs = df_historical["benchmark_run_id"].unique()
            colors = plt.cm.tab10(range(len(unique_runs)))
            run_colors = {run_id: colors[i] for i, run_id in enumerate(unique_runs)}

            fig, ax = plt.subplots(figsize=(14, 6))

            # Side by side boxplots for each run
            n_runs = len(unique_runs)
            width = 0.8 / n_runs

            for i, run_id in enumerate(unique_runs):
                run_data = df_historical[df_historical["benchmark_run_id"] == run_id]
                run_name = run_data["run_name"].iloc[0]

                boxplot_data = []
                positions = []
                for j, commit in enumerate(ordered_commits):
                    times = run_data[run_data["commit_hash"] == commit]["time_ms"].values
                    if len(times) > 0:
                        boxplot_data.append(times)
                        positions.append(j + (i - n_runs/2 + 0.5) * width)

                if boxplot_data:
                    bp = ax.boxplot(
                        boxplot_data,
                        positions=positions,
                        widths=width * 0.8,
                        patch_artist=True,
                        showfliers=False,
                    )
                    for patch in bp["boxes"]:
                        patch.set_facecolor(run_colors[run_id])
                        patch.set_alpha(0.7)
                    ax.plot([], [], color=run_colors[run_id], linewidth=10, 
                            label=f"#{run_id}: {run_name}", alpha=0.7)

            ax.set_xticks(range(len(ordered_commits)))
            ax.set_xticklabels(commit_order["label"], rotation=45, ha="right")
            ax.set_xlabel("Commit (sorted by avg time)" if sort_by_time_switch.value else "Commit (chronological)")
            ax.set_ylabel("Time (ms)")
            ax.set_title("Execution Time Distribution per Commit")
            ax.legend(loc="best")
            ax.grid(axis="y", alpha=0.3)

            plt.tight_layout()
            return fig
        else:
            return mo.md("No historical data to display. Select benchmark runs above.")
    return (show_boxplot,)


@app.cell(hide_code=True)
def _(btn_show_plots, mo, show_boxplot, show_graph):
    line_graph = mo.md("Currently no line graph to display. Press Show Plots to generate.")
    commit_table_display = mo.md("")
    boxplot = mo.md("Currently no boxplot to display. Press Show Plots to generate.")

    if btn_show_plots.value:
        line_graph, commit_table = show_graph()
        if not commit_table.empty:
            commit_table_display = mo.ui.table(commit_table)
        boxplot = show_boxplot()

    mo.vstack([
        line_graph,
        commit_table_display,
        boxplot
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Compare
    """)
    return


@app.cell(hide_code=True)
def _(btn_refresh_group_selector, db_path_input, get_benchmark_runs, mo):
    def get_group_selectors():
        stored_runs = get_benchmark_runs(db_path_input.value)
        if stored_runs:
            run_options = {
                f"#{r['id']}: {r['name']} ({r['timestamp'][:16]}) - {r['run_count']} results": r['id']
                for r in stored_runs
            }
            group_a_selector = mo.ui.multiselect(
                options=run_options,
                label="Group A (e.g., baseline runs)",
                value=[],
                full_width=True,
            )
            group_b_selector = mo.ui.multiselect(
                options=run_options,
                label="Group B (e.g., optimized runs)",
                value=[],
                full_width=True,
            )
        else:
            group_a_selector = mo.ui.multiselect(options={}, label="Group A", value=[], full_width=True)
            group_b_selector = mo.ui.multiselect(options={}, label="Group B", value=[], full_width=True)
        return group_a_selector, group_b_selector

    # Always create the selectors (refresh button just triggers re-evaluation)
    group_a_selector, group_b_selector = get_group_selectors()

    # Reference the button to create reactivity (when clicked, cell re-runs)
    btn_refresh_group_selector

    group_a_name = mo.ui.text(value="Group A", label="Group A Name", placeholder="e.g., 'Baseline'")
    group_b_name = mo.ui.text(value="Group B", label="Group B Name", placeholder="e.g., 'Optimized'")

    btn_compare_groups = mo.ui.run_button(label="Compare Groups")

    sort_cmp_by_time_switch = mo.ui.switch(label="Sort commits by avg time", value=False)

    mo.vstack([
        mo.md("### Compare Run Groups"),
        mo.hstack([group_a_name, group_b_name], gap=2),
        group_a_selector,
        group_b_selector,
        sort_cmp_by_time_switch,
        btn_compare_groups,
    ])
    return (
        btn_compare_groups,
        group_a_name,
        group_a_selector,
        group_b_name,
        group_b_selector,
        sort_cmp_by_time_switch,
    )


@app.cell(hide_code=True)
def _(mo):
    btn_refresh_group_selector = mo.ui.run_button(label="Refresh Benchmark Runs")
    btn_refresh_group_selector
    return (btn_refresh_group_selector,)


@app.cell(hide_code=True)
def _(
    db_path_input,
    group_a_name,
    group_a_selector,
    group_b_name,
    group_b_selector,
    mo,
    pd,
    plt,
    sort_cmp_by_time_switch,
    sqlite3,
):
    def load_group_data(db_path: str, run_ids: list[int]) -> pd.DataFrame:
        """Load benchmark data for selected runs from the database."""
        if not run_ids:
            return pd.DataFrame()
        conn = sqlite3.connect(db_path)
        placeholders = ",".join("?" * len(run_ids))
        query = f"""
            SELECT 
                r.benchmark_run_id,
                br.name as run_name,
                r.commit_hash,
                c.commit_date,
                c.commit_message,
                r.time_ms
            FROM runs r
            JOIN benchmark_runs br ON r.benchmark_run_id = br.id
            JOIN commits c ON r.commit_hash = c.commit_hash
            WHERE r.benchmark_run_id IN ({placeholders})
        """
        df = pd.read_sql_query(query, conn, params=run_ids)
        conn.close()
        return df

    def show_group_comparison():
        group_a_ids = group_a_selector.value if group_a_selector.value else []
        group_b_ids = group_b_selector.value if group_b_selector.value else []

        if not group_a_ids and not group_b_ids:
            return mo.md("Select at least one run in either group to compare."), pd.DataFrame()

        df_a = load_group_data(db_path_input.value, group_a_ids)
        df_b = load_group_data(db_path_input.value, group_b_ids)

        if df_a.empty and df_b.empty:
            return mo.md("No data found for selected runs."), pd.DataFrame()

        # Compute average time per commit for each group
        if not df_a.empty:
            avg_a = df_a.groupby(["commit_hash", "commit_date", "commit_message"])["time_ms"].mean().reset_index()
            avg_a["group"] = group_a_name.value or "Group A"
        else:
            avg_a = pd.DataFrame()

        if not df_b.empty:
            avg_b = df_b.groupby(["commit_hash", "commit_date", "commit_message"])["time_ms"].mean().reset_index()
            avg_b["group"] = group_b_name.value or "Group B"
        else:
            avg_b = pd.DataFrame()

        # Combine for plotting
        combined = pd.concat([avg_a, avg_b], ignore_index=True)

        # Get all commits and sort them
        all_commits = combined[["commit_hash", "commit_date", "commit_message"]].drop_duplicates()

        # Compute global average for sorting by time
        global_avg = combined.groupby("commit_hash")["time_ms"].mean().reset_index()
        global_avg.columns = ["commit_hash", "global_avg_time"]
        all_commits = all_commits.merge(global_avg, on="commit_hash")

        if sort_cmp_by_time_switch.value:
            all_commits = all_commits.sort_values("global_avg_time", ascending=False)
        else:
            all_commits = all_commits.sort_values("commit_date")

        all_commits = all_commits.reset_index(drop=True)
        all_commits["x"] = all_commits.index

        # Create labels
        if sort_cmp_by_time_switch.value:
            all_commits["label"] = all_commits["commit_hash"].str[:8]
        else:
            all_commits["label"] = (
                pd.to_datetime(all_commits["commit_date"].str[:10])
                .dt.strftime("%m-%d")
                + " "
                + all_commits["commit_hash"].str[:8]
            )

        # Merge x positions into combined data
        combined = combined.merge(all_commits[["commit_hash", "x"]], on="commit_hash")

        # Plot
        fig, ax = plt.subplots(figsize=(12, 6))

        for group_label in combined["group"].unique():
            group_data = combined[combined["group"] == group_label].sort_values("x")
            color = "blue" if group_label == (group_a_name.value or "Group A") else "red"
            ax.plot(
                group_data["x"],
                group_data["time_ms"],
                marker="o",
                linestyle="-",
                label=group_label,
                color=color,
                linewidth=2,
            )

        ax.set_xticks(all_commits["x"])
        ax.set_xticklabels(all_commits["label"], rotation=45, ha="right")
        ax.set_xlabel("Commit (sorted by avg time)" if sort_cmp_by_time_switch.value else "Commit (chronological)")
        ax.set_ylabel("Avg Time (ms)")
        ax.set_title("Group Comparison: Average Execution Time per Commit")
        ax.legend(loc="best")
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        # Build comparison table
        comparison_table = all_commits[["commit_hash", "commit_date", "global_avg_time"]].copy()
        comparison_table = comparison_table.rename(columns={
            "commit_hash": "Commit Hash",
            "commit_date": "Date",
            "global_avg_time": "Overall Avg (ms)",
        })
        comparison_table["Overall Avg (ms)"] = comparison_table["Overall Avg (ms)"].round(3)

        return fig, comparison_table
    return (show_group_comparison,)


@app.cell(hide_code=True)
def _(btn_compare_groups, mo, pd, show_group_comparison):
    group_comparison_graph = mo.md("_Select runs for each group and click 'Compare Groups' to see the comparison plot._")
    group_comparison_table_display = mo.md("")

    if btn_compare_groups.value:
        group_comparison_graph, comparison_table = show_group_comparison()
        if isinstance(comparison_table, pd.DataFrame) and not comparison_table.empty:
            group_comparison_table_display = mo.ui.table(comparison_table)

    mo.vstack([
        group_comparison_graph,
        group_comparison_table_display,
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Edit Database
    """)
    return


@app.cell(hide_code=True)
def _(db_path_input, mo, pd, sqlite3, stored_runs):
    if stored_runs:
        conn_info = sqlite3.connect(db_path_input.value)
        df_runs_info = pd.read_sql_query("""
            SELECT 
                id as "Run ID",
                name as "Name",
                timestamp as "Timestamp",
                compiler as "Compiler",
                cflags as "CFLAGS",
                repetitions as "Reps",
                warmup as "Warmup"
            FROM benchmark_runs
            ORDER BY timestamp DESC
        """, conn_info)
        conn_info.close()
        _show = True
    else:
        _show = False

    mo.ui.table(df_runs_info) if _show else mo.md("_No benchmark runs stored yet._")
    return


@app.cell(hide_code=True)
def _(btn_refresh_delete_selector, db_path_input, get_benchmark_runs, mo):
    def get_delete_run_selector():
        stored_runs = get_benchmark_runs(db_path_input.value)
        if stored_runs:
            run_options = {
                f"#{r['id']}: {r['name']} ({r['timestamp'][:19].replace('T', ' ')})": r['id']
                for r in stored_runs
            }
            selector = mo.ui.dropdown(
                options=run_options,
                label="Select Run to Delete",
                value=None,
            )
        else:
            selector = mo.ui.dropdown(
                options={},
                label="Select Run to Delete",
                value=None,
            )
        return selector, stored_runs

    # Always create the selector (refresh button just triggers re-evaluation)
    delete_run_selector, _stored_runs_for_delete = get_delete_run_selector()

    # Reference the button to create reactivity (when clicked, cell re-runs)
    btn_refresh_delete_selector

    delete_run_button = mo.ui.run_button(label="Delete Run", kind="danger")

    mo.vstack([
        mo.md("### Delete Benchmark Run"),
        mo.hstack([delete_run_selector, delete_run_button], justify="start", gap=2)
    ])
    return delete_run_button, delete_run_selector


@app.cell(hide_code=True)
def _(mo):
    btn_refresh_delete_selector = mo.ui.button(label="Refresh", kind="neutral")
    btn_refresh_delete_selector
    return (btn_refresh_delete_selector,)


@app.cell(hide_code=True)
def _(
    db_path_input,
    delete_benchmark_run,
    delete_run_button,
    delete_run_selector,
    mo,
):
    _delete_status = None
    if delete_run_button is not None and delete_run_button.value and delete_run_selector is not None and delete_run_selector.value is not None:
        _run_id = delete_run_selector.value
        _success = delete_benchmark_run(db_path_input.value, _run_id)
        if _success:
            _delete_status = mo.md(f"✅ Deleted run #{_run_id}")
        else:
            _delete_status = mo.md(f"❌ Failed to delete run #{_run_id}")
    _delete_status if _delete_status else mo.md("")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Commit Info
    """)
    return


@app.cell(hide_code=True)
def _(mo, shown_commits):
    def create_single_commit_selector():
        single_commit_options = {
            f"{c['folder']} {'🟩' if c['valid'] else '🟥'}": c['folder']
            for c in shown_commits
        }

        return mo.ui.dropdown(
            options=single_commit_options,
            label="Select Single Commit",
            value=list(single_commit_options.keys())[-1] if single_commit_options else None,
            full_width=True,
        )

    single_commit_selector = create_single_commit_selector()
    single_commit_selector
    return (single_commit_selector,)


@app.cell(hide_code=True)
def _(Path, commits_folder_input, mo, single_commit_selector):
    def get_commit_message():
        if not single_commit_selector.value:
            return mo.md("_No commit selected_")

        commit_folder = single_commit_selector.value
        commit_path = Path(commits_folder_input.value) / commit_folder
        commit_message_file = commit_path / "commit_message.txt"

        if not commit_message_file.exists():
            return mo.md("_commit_message.txt not found_")

        message = commit_message_file.read_text()

        return mo.ui.text_area(
            value=message,
            label="Commit Message",
            full_width=True,
            rows=10,
            disabled=True,
        )

    get_commit_message()
    return


if __name__ == "__main__":
    app.run()
