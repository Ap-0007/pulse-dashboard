import os
import subprocess
import re
import json
import time
from datetime import datetime, timedelta

# Configuration
WORKSPACE_ROOT = "/Users/amogh/Downloads/anti/side_pro"
EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', '__pycache__', '.next', '.vercel', 'static'}
TODO_PATTERNS = [
    re.compile(r'#\s*TODO[:\s]*(.*)', re.IGNORECASE),
    re.compile(r'//\s*TODO[:\s]*(.*)', re.IGNORECASE),
    re.compile(r'#\s*FIXME[:\s]*(.*)', re.IGNORECASE),
    re.compile(r'//\s*FIXME[:\s]*(.*)', re.IGNORECASE),
    re.compile(r'\[\s\]\s*(.*)') # Markdown tasks
]

def get_git_stats(repo_path):
    """Extracts commit frequency and last activity."""
    try:
        # Get count of commits in the last 30 days
        since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cmd = f"git -C {repo_path} log --since='{since}' --oneline"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        commits = result.stdout.strip().split('\n')
        count = len(commits) if commits[0] != "" else 0

        # Get last commit date
        cmd_last = f"git -C {repo_path} log -1 --format='%ai'"
        result_last = subprocess.run(cmd_last, shell=True, capture_output=True, text=True)
        last_date = result_last.stdout.strip()

        return {"recent_commits": count, "last_activity": last_date}
    except Exception:
        return {"recent_commits": 0, "last_activity": "Unknown"}

def extract_todos(project_path):
    """Scans project files for TODO/FIXME comments."""
    todos = []
    for root, dirs, files in os.walk(project_path):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.tsx', '.sh', '.md', '.html', '.css')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            for pattern in TODO_PATTERNS:
                                match = pattern.search(line)
                                if match:
                                    todos.append({
                                        "file": os.path.relpath(file_path, project_path),
                                        "line": i,
                                        "text": match.group(1).strip()
                                    })
                except Exception:
                    continue
    return todos

def analyze_workspace():
    """Main orchestrator for workspace pulse."""
    results = []
    for item in os.listdir(WORKSPACE_ROOT):
        path = os.path.join(WORKSPACE_ROOT, item)
        if os.path.isdir(path) and item not in EXCLUDE_DIRS:
            # Check if it's a project (has git or build files)
            is_proj = any(os.path.exists(os.path.join(path, f)) for f in ['.git', 'package.json', 'pyproject.toml', 'requirements.txt'])
            
            if is_proj:
                print(f"Analyzing {item}...")
                stats = get_git_stats(path)
                todos = extract_todos(path)
                
                # Heuristic Vitality Score
                # 100 base, -10 per day of inactivity, +5 per recent commit
                vitality = 100
                if stats['last_activity'] != "Unknown":
                    last_dt = datetime.fromisoformat(stats['last_activity'].split(' ')[0])
                    days_idle = (datetime.now() - last_dt).days
                    vitality = max(0, min(100, 100 - (days_idle * 2) + (stats['recent_commits'] * 5)))

                results.append({
                    "name": item,
                    "vitality": vitality,
                    "stats": stats,
                    "todo_count": len(todos),
                    "todos": todos[:20] # Limit for UI brevity
                })
    
    return results

if __name__ == "__main__":
    report = analyze_workspace()
    with open("pulse_data.json", "w") as f:
        json.dump(report, f, indent=4)
    print(f"Pulse generated: {len(report)} projects analyzed.")
