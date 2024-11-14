# tokenizer.py
from konlpy.tag import Okt  # KoNLPy의 Okt 형태소 분석기를 불러옴

# Okt 형태소 분석기 초기화
okt = Okt()

# 텍스트를 형태소 단위로 분리하여 토큰화하는 함수 정의
def tokenize(text):
    """입력 텍스트를 형태소 단위로 분리하여 토큰화"""
    if not isinstance(text, str):  # 입력이 문자열이 아닌 경우 빈 문자열로 처리
        text = ""
    return okt.morphs(text)  # 형태소 단위로 분리된 리스트 반환

# 다른 스크립트에서 tokenizer.py 모듈을 사용하기 위한 설정

import sys
sys.path.append('path/to/directory/containing/tokenizer')  # tokenizer.py가 있는 디렉토리 경로를 추가
from tokenizer import tokenize  # tokenizer 모듈에서 tokenize 함수 불러오기
