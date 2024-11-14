# 텍스트 감정 분류 모델을 학습하고 평가
# 학습된 Naive Bayes 모델과 TF-IDF 벡터라이저를 저장

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix
from konlpy.tag import Okt
from joblib import dump  # 모델 저장을 위한 모듈

# 1. CSV 파일 로드
data_path = r"C:\ITWILL\3_TextMining\labeled_data.csv"  # 데이터 파일 경로 설정
df = pd.read_csv(data_path)  # CSV 파일 로드

# 데이터 확인 (초기 데이터의 일부를 출력)
print(df.head())

# 2. 변수 준비 (문장과 라벨)
# 감정 라벨이 3, 4, 5, 6인 데이터를 제외하고 필터링
df = df[~((df['예측 라벨'] == 3) | (df['예측 라벨'] == 4) | (df['예측 라벨'] == 5) | (df['예측 라벨'] == 6))]

# 리뷰 텍스트와 감정 라벨로 각각 변수 설정
reviews = df['Review']  # 리뷰 텍스트
labels = df['예측 라벨']  # 감정 라벨

# 3. 한글 형태소 분석기 초기화 및 DTM 생성
# 리뷰 텍스트를 형태소 분석하여 명사만 추출하는 함수 정의
def tokenize(text):
    return Okt().nouns(text)  # 명사만 추출하여 리스트로 반환

# 4. TF-IDF 벡터화
# 리뷰 텍스트를 TF-IDF 벡터로 변환하여 학습에 사용
tfidf = TfidfVectorizer(tokenizer=tokenize, max_features=4000, min_df=5, max_df=0.5)  # 최대 4000개의 단어만 사용, 최소 문서 빈도 5
X = tfidf.fit_transform(reviews).toarray()  # 리뷰 데이터를 벡터화하고 배열 형태로 변환

# 5. 라벨 데이터 준비
y = labels  # 감정 라벨을 y로 설정

# 6. 훈련/테스트 데이터 분리 (75% 훈련, 25% 테스트)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)  # 데이터를 75% 훈련, 25% 테스트로 분할

# 7. Naive Bayes 분류기 학습 및 예측
nb_model = MultinomialNB()  # 멀티노미얼 나이브 베이즈 모델 생성
nb_model.fit(X_train, y_train)  # 모델 학습

# 테스트 데이터로 예측 수행
y_pred = nb_model.predict(X_test)

# 8. 모델 평가 (정확도 및 혼동 행렬)
acc = accuracy_score(y_test, y_pred)  # 예측 정확도 계산
print(f'Naive Bayes 분류 정확도: {acc}')  # 정확도 출력

conf_matrix = confusion_matrix(y_test, y_pred)  # 혼동 행렬 생성
print(f'\n혼동 행렬:\n{conf_matrix}')  # 혼동 행렬 출력

# 9. 각 클래스별 예측률 계산
for i in range(len(conf_matrix)):  # 각 클래스에 대해 반복
    class_acc = conf_matrix[i, i] / sum(conf_matrix[i])  # 클래스별 예측률 계산
    print(f'클래스 {i} 예측률: {class_acc}')  # 클래스별 예측률 출력

# 10. 모델 및 TF-IDF 벡터라이저 저장
# 학습된 모델과 TF-IDF 벡터라이저를 파일로 저장
model_path = r"C:\ITWILL\3_TextMining\naive_bayes_model.pkl"
vectorizer_path = r"C:\ITWILL\3_TextMining\tfidf_vectorizer.pkl"

# 모델과 벡터라이저 각각 저장
dump(nb_model, model_path)  # 모델 저장
dump(tfidf, vectorizer_path)  # 벡터라이저 저장
print(f"모델이 '{model_path}'에 저장되었습니다.")  # 모델 저장 경로 출력
print(f"TF-IDF 벡터라이저가 '{vectorizer_path}'에 저장되었습니다.")  # 벡터라이저 저장 경로 출력
