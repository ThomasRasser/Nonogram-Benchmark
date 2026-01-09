import marimo

__generated_with = "0.19.0"
app = marimo.App(width="medium")


@app.cell
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


@app.cell
def _():
    import subprocess
    import sqlite3
    import time
    import re
    from pathlib import Path
    from datetime import datetime
    import pandas as pd
    import plotly.express as px
    import matplotlib.pyplot as plt
    return Path, datetime, pd, plt, re, sqlite3, subprocess


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
        value="./puzzles/island_fast",
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
        value=10,
        label="Repetitions per puzzle",
        show_value=True,
    )
    repetitions_input
    return (repetitions_input,)


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
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commit_hash TEXT,
                puzzle_name TEXT,
                puzzle_size TEXT,
                puzzle_density INTEGER,
                puzzle_id INTEGER,
                repetition INTEGER,
                time_ns INTEGER,
                time_ms REAL,
                timestamp TEXT,
                FOREIGN KEY (commit_hash) REFERENCES commits(commit_hash)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_commit ON runs(commit_hash)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_puzzle ON runs(puzzle_name)
        """)
        conn.commit()
        return conn
    return (init_database,)


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
def _(subprocess):
    def run_benchmark(executable: str, puzzle_path: str, repetitions: int = 1) -> list[dict]:
        """Run multiple benchmark repetitions in a single subprocess."""
        import time
    
        results = []
        for _ in range(repetitions):
            start_ns = time.perf_counter_ns()
        
            result = subprocess.run(
                [executable, puzzle_path],
                capture_output=True,
                text=True,
            )
        
            end_ns = time.perf_counter_ns()
        
            if result.returncode != 0:
                results.append({"error": f"Execution failed: {result.stderr}"})
            else:
                elapsed_ns = end_ns - start_ns
                results.append({
                    "time_ns": elapsed_ns,
                    "time_ms": elapsed_ns / 1_000_000,
                })
    
        return results
    return (run_benchmark,)


@app.cell(hide_code=True)
def _(Path, check_commit_folder, commits_folder_input, mo, parse_commit_info):
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
    commit_options = {
        f"{c['folder']} {'🟩' if c['valid'] else '🟥'}": c['folder']
        for c in available_commits
    }

    commit_selector = mo.ui.multiselect(
        options=commit_options,
        label="Select Commits to Benchmark",
        value=[list(commit_options.keys())[-1]] if commit_options else [],
        full_width=True,
    )

    mo.md("## Select Commits\n\n🟩 Valid  🟥 Missing files") if available_commits else mo.md("## Select Commits\n\n⚠️ No commits found.")
    return (commit_selector,)


@app.cell
def _(commit_selector):
    commit_selector
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


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Run Benchmark
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Summary
    """)
    return


@app.cell
def _(commit_selector):
    commit_selector.value
    return


@app.cell
def _(filtered_puzzles):
    filtered_puzzles
    return


@app.cell
def _(commit_selector, filtered_puzzles, mo, repetitions_input):
    _num_runs = len(commit_selector.value) * len(filtered_puzzles) * repetitions_input.value
    run_button = mo.ui.run_button(label=f"Run Benchmark on {_num_runs} runs")
    run_button
    return (run_button,)


@app.cell
def _(
    Path,
    available_puzzles,
    cflags_input,
    check_commit_folder,
    commit_selector,
    commits_folder_input,
    compile_solver,
    compiler_input,
    datetime,
    db_path_input,
    filtered_puzzles,
    init_database,
    ldflags_input,
    parse_commit_info,
    puzzles_folder_input,
    repetitions_input,
    run_benchmark,
    run_button,
):
    DEBUG = True

    benchmark_results = []
    if run_button.value and commit_selector.value and filtered_puzzles:
        import time as bench_time
        total_start = bench_time.perf_counter()
    
        conn = init_database(db_path_input.value)
        commits_path = Path(commits_folder_input.value)
        puzzles_path = Path(puzzles_folder_input.value)
    
        for folder_name in commit_selector.value:
            commit_start = bench_time.perf_counter()
            commit_path = commits_path / folder_name
            is_valid, missing = check_commit_folder(commit_path)
            if not is_valid:
                if DEBUG:
                    print(f"[DEBUG] Skipping {folder_name}: missing {missing}")
                continue
            info = parse_commit_info(commit_path)
            conn.execute("""
                INSERT OR REPLACE INTO commits (commit_hash, commit_date, commit_message, commit_url)
                VALUES (?, ?, ?, ?)
            """, (info["hash"], info["date"], info["message"], info["url"]))
        
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
                continue
        
            executable = str(commit_path / "nonograms")
            runs_to_insert = []
        
            for puzzle_file in filtered_puzzles:
                puzzle_start = bench_time.perf_counter()
                puzzle_path = puzzles_path / puzzle_file
                puzzle_info = next((p for p in available_puzzles if p["file"] == puzzle_file), {})
            
                metrics_list = run_benchmark(executable, str(puzzle_path), repetitions_input.value)
            
                for rep, metrics in enumerate(metrics_list, 1):
                    if "error" in metrics:
                        if DEBUG:
                            print(f"[DEBUG] Error {puzzle_file} rep {rep}: {metrics['error']}")
                        continue
                
                    runs_to_insert.append((
                        info["hash"],
                        puzzle_file,
                        puzzle_info.get("size", "unknown"),
                        puzzle_info.get("density", 0),
                        puzzle_info.get("id", 0),
                        rep,
                        metrics["time_ns"],
                        metrics["time_ms"],
                        datetime.now().isoformat(),
                    ))
                
                    benchmark_results.append({
                        "commit": folder_name,
                        "commit_hash": info["hash"][:8],
                        "puzzle": puzzle_file,
                        "size": puzzle_info.get("size", "unknown"),
                        "density": puzzle_info.get("density", 0),
                        "rep": rep,
                        "time_ms": metrics["time_ms"],
                    })
            
                if DEBUG:
                    print(f"[DEBUG] {puzzle_file} ({repetitions_input.value} reps): {bench_time.perf_counter() - puzzle_start:.2f}s")
        
            db_start = bench_time.perf_counter()
            conn.executemany("""
                INSERT INTO runs (
                    commit_hash, puzzle_name, puzzle_size, puzzle_density, puzzle_id,
                    repetition, time_ns, time_ms, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, runs_to_insert)
            conn.commit()
            if DEBUG:
                print(f"[DEBUG] DB insert ({len(runs_to_insert)} rows): {bench_time.perf_counter() - db_start:.3f}s")
                print(f"[DEBUG] Commit {folder_name} total: {bench_time.perf_counter() - commit_start:.2f}s")
    
        conn.close()
        if DEBUG:
            print(f"[DEBUG] Total: {bench_time.perf_counter() - total_start:.2f}s")
    return (benchmark_results,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Results
    """)
    return


@app.cell
def _(benchmark_results, mo, pd):
    df_benchmark_results = pd.DataFrame(benchmark_results)
    mo.ui.table(df_benchmark_results) if benchmark_results else mo.md("No benchmark results to display.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Historical Data
    """)
    return


@app.cell
def _(benchmark_results, mo, pd, plt):
    if benchmark_results:
        df = pd.DataFrame(benchmark_results)
        avg_time = df.groupby("commit")["time_ms"].mean().reset_index()
        avg_time = avg_time.sort_values("commit")  # sorts chronologically due to date prefix
    
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(len(avg_time)), avg_time["time_ms"], marker="o", linestyle="-")
        ax.set_xticks(range(len(avg_time)))
        ax.set_xticklabels(avg_time["commit"], rotation=45, ha="right")
        ax.set_xlabel("Commit")
        ax.set_ylabel("Avg Time (ms)")
        ax.set_title("Average Execution Time per Commit")
        plt.tight_layout()
        plt.show()
    else:
        mo.md("No historical data to display.")
    return


if __name__ == "__main__":
    app.run()
