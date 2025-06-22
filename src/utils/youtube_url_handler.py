"""
Utilitários para URLs do YouTube - MOEDOR AO VIVO
Normaliza e valida URLs de live e vídeos do YouTube
"""

import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class YouTubeURLHandler:
    """Manipula e normaliza URLs do YouTube"""
    
    @staticmethod
    def normalize_youtube_url(url: str) -> Optional[str]:
        """
        Normaliza URLs do YouTube para formato padrão
        Aceita:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://www.youtube.com/live/VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://m.youtube.com/watch?v=VIDEO_ID
        """
        if not url or not isinstance(url, str):
            return None
            
        url = url.strip()
        
        # Padrões de URL do YouTube
        patterns = [
            # Live URLs
            r'(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})',
            # Watch URLs
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            # Short URLs
            r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
            # Mobile URLs
            r'(?:https?://)?m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            # Embed URLs
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                normalized_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"🔗 URL normalizada: {url} -> {normalized_url}")
                return normalized_url
        
        logger.warning(f"⚠️ URL do YouTube não reconhecida: {url}")
        return None
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extrai o ID do vídeo de uma URL do YouTube"""
        normalized = YouTubeURLHandler.normalize_youtube_url(url)
        if not normalized:
            return None
            
        match = re.search(r'v=([a-zA-Z0-9_-]{11})', normalized)
        return match.group(1) if match else None
    
    @staticmethod
    def is_live_url(url: str) -> bool:
        """Verifica se a URL é de uma live do YouTube"""
        if not url:
            return False
            
        # URLs de live podem ter /live/ ou ser streams ao vivo
        live_patterns = [
            r'youtube\.com/live/',
            r'youtube\.com/watch\?v=.*&live=1',
            r'youtube\.com/watch\?v=.*&t=\d+s.*live'
        ]
        
        for pattern in live_patterns:
            if re.search(pattern, url):
                return True
                
        return False
    
    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        """Valida se a URL é válida do YouTube"""
        return YouTubeURLHandler.normalize_youtube_url(url) is not None
    
    @staticmethod
    def get_live_stream_url(video_id: str) -> str:
        """Gera URL de live stream para um video ID"""
        return f"https://www.youtube.com/watch?v={video_id}"
    
    @staticmethod
    def add_live_parameters(url: str) -> str:
        """Adiciona parâmetros para otimizar live streams"""
        if not url:
            return url
            
        # Adicionar parâmetros para live streams
        separator = "&" if "?" in url else "?"
        live_params = "autoplay=1&mute=1&controls=0&modestbranding=1"
        
        return f"{url}{separator}{live_params}"

def test_youtube_urls():
    """Testa o manipulador de URLs"""
    test_urls = [
        "https://www.youtube.com/live/egUBgqdvHb4?si=aJ0Z8l1bPD0TLrzC",
        "https://www.youtube.com/live/egUBgqdvHb4",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "invalid_url"
    ]
    
    handler = YouTubeURLHandler()
    
    print("🧪 Testando URLs do YouTube:")
    for url in test_urls:
        normalized = handler.normalize_youtube_url(url)
        video_id = handler.extract_video_id(url)
        is_live = handler.is_live_url(url)
        is_valid = handler.validate_youtube_url(url)
        
        print(f"URL: {url}")
        print(f"  Normalizada: {normalized}")
        print(f"  Video ID: {video_id}")
        print(f"  É Live: {is_live}")
        print(f"  Válida: {is_valid}")
        print()

if __name__ == "__main__":
    test_youtube_urls()

