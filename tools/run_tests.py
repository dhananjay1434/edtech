import argparse
import sys
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Run CDE tests")
    parser.add_argument("--agent", choices=["alpha", "beta", "gamma", "merger"], required=True)
    parser.add_argument("--tier", choices=["unit", "contract", "integration", "replay", "live", "gate"], required=True)
    
    # parse_known_args to capture pytest args
    args, pytest_args = parser.parse_known_args()
    
    # if '--' in args, strip it
    if '--' in pytest_args:
        pytest_args.remove('--')
        
    print(f"Running {args.tier} tests for {args.agent} agent...")
    
    # A fake test runner for B0 baseline, just run pytest
    cmd = [sys.executable, "-m", "pytest"] + pytest_args
    print("Executing:", " ".join(cmd))
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
