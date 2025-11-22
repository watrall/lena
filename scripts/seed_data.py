import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Configuration
COURSE_ID = "anth101"
STORAGE_DIR = Path("storage")
INTERACTIONS_FILE = STORAGE_DIR / "interactions.jsonl"
ESCALATIONS_FILE = STORAGE_DIR / "escalations.jsonl"

def ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def generate_interactions(count=50):
    interactions = []
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    questions = [
        "What is cultural relativism?",
        "Explain the difference between emic and etic.",
        "When is the midterm?",
        "How do I cite sources?",
        "What is ethnography?"
    ]

    for _ in range(count):
        ts = start_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        q = random.choice(questions)
        
        # Ask event
        interactions.append({
            "type": "ask",
            "question_id": uuid.uuid4().hex,
            "timestamp": ts.isoformat().replace("+00:00", "Z"),
            "confidence": random.uniform(0.7, 0.99),
            "course_id": COURSE_ID,
            "question": q
        })
        
        # Feedback event (sometimes)
        if random.random() > 0.3:
            interactions.append({
                "type": "feedback",
                "question_id": interactions[-1]["question_id"],
                "timestamp": (ts + timedelta(seconds=random.randint(10, 600))).isoformat().replace("+00:00", "Z"),
                "helpful": random.choice([True, True, True, False]),
                "course_id": COURSE_ID,
                "question": q
            })

    return interactions

def generate_escalations(count=5):
    escalations = []
    for _ in range(count):
        escalations.append({
            "id": uuid.uuid4().hex,
            "question_id": uuid.uuid4().hex,
            "question": "I don't understand the grading criteria.",
            "student": f"Student {random.randint(1, 100)}",
            "student_email": f"student{random.randint(1, 100)}@example.com",
            "course_id": COURSE_ID,
            "submitted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "delivered": False
        })
    return escalations

def seed():
    ensure_storage()
    
    print(f"Seeding {INTERACTIONS_FILE}...")
    interactions = generate_interactions()
    with open(INTERACTIONS_FILE, "a") as f:
        for record in interactions:
            f.write(json.dumps(record) + "\n")
            
    print(f"Seeding {ESCALATIONS_FILE}...")
    escalations = generate_escalations()
    with open(ESCALATIONS_FILE, "a") as f:
        for record in escalations:
            f.write(json.dumps(record) + "\n")
            
    print("Done.")

if __name__ == "__main__":
    seed()
