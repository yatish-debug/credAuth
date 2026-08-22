import sys
import os

# Add root backend directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.generate_demo_data import generate_synthetic_demo_data

def seed_db():
    print("Initiating SSBT Platform database seed...")
    generate_synthetic_demo_data()

if __name__ == "__main__":
    seed_db()
