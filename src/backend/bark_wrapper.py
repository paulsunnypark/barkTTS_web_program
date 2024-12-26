from bark import SAMPLE_RATE, generate_audio, preload_models
import numpy as np
import torch
import gc

class BarkTTS:
    def __init__(self):
        # GPU 메모리 효율적 사용을 위한 설정
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # CUDA 설정 추가
        if self.device == "cuda":
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.cuda.empty_cache()
        
        # 모델 미리 로드
        try:
            preload_models()
            gc.collect()
        except Exception as e:
            raise Exception(f"모델 로드 실패: {str(e)}")
            
        self.available_speakers = {
            "korean_male_1": "v2/ko_speaker_0",
            "korean_male_2": "v2/ko_speaker_1",
            "korean_female_1": "v2/ko_speaker_2",
            "korean_female_2": "v2/ko_speaker_3"
        }
    
    def generate_speech(self, text: str, speaker: str, temperature: float = 0.7):
        try:
            # 텍스트 전처리 강화
            text = text.strip()
            if not text:
                raise ValueError("Empty text input")
            
            # 최대 텍스트 길이 제한
            max_text_length = 256
            if len(text) > max_text_length:
                text = text[:max_text_length]
                
            # GPU 메모리 초기화
            if self.device == "cuda":
                with torch.cuda.device(self.device):
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
            
            speaker_id = self.available_speakers.get(speaker)
            if not speaker_id:
                raise ValueError("Invalid speaker selection")
                
            # 음성 생성
            with torch.inference_mode(), torch.no_grad():
                audio_array = generate_audio(
                    text,
                    history_prompt=speaker_id,
                    text_temp=temperature
                )
            
            return audio_array, SAMPLE_RATE
            
        except Exception as e:
            # 오류 발생 시 메모리 정리
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            gc.collect()
            raise Exception(f"음성 생성 중 오류 발생: {str(e)}") 