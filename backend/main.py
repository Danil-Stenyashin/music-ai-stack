import os
import json
from fastapi import FastAPI, UploadFile, File, Form
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import redis

# Настройки баз данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/music_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# SQLAlchemy Инициализация
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    status = Column(String, default="Processing")  # Processing, Completed, Failed
    vocal_url = Column(String, nullable=True)
    sheet_music_url = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# Redis соединение
redis_client = redis.Redis.from_url(REDIS_URL)

app = FastAPI()

@app.get("/tracks")
def get_tracks():
    db = SessionLocal()
    tracks = db.query(Track).order_by(Track.id.desc()).all()
    db.close()
    return tracks

@app.post("/upload")
def upload_track(title: str = Form(...), file: UploadFile = File(...)):
    db = SessionLocal()
    
    # 1. Создаем запись в PostgreSQL со статусом "Processing" (создание записи по архитектурной схеме)
    new_track = Track(title=title, status="Processing")
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    
    # Имитация сохранения файла на S3 (сохранение в локальную папку контейнера)
    file_path = f"/tmp/{new_track.id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
        
    # 2. Отправляем ID задачи в очередь Redis (отправка события по архитектурной схеме)
    task_payload = {
        "track_id": new_track.id,
        "file_path": file_path
    }
    redis_client.rpush("ai_tasks", json.dumps(task_payload))
    
    db.close()
    return {"status": "queued", "track_id": new_track.id}