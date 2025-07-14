#!/usr/bin/env python3
"""
Auto Git Push Helper
Automatically commits and pushes changes when tasks are completed
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()

def auto_git_push(task_description, detailed_changes=None):
    """
    Automatically add, commit, and push changes to git
    
    Args:
        task_description (str): Brief description of the completed task
        detailed_changes (list): Optional list of detailed changes made
    """
    
    # Get current working directory
    cwd = os.getcwd()
    if not cwd.endswith('bashai.com'):
        cwd = os.path.join(cwd, 'bashai.com')
    
    print(f"🔄 Auto Git Push: {task_description}")
    
    # Check git status
    status_output, error = run_command("git status --porcelain", cwd)
    if error:
        print(f"❌ Git status error: {error}")
        return False
    
    if not status_output:
        print("ℹ️  No changes to commit")
        return True
    
    # Add all changes
    print("📁 Adding changes...")
    _, error = run_command("git add .", cwd)
    if error:
        print(f"❌ Git add error: {error}")
        return False
    
    # Create commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"{task_description}\n\nCompleted: {timestamp}"
    
    if detailed_changes:
        commit_message += "\n\nChanges made:"
        for change in detailed_changes:
            commit_message += f"\n• {change}"
    
    # Commit changes
    print("💾 Committing changes...")
    commit_cmd = f'git commit -m "{commit_message}"'
    _, error = run_command(commit_cmd, cwd)
    if error:
        print(f"❌ Git commit error: {error}")
        return False
    
    # Push to origin
    print("🚀 Pushing to origin...")
    _, error = run_command("git push origin main", cwd)
    if error:
        print(f"❌ Git push error: {error}")
        return False
    
    print("✅ Successfully pushed changes to git!")
    return True

def quick_push(message):
    """Quick push with a simple message"""
    return auto_git_push(message)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_git_push.py 'commit message'")
        sys.exit(1)
    
    message = sys.argv[1]
    detailed_changes = sys.argv[2:] if len(sys.argv) > 2 else None
    
    success = auto_git_push(message, detailed_changes)
    sys.exit(0 if success else 1)
