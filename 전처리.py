import pandas as pd
import re
from konlpy.tag import Okt

# 1. 감정 라벨과 키워드 정의
emotion_labels = {
    0: ["기쁨", "행복", "즐거움", "웃음", "신남", "만족", "기쁘다", "즐겁다", "행복하다", "웃기다", "좋다", 
        "즐거운", "유쾌한", "상쾌함", "사랑", "사랑스럽다", "행복한", "즐거운 일", "소중한", "환호", 
        "축하", "빛나는", "상쾌하다", "기분 좋음", "희열", "벅차오름", "활기", "환희", "즐거운 추억", "환상적"],

    1: ["믿음", "신뢰", "의지", "충성", "친밀함", "배려", "믿다", "의지하다", "신뢰하다", "의지됨", 
        "가깝다", "친근감", "동료애", "사랑", "지원", "함께하다", "연대", "협력", "기대", "안정감", 
        "소통", "연결", "상호작용", "신뢰감", "신뢰할 수 있는", "협동", "연합", "믿을 수 있는", "연민", "우정", "친애"],

    2: ["두려움", "불안", "걱정", "겁", "초조", "무서움", "무섭다", "두렵다", "불안하다", "초조하다", 
        "겁난다", "걱정스럽다", "두려움", "두려운", "신경 쓰이다", "조마조마하다", "우려", "위험감", 
        "공포", "소름", "불안정", "불안정하다", "위협", "위험", "막막함", "두려워하다", "두려워하는", "불안한", "무기력",

        "놀람", "경악", "충격", "깜짝", "어리둥절", "뜻밖", "놀랍다", "경악하다", "충격적이다", "깜짝 놀라다", 
        "놀란", "예상치 못한", "급작스러운", "당황", "충격적인", "의아함", "비상", "불안정", "의외", 
        "뜻밖의", "놀랍도록", "흥미로운", "경이로운", "충격과 공포", "혼란", "어리둥절한", "미지의", "신비로운", "상상 밖의",

        "슬픔", "우울", "눈물", "아픔", "외로움", "침울", "슬프다", "눈물나다", "우울하다", "외롭다", 
        "아프다", "상실", "고통", "비애", "우울증", "상심", "슬프고 아픈", "우울한", "고독", 
        "한숨", "슬픈 기억", "애도", "처참함", "허전함", "상심한", "감정적 고통", "우울감", "이별의 아픔", "상실감",

        "싫음", "혐오", "역겨움", "거부감", "짜증", "경멸", "싫다", "짜증난다", "역겹다", "거부하다", 
        "싫어하다", "불쾌감", "부정적", "혐오감", "억압감", "거부감", "싫어지는", "불만", "미움", 
        "지긋지긋함", "고통스러운", "불쾌한", "혐오스러운", "경악할만한", "싫어하는", "실망", "비난", "거부당하다",

        "화", "분노", "짜증", "성남", "격분", "열받다", "화나다", "짜증난다", "분노하다", "빡치다", 
        "억울함", "불쾌함", "분노의", "격렬한", "화가 나는", "화내다", "모욕감", "흥분", "열정적", 
        "격렬한 감정", "부정적 감정", "불만족", "전투적인", "치솟는", "성급한", "격렬한 반응", "공격적"],
    
    3: ["놀람", "경악", "충격", "깜짝", "어리둥절", "뜻밖", "놀랍다", "경악하다", "충격적이다", "깜짝 놀라다", 
       "놀란", "예상치 못한", "급작스러운", "당황", "충격적인", "의아함", "비상", "불안정", "의외", 
       "뜻밖의", "놀랍도록", "흥미로운", "경이로운", "충격과 공포", "혼란", "어리둥절한", "미지의", "신비로운", "상상 밖의"],

    4: ["슬픔", "우울", "눈물", "아픔", "외로움", "침울", "슬프다", "눈물나다", "우울하다", "외롭다", 
        "아프다", "상실", "고통", "비애", "우울증", "상심", "슬프고 아픈", "우울한", "고독", 
        "한숨", "슬픈 기억", "애도", "처참함", "허전함", "상심한", "감정적 고통", "우울감", "이별의 아픔", "상실감"],

    5: ["싫음", "혐오", "역겨움", "거부감", "짜증", "경멸", "싫다", "짜증난다", "역겹다", "거부하다", 
        "싫어하다", "불쾌감", "부정적", "혐오감", "억압감", "거부감", "싫어지는", "불만", "미움", 
        "지긋지긋함", "고통스러운", "불쾌한", "혐오스러운", "경악할만한", "싫어하는", "실망", "비난", "거부당하다"],

    6: ["화", "분노", "짜증", "성남", "격분", "열받다", "화나다", "짜증난다", "분노하다", "빡치다", 
        "억울함", "불쾌함", "분노의", "격렬한", "화가 나는", "화내다", "모욕감", "흥분", "열정적", 
        "격렬한 감정", "부정적 감정", "불만족", "전투적인", "치솟는", "성급한", "격렬한 반응", "공격적"],
    
    7: ["기대", "희망", "설렘", "궁금증", "열망", "기다림", "기대하다", "희망하다", "설렌다", "기대된다", 
        "소망", "갈망", "열망하다", "기대하는","기대되는","희망의 등불", "희망의 꽃", "희망의 날개", "희망의 힘" "기회", "미래에 대한 기대", "꿈", "가능성", 
        "기대감", "희망찬", "희망적인", "흥미", "흥분되는", "참을성", "장래의", "미래 지향적", "설레임", "환상", "성장", "환희","햇살", "햇빛","온정","현의",
        "싱그럽다", "두근", "드디어", "내일", "기억", "하늘", "고전","힘", "영감","계발", "풍요", "경험", "진화"]
}



# 2. CSV 파일 불러오기 (결측값 처리 포함)
path = r'C:\ITWILL\3_TextMining'
unlabeled_df = pd.read_csv(path + '/all_reviews.csv')
unlabeled_df = unlabeled_df.fillna("")



print(unlabeled_df.head())

# 3. 형태소 분석기 초기화 및 전처리 함수 정의
okt = Okt()

def tokenize(text):
    """형태소 분석을 통해 문장을 토큰화"""
    if not isinstance(text, str):
        text = ""
    return okt.morphs(text)  # 형태소 단위로 분리된 리스트 반환

# 4. 감정 키워드를 활용해 라벨링 함수 정의
def label_sentence(tokens):
    """토큰화된 문장에 키워드가 포함된 경우 해당 라벨 반환"""
    for label, keywords in emotion_labels.items():
        if any(keyword in tokens for keyword in keywords):
            return label
    return -1  # 해당되지 않으면 -1 반환

# 5. 문장 데이터 전처리 및 라벨링 적용
unlabeled_df['토큰화 문장'] = unlabeled_df['Review'].apply(tokenize)
unlabeled_df['예측 라벨'] = unlabeled_df['토큰화 문장'].apply(label_sentence)

# 6. -1로 라벨링된 행 삭제
labeled_df = unlabeled_df[unlabeled_df['예측 라벨'] != -1]

# 사용자 지정 불용어 리스트
custom_stopwords = ["택배", "배송", "축하", "노벨상", "수상"]

# 불용어가 포함된 행 필터링 함수 정의
def contains_stopword(text):
    if pd.isna(text):  # 만약 텍스트가 NaN이면 False 반환
        return False
    return any(stopword in text for stopword in custom_stopwords)

# 불용어가 포함된 문장과 라벨 삭제
labeled_df = labeled_df[~labeled_df['Review'].apply(contains_stopword)]

# 7. 라벨링된 데이터 출력
print(labeled_df.head())

# 8. 토큰화 열 제외하고 CSV로 저장
output_path = r"C:/ITWILL/3_TextMining/labeled_data.csv"
labeled_df[['Review', '예측 라벨']].to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"라벨링된 데이터가 '{output_path}'에 저장되었습니다.")

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix
from konlpy.tag import Okt

# 1. CSV 파일 로드
data_path = r"C:/ITWILL/3_TextMining/labeled_data.csv"  # 올바른 경로로 설정
df = pd.read_csv(data_path)

# 데이터 확인
print(df.head())

# 2. 변수 준비 (문장과 라벨)
df = df[~((df['예측 라벨'] == 3) | (df['예측 라벨'] == 4) | (df['예측 라벨'] == 5) | (df['예측 라벨'] == 6))] # 감정 라벨이 5 또는 6인 행을 제외

reviews = df['Review']  # 리뷰 텍스트
labels = df['예측 라벨']  # 감정 라벨


# 3. 한글 형태소 분석기 초기화 및 DTM 생성

def tokenize(text):
    return Okt().nouns(text)  # 리뷰 텍스트에서 명사 추출

# 4. TF-IDF 벡터화
tfidf = TfidfVectorizer(tokenizer=tokenize, max_features=4000, min_df=5, max_df=0.5)
X = tfidf.fit_transform(reviews).toarray()

# 5. 라벨 데이터 
y = labels

# 6. 훈련/테스트 데이터 분리 (75% 훈련, 25% 테스트)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# 7. Naive Bayes 분류기 학습 및 예측
nb_model = MultinomialNB()
nb_model.fit(X_train, y_train)

# 테스트 데이터로 예측 수행
y_pred = nb_model.predict(X_test)

# 8. 모델 평가 (정확도 및 혼동 행렬)
acc = accuracy_score(y_test, y_pred)
print(f'Naive Bayes 분류 정확도: {acc}')

conf_matrix = confusion_matrix(y_test, y_pred)
print(f'\n혼동 행렬:\n{conf_matrix}')

# 9. 각 클래스별 예측률 계산
for i in range(len(conf_matrix)):
    class_acc = conf_matrix[i, i] / sum(conf_matrix[i])
    print(f'클래스 {i} 예측률: {class_acc}')

# 10. 모델 및 TF-IDF 벡터라이저 저장
from joblib import dump

model_path = r"C:/ITWILL/3_TextMining/naive_bayes_model.pkl"
vectorizer_path = r"C:/ITWILL/3_TextMining/tfidf_vectorizer.pkl"

# 모델과 벡터라이저 각각 저장
dump(nb_model, model_path)
dump(tfidf, vectorizer_path)
print(f"모델이 '{model_path}'에 저장되었습니다.")
print(f"TF-IDF 벡터라이저가 '{vectorizer_path}'에 저장되었습니다.")




