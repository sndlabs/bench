#!/usr/bin/env python3
"""
Check available Korean benchmarks in lm-evaluation-harness
"""

import subprocess
import sys
import json
from pathlib import Path

def check_lm_eval_installed():
    """Check if lm-evaluation-harness is installed."""
    try:
        import lm_eval
        return True
    except ImportError:
        return False

def get_available_tasks():
    """Get list of available tasks from lm-eval."""
    try:
        result = subprocess.run(
            ["lm_eval", "--tasks", "list"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            print(f"Error getting task list: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error running lm_eval: {e}")
        return []

def filter_korean_tasks(tasks):
    """Filter tasks that are likely Korean benchmarks."""
    korean_keywords = [
        'ko', 'korean', 'klue', 'kmmlu', 'kobest', 'nsmc', 
        'hate_speech_ko', 'pawsx_ko', 'kor_', 'k_'
    ]
    
    korean_tasks = []
    for task in tasks:
        task_lower = task.lower()
        if any(keyword in task_lower for keyword in korean_keywords):
            korean_tasks.append(task)
    
    return sorted(korean_tasks)

def categorize_korean_tasks(tasks):
    """Categorize Korean tasks by type."""
    categories = {
        'KoBEST': [],
        'KMMLU': [],
        'KLUE': [],
        'Hate Speech': [],
        'Other': []
    }
    
    for task in tasks:
        task_lower = task.lower()
        if 'kobest' in task_lower:
            categories['KoBEST'].append(task)
        elif 'kmmlu' in task_lower:
            categories['KMMLU'].append(task)
        elif 'klue' in task_lower:
            categories['KLUE'].append(task)
        elif 'hate' in task_lower and ('ko' in task_lower or 'speech' in task_lower):
            categories['Hate Speech'].append(task)
        else:
            categories['Other'].append(task)
    
    return categories

def main():
    print("🔍 Checking Korean benchmark availability in lm-evaluation-harness...\n")
    
    # Check if lm-eval is installed
    if not check_lm_eval_installed():
        print("❌ lm-evaluation-harness is not installed!")
        print("\nTo install, run:")
        print("  pip install lm-eval")
        print("\nOr in the virtual environment:")
        print("  source venv/bin/activate")
        print("  pip install lm-eval")
        sys.exit(1)
    
    print("✅ lm-evaluation-harness is installed\n")
    
    # Get available tasks
    print("📋 Fetching available tasks...")
    all_tasks = get_available_tasks()
    
    if not all_tasks:
        print("❌ Could not retrieve task list")
        sys.exit(1)
    
    print(f"Found {len(all_tasks)} total tasks\n")
    
    # Filter Korean tasks
    korean_tasks = filter_korean_tasks(all_tasks)
    print(f"🇰🇷 Found {len(korean_tasks)} Korean benchmark tasks:\n")
    
    if not korean_tasks:
        print("No Korean tasks found. This might mean:")
        print("- Korean benchmarks are not included in your lm-eval version")
        print("- Task names don't match expected patterns")
        print("\nTry updating lm-eval: pip install --upgrade lm-eval")
        sys.exit(0)
    
    # Categorize and display
    categories = categorize_korean_tasks(korean_tasks)
    
    for category, tasks in categories.items():
        if tasks:
            print(f"\n{category} ({len(tasks)} tasks):")
            print("-" * 40)
            for task in sorted(tasks):
                print(f"  • {task}")
    
    # Generate example command
    print("\n\n💡 Example Commands:")
    print("-" * 50)
    
    # Basic example
    if categories['KoBEST']:
        kobest_tasks = ','.join(categories['KoBEST'][:3])
        print(f"\n# Run KoBEST benchmarks:")
        print(f"./run-benchmark.sh --model gpt2 --tasks {kobest_tasks}")
    
    if categories['KMMLU']:
        print(f"\n# Run KMMLU benchmark:")
        print(f"./run-benchmark.sh --model gpt2 --tasks {categories['KMMLU'][0]}")
    
    # Interactive mode
    print("\n# Or use interactive mode to select from menu:")
    print("./run-benchmark.sh")
    
    # Save task list
    output_file = Path(__file__).parent / "korean_tasks.json"
    task_data = {
        'total_tasks': len(all_tasks),
        'korean_tasks': len(korean_tasks),
        'categories': categories,
        'all_korean_tasks': korean_tasks
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n📁 Full task list saved to: {output_file}")

if __name__ == "__main__":
    main()