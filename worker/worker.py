import os
import time
import json
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import redis

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/music_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    status = Column(String)
    vocal_url = Column(String)
    sheet_music_url = Column(String)

# Подключение к Redis
redis_client = redis.Redis.from_url(REDIS_URL)

def process_ai_task(task):
    db = SessionLocal()
    track_id = task["track_id"]
    
    # Получаем запись из БД
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        db.close()
        return

    print(f"[ИИ ОРКЕСТРАТОР] Начало обработки трека #{track_id}: '{track.title}'")
    
    try:
        # Имитируем работу тяжелых ML-моделей (Audio Separation и Note Transcription)
        print("[ИИ ОРКЕСТРАТОР] Шаг 1: Запуск ИИ разделения дорожек (Stems)...")
        time.sleep(5) 
        
        print("[ИИ ОРКЕСТРАТОР] Шаг 2: Запуск ИИ транскрипции в нотный стан...")
        time.sleep(5)
        
        # Обновляем статус в БД и прописываем "ссылки" на результаты (якобы в S3)
        track.vocal_url = f"https://s3.mock-storage.local/vocals/{track_id}_vocals.wav"
        track.sheet_music_url = f"https://s3.mock-storage.local/sheets/{track_id}_sheets.pdf"
        track.status = "Completed"
        
        db.commit()
        print(f"[ИИ ОРКЕСТРАТОР] Успешно завершена обработка трека #{track_id}!")
    except Exception as e:
        print(f"[ИИ ОРКЕСТРАТОР] Ошибка при обработке: {e}")
        track.status = "Failed"
        db.commit()
    finally:
        db.close()

def main():
    print("[ИИ ОРКЕСТРАТОР] Воркер запущен. Ожидание задач в очереди...")
    while True:
        # Читаем задачу из Redis очереди (блокирующий метод blpop)
        task_data = redis_client.blpop("ai_tasks", timeout=5)
        if task_data:
            task_json = task_data[1].decode("utf-8")
            task = json.loads(task_json)
            process_ai_task(task)

if __name__ == "__main__":
    main()