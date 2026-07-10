import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_integration():
    print("Testing Backend Integration...")

    # 1. Create a Project
    print("1. Creating Project...")
    resp = requests.post(f"{BASE_URL}/projects", json={
        "name": "Integration Test Project",
        "domain": "Biomedical NLP",
        "description": "A test project for integration.",
        "subject_scope": ["LLMs", "Bioinformatics"]
    })
    
    if resp.status_code != 201:
        print(f"Failed to create project: {resp.text}")
        sys.exit(1)
        
    project = resp.json()
    project_id = project["id"]
    print(f"Project created with ID: {project_id}")

    # 2. Add an Idea
    print("2. Adding Idea...")
    resp = requests.post(f"{BASE_URL}/ideas?project_id={project_id}", json={
        "text": "Use LLMs to extract gene interactions",
        "flexibility": 0.5
    })
    
    if resp.status_code != 201:
        print(f"Failed to add idea: {resp.text}")
        sys.exit(1)
        
    idea = resp.json()
    idea_id = idea["id"]
    print(f"Idea created with ID: {idea_id}")

    # 3. Start a Research Run
    print("3. Starting Research Run...")
    resp = requests.post(f"{BASE_URL}/runs?project_id={project_id}", json={
        "idea_id": idea_id,
        "run_type": "user_directed",
        "max_minutes": 5,
        "max_sources": 5
    })
    
    if resp.status_code != 201:
        print(f"Failed to start run: {resp.text}")
        sys.exit(1)
        
    run = resp.json()
    run_id = run["id"]
    print(f"Run started with ID: {run_id}")

    # 4. Check Run Status
    print("4. Checking Run Status...")
    time.sleep(2)
    resp = requests.get(f"{BASE_URL}/runs/{run_id}")
    
    if resp.status_code != 200:
        print(f"Failed to get run status: {resp.text}")
        sys.exit(1)
        
    run_status = resp.json()
    print(f"Run State: {run_status.get('state')}")
    print("Integration test complete.")

if __name__ == "__main__":
    test_integration()
