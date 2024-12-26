document.addEventListener('DOMContentLoaded', async () => {
    const speakerSelect = document.getElementById('speaker');
    const textArea = document.getElementById('text');
    const temperatureInput = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    const generateBtn = document.getElementById('generateBtn');
    const audioContainer = document.getElementById('audioContainer');
    const audioPlayer = document.getElementById('audioPlayer');
    const loading = document.getElementById('loading');

    // 화자 목록 가져오기
    try {
        console.log("화자 목록 가져오기 시작...");
        const response = await fetch('http://localhost:8000/speakers');
        console.log("서버 응답:", response);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("받은 데이터:", data);
        
        data.speakers.forEach(speaker => {
            const option = document.createElement('option');
            option.value = speaker;
            option.textContent = speaker.replace(/_/g, ' ');
            speakerSelect.appendChild(option);
        });
    } catch (error) {
        console.error('화자 목록을 가져오는데 실패했습니다:', error);
        // 사용자에게 오류 표시
        const errorMsg = document.createElement('div');
        errorMsg.style.color = 'red';
        errorMsg.textContent = '화자 목록을 불러오는데 실패했습니다. 페이지를 새로고침 해주세요.';
        speakerSelect.parentNode.appendChild(errorMsg);
    }

    // 온도 값 표시 업데트
    temperatureInput.addEventListener('input', (e) => {
        temperatureValue.textContent = e.target.value;
    });

    // 음성 생성
    generateBtn.addEventListener('click', async () => {
        const text = textArea.value.trim();
        if (!text) {
            alert('텍스트를 입력해주세요.');
            return;
        }

        loading.style.display = 'block';
        audioContainer.style.display = 'none';
        generateBtn.disabled = true;

        try {
            const response = await fetch('http://localhost:8000/generate-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    speaker: speakerSelect.value,
                    temperature: parseFloat(temperatureInput.value)
                })
            });

            if (!response.ok) {
                throw new Error('음성 생성 실패');
            }

            // Blob으로 응답 받기
            const blob = await response.blob();
            const audioUrl = URL.createObjectURL(blob);

            // 이전 다운로드 링크가 있다면 제거
            const oldDownloadLink = audioContainer.querySelector('.download-link');
            if (oldDownloadLink) {
                oldDownloadLink.remove();
            }

            // 오디오 플레이어 설정
            audioPlayer.src = audioUrl;
            audioContainer.style.display = 'block';
            
            // 파일명 가져오기
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition
                ? contentDisposition.split('filename=')[1].replace(/['"]/g, '')
                : 'generated_audio.wav';

            // 다운로드 링크 추가
            const downloadLink = document.createElement('a');
            downloadLink.href = audioUrl;
            downloadLink.download = filename;
            downloadLink.textContent = '음성 파일 다운로드';
            downloadLink.className = 'download-link';
            audioContainer.appendChild(downloadLink);

            // 오디오 플레이어 로드
            audioPlayer.load();
            
            // 메모리 정리를 위한 이벤트 리스너
            audioPlayer.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };

        } catch (error) {
            alert('음성 생성 중 오류가 발생했습니다: ' + error.message);
        } finally {
            loading.style.display = 'none';
            generateBtn.disabled = false;
        }
    });
}); 