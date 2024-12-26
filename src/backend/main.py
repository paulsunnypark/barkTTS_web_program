from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np
import soundfile as sf
import os
from src.backend.bark_wrapper import BarkTTS
import logging
import torch
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 정적 파일 제공을 위한 설정
os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# GPU 메모리 관리 설정
os.environ["CUDA_VISIBLE_DEVICES"]="0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"  # 메모리 단편화 방지

# GPU 메모리 설정 함수
def setup_gpu():
    if torch.cuda.is_available():
        # GPU 메모리 캐시 초기화
        torch.cuda.empty_cache()
        # 메모리 할당자 설정
        torch.cuda.set_per_process_memory_fraction(0.75)  # 75%로 증가
        return True
    return False

# FastAPI 앱 시작 전 GPU 설정
setup_gpu()

# BarkTTS 인스턴스를 전역 변수로 선언
bark_tts = None

@app.on_event("startup")
async def startup_event():
    global bark_tts
    logger.info("Starting to load Bark TTS model...")
    try:
        # GPU 메모리 상태 로깅
        if torch.cuda.is_available():
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            logger.info(f"Available Memory: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        
        bark_tts = BarkTTS()
        logger.info("Bark TTS model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load Bark TTS model: {str(e)}")
        raise e

# CORS 설정을 더 구체적으로
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]  # 다운로드를 위해 추가
)

class TTSRequest(BaseModel):
    text: str
    speaker: str
    temperature: float = 0.7

@app.post("/generate-speech")
async def generate_speech(request: TTSRequest):
    if bark_tts is None:
        raise HTTPException(status_code=503, detail="TTS model is not ready yet")
        
    try:
        # 이전 파일 정리
        output_dir = "static/audio"
        for file in os.listdir(output_dir):
            if file.startswith("output_") and file.endswith(".wav"):
                try:
                    os.remove(os.path.join(output_dir, file))
                except Exception as e:
                    logger.warning(f"Failed to remove old file {file}: {str(e)}")

        logger.info(f"Generating speech for text: {request.text[:50]}...")
        
        # 입력 텍스트 검증
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Empty text input")
            
        audio_array, sample_rate = bark_tts.generate_speech(
            request.text,
            request.speaker,
            request.temperature
        )
        
        # 타임스탬프를 포함한 고유한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_{timestamp}.wav"
        output_path = f"static/audio/{filename}"
        
        # 파일 저장
        sf.write(output_path, audio_array, sample_rate)
        logger.info(f"Speech generated successfully: {output_path}")
        
        # 메모리 정리
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        # FileResponse로 직접 파일 반환
        return FileResponse(
            output_path,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        # 오류 발생 시 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/speakers")
async def get_speakers():
    if bark_tts is None:
        raise HTTPException(status_code=503, detail="TTS model is not ready yet")
    return {"speakers": list(bark_tts.available_speakers.keys())}

@app.get("/status")
async def get_status():
    return {"status": "ready" if bark_tts is not None else "loading"}