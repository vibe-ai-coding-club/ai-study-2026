import base64
import os
from openai import OpenAI
from dotenv import load_dotenv
import pygame

# .env 파일에서 API 키 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text, output_file="speech.mp3"):
    """
    텍스트를 음성으로 변환하고 파일로 저장합니다.
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # alloy, echo, fable, onyx, nova, shimmer 중 선택 가능
            input=text
        )
        
        # 음성 파일 저장
        response.stream_to_file(output_file)
        return output_file
        
    except Exception as e:
        print(f"TTS 변환 오류: {str(e)}")
        return None

def play_audio(file_path):
    """
    오디오 파일을 재생합니다.
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # 재생이 끝날 때까지 대기
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()
        
    except Exception as e:
        print(f"오디오 재생 오류: {str(e)}")

def analyze_image(image_path):
    """
    지정된 이미지 파일을 분석하고 해석을 반환합니다.
    """
    try:
        # 이미지 파일을 base64로 인코딩
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 이미지에 대해 자세히 설명해주세요. 이미지의 내용, 특징, 그리고 흥미로운 점들을 분석해주세요."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # 응답 반환
        return response.choices[0].message.content
        
    except FileNotFoundError:
        return f"오류: {image_path} 파일을 찾을 수 없습니다."
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

if __name__ == "__main__":
    # 이미지 분석 실행
    result = analyze_image("cat.jpeg")
    print("=== 이미지 분석 결과 ===")
    print(result)
    
    # TTS로 음성 변환
    print("\n=== 음성 변환 중 ===")
    audio_file = text_to_speech(result, "cat_analysis.mp3")
    
    if audio_file:
        print(f"음성 파일 저장됨: {audio_file}")
        
        # 음성 재생
        print("=== 음성 재생 중 ===")
        play_audio(audio_file)
        print("재생 완료")
    else:
        print("음성 변환 실패")
