"""Worker entry point. Production deployments can replace this loop with Celery/RQ consumers.
The API keeps job execution idempotent through JobRun.input_hash.
"""
import time
from app.db.database import Base, engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Jal-Drishti worker ready; queue adapter can be attached here.")
    while True:
        time.sleep(30)
