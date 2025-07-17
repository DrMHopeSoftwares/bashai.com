#!/usr/bin/env python3
"""
Auto Task Git Integration
Automatically pushes to git when tasks are completed using the existing auto_git_push.py
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Any
from auto_git_push import auto_git_push

class AutoTaskGitIntegration:
    """Handles automatic git pushing when tasks are completed"""
    
    def __init__(self):
        self.base_path = "/Users/murali/bhashai.com 15th Jul/bashai.com"
        self.todo_state_file = os.path.join(self.base_path, ".todo_state.json")
        self.last_completed_tasks = self.load_last_completed_tasks()
        
    def load_last_completed_tasks(self) -> List[str]:
        """Load the list of previously completed tasks"""
        try:
            if os.path.exists(self.todo_state_file):
                with open(self.todo_state_file, 'r') as f:
                    data = json.load(f)
                    return data.get('completed_tasks', [])
        except Exception as e:
            print(f"Warning: Could not load todo state: {e}")
        return []
    
    def save_completed_tasks(self, completed_tasks: List[str]):
        """Save the list of completed tasks"""
        try:
            data = {
                'completed_tasks': completed_tasks,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.todo_state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save todo state: {e}")
    
    def detect_newly_completed_tasks(self, current_todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect tasks that have been newly completed since last check"""
        newly_completed = []
        current_completed_ids = []
        
        for todo in current_todos:
            if todo.get('status') == 'completed':
                task_id = todo.get('id')
                current_completed_ids.append(task_id)
                
                # Check if this task was not completed before
                if task_id not in self.last_completed_tasks:
                    newly_completed.append(todo)
        
        return newly_completed, current_completed_ids
    
    def generate_commit_message(self, completed_tasks: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive commit message for completed tasks"""
        
        if len(completed_tasks) == 1:
            task = completed_tasks[0]
            priority = task.get('priority', 'medium').upper()
            return f"✅ {priority}: {task.get('content', 'Task completed')}"
        else:
            # Multiple tasks completed
            high_priority = [t for t in completed_tasks if t.get('priority') == 'high']
            medium_priority = [t for t in completed_tasks if t.get('priority') == 'medium']
            low_priority = [t for t in completed_tasks if t.get('priority') == 'low']
            
            message = f"✅ Completed {len(completed_tasks)} tasks"
            
            details = []
            if high_priority:
                details.append(f"🔥 {len(high_priority)} high priority tasks")
            if medium_priority:
                details.append(f"⚡ {len(medium_priority)} medium priority tasks")
            if low_priority:
                details.append(f"📝 {len(low_priority)} low priority tasks")
            
            if details:
                message += f" ({', '.join(details)})"
            
            return message
    
    def generate_detailed_changes(self, completed_tasks: List[Dict[str, Any]]) -> List[str]:
        """Generate detailed list of changes for the commit"""
        
        changes = []
        for task in completed_tasks:
            content = task.get('content', 'Task completed')
            priority = task.get('priority', 'medium')
            priority_icon = {'high': '🔥', 'medium': '⚡', 'low': '📝'}.get(priority, '📝')
            changes.append(f"{priority_icon} {content}")
        
        # Add additional context
        changes.append("")
        changes.append("🤖 Auto-pushed via task completion system")
        changes.append(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return changes
    
    def auto_push_for_completed_tasks(self, current_todos: List[Dict[str, Any]]) -> bool:
        """Check for completed tasks and auto-push if any are found"""
        
        print("🔍 Checking for newly completed tasks...")
        
        # Detect newly completed tasks
        newly_completed, current_completed_ids = self.detect_newly_completed_tasks(current_todos)
        
        if not newly_completed:
            print("ℹ️  No new tasks completed since last check")
            return True
        
        print(f"🎉 Found {len(newly_completed)} newly completed tasks!")
        for task in newly_completed:
            print(f"   ✅ {task.get('content', 'Unnamed task')}")
        
        # Generate commit message and details
        commit_message = self.generate_commit_message(newly_completed)
        detailed_changes = self.generate_detailed_changes(newly_completed)
        
        print(f"📝 Commit message: {commit_message}")
        
        # Perform auto git push
        success = auto_git_push(commit_message, detailed_changes)
        
        if success:
            # Update our saved state
            self.save_completed_tasks(current_completed_ids)
            print("🎊 Successfully auto-pushed completed tasks to git!")
        else:
            print("❌ Failed to auto-push to git")
        
        return success
    
    def manual_push_with_task_context(self, task_description: str, additional_details: List[str] = None) -> bool:
        """Manually trigger a push with task context"""
        
        detailed_changes = additional_details or []
        detailed_changes.extend([
            "",
            "🤖 Manual push via task completion system",
            f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return auto_git_push(task_description, detailed_changes)

# Integration function that can be called from any script
def check_and_auto_push_tasks(current_todos: List[Dict[str, Any]]) -> bool:
    """
    Check for completed tasks and auto-push to git if any are found
    
    Args:
        current_todos: List of current todo items with status
        
    Returns:
        bool: True if successful or no action needed, False if failed
    """
    integration = AutoTaskGitIntegration()
    return integration.auto_push_for_completed_tasks(current_todos)

def manual_task_push(task_description: str, details: List[str] = None) -> bool:
    """
    Manually trigger a git push with task context
    
    Args:
        task_description: Description of the completed task
        details: Optional list of detailed changes
        
    Returns:
        bool: True if successful, False if failed
    """
    integration = AutoTaskGitIntegration()
    return integration.manual_push_with_task_context(task_description, details)

# Enhanced TodoWrite integration
class AutoGitTodoWriter:
    """Enhanced todo writer that automatically pushes on task completion"""
    
    def __init__(self):
        self.git_integration = AutoTaskGitIntegration()
    
    def update_todos_with_auto_push(self, todos: List[Dict[str, Any]]) -> bool:
        """Update todos and automatically push if tasks are completed"""
        
        # First, check for completed tasks and auto-push
        auto_push_success = self.git_integration.auto_push_for_completed_tasks(todos)
        
        # Always return True for todo updates (don't fail todo updates due to git issues)
        return True
    
    def complete_task_and_push(self, task_id: str, todos: List[Dict[str, Any]], 
                               additional_message: str = None) -> bool:
        """Mark a task as completed and immediately push to git"""
        
        # Find and update the task
        task_found = False
        completed_task = None
        
        for todo in todos:
            if todo.get('id') == task_id:
                todo['status'] = 'completed'
                completed_task = todo
                task_found = True
                break
        
        if not task_found:
            print(f"❌ Task with ID {task_id} not found")
            return False
        
        # Generate commit message
        task_content = completed_task.get('content', 'Task completed')
        priority = completed_task.get('priority', 'medium').upper()
        
        commit_message = f"✅ {priority}: {task_content}"
        if additional_message:
            commit_message += f" - {additional_message}"
        
        # Push to git
        details = [
            f"🎯 Task: {task_content}",
            f"📊 Priority: {priority}",
            f"🔄 Status: Completed"
        ]
        
        if additional_message:
            details.append(f"💬 Note: {additional_message}")
        
        success = self.git_integration.manual_push_with_task_context(commit_message, details)
        
        if success:
            # Update saved state
            current_completed_ids = [t.get('id') for t in todos if t.get('status') == 'completed']
            self.git_integration.save_completed_tasks(current_completed_ids)
        
        return success

# Command line interface
def main():
    """Command line interface for auto git integration"""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python auto_task_git_integration.py check [todos.json]")
        print("  python auto_task_git_integration.py push 'task description' [detail1] [detail2] ...")
        print("  python auto_task_git_integration.py complete [task_id] [todos.json] [message]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        # Check for completed tasks and auto-push
        todos_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if todos_file and os.path.exists(todos_file):
            with open(todos_file, 'r') as f:
                todos = json.load(f)
        else:
            # Default empty todos for testing
            todos = []
        
        success = check_and_auto_push_tasks(todos)
        sys.exit(0 if success else 1)
        
    elif command == "push":
        # Manual push with task context
        if len(sys.argv) < 3:
            print("Error: Task description required for push command")
            sys.exit(1)
        
        task_description = sys.argv[2]
        details = sys.argv[3:] if len(sys.argv) > 3 else None
        
        success = manual_task_push(task_description, details)
        sys.exit(0 if success else 1)
        
    elif command == "complete":
        # Complete a specific task and push
        if len(sys.argv) < 4:
            print("Error: Task ID and todos file required for complete command")
            sys.exit(1)
        
        task_id = sys.argv[2]
        todos_file = sys.argv[3]
        additional_message = sys.argv[4] if len(sys.argv) > 4 else None
        
        if not os.path.exists(todos_file):
            print(f"Error: Todos file {todos_file} not found")
            sys.exit(1)
        
        with open(todos_file, 'r') as f:
            todos = json.load(f)
        
        writer = AutoGitTodoWriter()
        success = writer.complete_task_and_push(task_id, todos, additional_message)
        
        # Save updated todos
        with open(todos_file, 'w') as f:
            json.dump(todos, f, indent=2)
        
        sys.exit(0 if success else 1)
    
    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()