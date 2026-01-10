#!/usr/bin/env python3
"""
Git Commit Extractor
Clones a git repository and extracts each commit into its own folder.
"""

import subprocess
import os
import sys
import shutil
import argparse
from pathlib import Path


def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return output."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {result.stderr}")
    return result.stdout.strip()


def get_all_commits(repo_path: str) -> list[tuple[str, str, str]]:
    """Get all commits (full_hash, full_message, date) in chronological order."""
    # Use %x00 as delimiter to handle multi-line commit messages
    output = run_git(
        ["log", "--reverse", "--format=%H%x00%B%x00%cI%x00"],
        cwd=repo_path
    )
    commits = []
    parts = output.split("\x00")
    i = 0
    while i < len(parts) - 2:
        full_hash = parts[i].strip()
        message = parts[i + 1].strip() if i + 1 < len(parts) else ""
        date = parts[i + 2].strip() if i + 2 < len(parts) else ""
        if full_hash:
            commits.append((full_hash, message, date))
        i += 3
    return commits


def extract_commit(repo_path: str, commit_hash: str, output_dir: str):
    """Extract a specific commit's files to a directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Use git archive to extract the commit contents
    archive_cmd = subprocess.Popen(
        ["git", "archive", "--format=tar", commit_hash],
        cwd=repo_path,
        stdout=subprocess.PIPE
    )
    
    # Extract the tar archive
    subprocess.run(
        ["tar", "-xf", "-"],
        cwd=output_dir,
        stdin=archive_cmd.stdout,
        check=True
    )
    archive_cmd.wait()


def main():
    parser = argparse.ArgumentParser(
        description="Clone a git repo and extract each commit into its own folder."
    )
    parser.add_argument("url", help="Git repository URL (used for cloning)")
    parser.add_argument("destination", help="Destination folder for extracted commits")
    parser.add_argument(
        "--repo-url",
        help="Base URL for commit links (e.g., https://github.com/user/repo). Defaults to clone URL without .git suffix."
    )
    parser.add_argument(
        "--keep-clone",
        action="store_true",
        help="Keep the cloned repository (otherwise deleted after extraction)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing commit folders instead of skipping them"
    )
    
    args = parser.parse_args()
    
    destination = Path(args.destination).resolve()
    temp_clone = destination / ".temp_clone"
    
    # Determine base URL for commit links
    repo_url = args.repo_url if args.repo_url else args.url.rstrip("/").removesuffix(".git")
    
    # Create destination directory
    destination.mkdir(parents=True, exist_ok=True)
    
    print(f"Cloning {args.url}...")
    try:
        run_git(["clone", args.url, str(temp_clone)])
    except RuntimeError as e:
        print(f"Error cloning repository: {e}")
        sys.exit(1)
    
    print("Getting commit history...")
    commits = get_all_commits(str(temp_clone))
    print(f"Found {len(commits)} commits")
    
    # Extract each commit
    skipped = 0
    extracted = 0
    for i, (full_hash, message, datetime_str) in enumerate(commits, 1):
        short_hash = full_hash[:6]

        # Parse datetime and format as yyyy_mm_dd_HHMMSS
        dt_parts = datetime_str.split('T')
        date_part = dt_parts[0].replace("-", "_")  # 2024_01_15
        time_part = dt_parts[1].split('-')[0].split('+')[0].replace(":", "")  # 143045        

        folder_name = f"{date_part}_{time_part}_{short_hash}"
        output_dir = destination / folder_name
        
        subject = message.split("\n")[0] if message else "(no message)"
        
        # Skip if folder already exists (unless overwrite is set)
        if output_dir.exists():
            if args.overwrite:
                shutil.rmtree(output_dir)
            else:
                skipped += 1
                continue
        
        print(f"[{i}/{len(commits)}] Extracting {short_hash}: {subject[:50]}...")
        
        try:
            extract_commit(str(temp_clone), full_hash, str(output_dir))
            
            # Write commit_message.txt with URL and full message
            commit_url = f"{repo_url}/commit/{full_hash}"
            info_file = output_dir / "commit_message.txt"
            info_file.write_text(f"{commit_url}\n\n{message}\n")
            extracted += 1
        except Exception as e:
            print(f"  Warning: Failed to extract commit {short_hash}: {e}")
    
    # Cleanup
    if not args.keep_clone:
        print("Cleaning up temporary clone...")
        shutil.rmtree(temp_clone)
    
    print(f"\nDone! Extracted {extracted} new commits, skipped {skipped} existing. Total: {len(commits)}")


if __name__ == "__main__":
    main()