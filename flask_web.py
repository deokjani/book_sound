import time
from flask import Flask, render_template, request, send_from_directory, url_for, redirect, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from joblib import load
import os
import re
import csv
import pandas as pd
from collections import Counter
from tokenizer import tokenize
from konlpy.tag import Okt 
import urllib.parse
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from wordcloud import WordCloud
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
import pickle
from flask import Flask, render_template, abort
from matplotlib.colors import LinearSegmentedColormap


chrome_options = Options()
#chrome_options.add_argument('--headless')  # 헤드리스 모드 설정

# Flask 애플리케이션 설정
app = Flask(__name__)
app.config['MUSIC_FOLDER'] = "C:/ITWILL/3_TextMining/project/static/sounds"


# 감정 라벨에 맞는 음악 파일 경로 설정
# 'static' 폴더 내에 'sounds' 폴더가 있다고 가정하고 각 음악 파일을 저장
music_files = {
    0: "sounds/sunny_0.mp3",
    1: "sounds/slowmotion_1.mp3",
    2: "sounds/november_2.mp3",
    7: "sounds/energy_7.mp3"
}

# Selenium으로 이미지 URL과 번호 수집
def get_image_urls():
    image_urls = []
    book_titles = []
    # ChromeDriver 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://store.kyobobook.co.kr/bestseller/steady/domestic")  # 예시 URL
    driver.maximize_window()  # 전체화면으로 열기
    time.sleep(2)  # 페이지 전체 로딩을 위한 대기 시간

    # 1~10위 책 이미지 경로와 제목 가져오기
    for i in range(1, 11):  # li[i]의 i 값을 조정하여 원하는 순위 범위 지정
        image_xpath = f"/html/body/div[1]/main/section/div/div/section/ol[1]/li[{i}]/div/div[2]/div[1]/a/div/img"
        title_xpath = f"/html/body/div[1]/main/section/div/div/section/ol[1]/li[{i}]/div/div[2]/div[2]/a"
        
        # 이미지 URL 가져오기 시도
        image_url = None
        for attempt in range(3):  # 최대 3번 시도
            try:
                img_element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, image_xpath))
                )
                image_url = img_element.get_attribute("src")
                if image_url:
                    image_urls.append(image_url)
                    print(f"이미지 URL (index {i}): {image_url}")
                    break  # 성공적으로 URL을 가져왔으면 루프 탈출
            except (TimeoutException, StaleElementReferenceException) as e:
                print(f"이미지 로드 시도 {attempt + 1} 실패 (index {i}): {e}")
                time.sleep(2)  # 재시도 전 대기
        
        # 이미지가 없을 경우 기본 이미지로 대체
        if not image_url:
            print(f"이미지를 찾을 수 없습니다 (index {i}). 기본 이미지를 사용합니다.")
            default_image_url = url_for('static', filename='images/book.png', _external=True)
            image_urls.append(default_image_url)
        
        # 책 제목 가져오기
        try:
            title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, title_xpath))
            )
            book_title = title_element.text.strip()
            book_titles.append(book_title)
        except TimeoutException:
            print(f"책 제목을 찾을 수 없습니다 (index {i}). 제목을 기본값으로 설정합니다.")
            book_titles.append(f"Book {i}")

    driver.quit()

    # 책 제목과 이미지 URL을 DataFrame으로 생성
    book_df = pd.DataFrame({'Title': book_titles, 'Image_URL': image_urls})
    return book_df


# 검색 도서의 리뷰 수집 및 분석
def collect_and_analyze_reviews(query):   
    # ChromeDriver 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        # 검색 페이지로 이동
        driver.get(f"https://search.kyobobook.co.kr/search?keyword={query}&gbCode=TOT&target=total&gbCode=TOT&ra=kcont")
        driver.maximize_window()  # 전체화면으로 열기

        # 저자 정보 가져오기
        author_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="shopData_list"]/ul/li[1]/div[1]/div[2]/div[4]/div[1]/div[1]/div'))
        )
        author_text = author_element.text.strip()
        
        # 첫 번째 책 선택
        book_title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="shopData_list"]/ul/li[1]/div[1]/div[2]/div[2]/div[1]/div/a'))
        )
        book_title = book_title_element.text.strip()
        book_title_element.click()

        # 이미지 URL 가져오기
        try:
            img_element = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, '/html/body/div[3]/main/section[2]/div[1]/div/div[2]/div[2]/div[2]/div[1]/div[1]/ul/li[1]/div/div[2]/img'))
            )
            book_image_url = img_element.get_attribute("src")
            print("이미지 URL:", book_image_url)
        except TimeoutException:
            print("이미지 로드에 실패했습니다. 바로 리뷰 수집으로 이동합니다.")
            book_image_url = url_for('static', filename='images/book.png')

        # 페이지 배율을 50%로 조정
        driver.execute_script("document.body.style.transform = 'scale(0.5)'; document.body.style.transformOrigin = '0 0';")
        
        # 리뷰 버튼 클릭
        try:
            third_tab_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/main/section[2]/div[2]/div[1]/div/div[1]/ul/li[3]'))
            )
            driver.execute_script("arguments[0].click();", third_tab_element)  # JavaScript로 강제 클릭
            time.sleep(1)  # 클릭 후 대기
        except TimeoutException:
            print("지정된 탭 클릭에 실패했습니다.")
            
        # 전체 리뷰 버튼 클릭
        review_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/main/section[2]/div[2]/div[2]/div[1]/section[3]/div[1]/div[3]/div[1]/ul/li[1]/button'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", review_button)  # 스크롤로 버튼 위치 조정
        time.sleep(1)  # 스크롤 후 약간 대기
        review_button.click()

        # 리뷰 수집
        reviews = []
        for page in range(1, 6):  # 첫 5페이지의 리뷰 수집 예시
            for i in range(1, 11):
                try:
                    review_element = driver.find_element(By.XPATH, f'//*[@id="ReviewList1"]/div[3]/div[2]/div/div[1]/div[{i}]/div[2]/div/div/div/div')
                    reviews.append(review_element.text)
                except Exception as e:
                    print(f"Review collection error: {e}")
            # 다음 페이지로 이동
            try:
                next_button = driver.find_element(By.XPATH, '//*[@id="ReviewList1"]/div[3]/div[2]/div/div[2]/button[2]')
                next_button.click()
                time.sleep(2)
            except Exception as e:
                print(f"Pagination error: {e}")
                break
            
        # print(reviews)

    finally:
        driver.quit()
    
    # 리스트 -> 데이터프레임
    df = pd.DataFrame(reviews, columns=['Review'])
    df = df.fillna("")
    
    # 불용어 리스트
    custom_stopwords = ["택배", "배송", "축하", "노벨상", "수상"]
    
    #필터링 함수
    def contains_stopword(text):
        return any(stopword in text for stopword in custom_stopwords)

    # 불용어가 포함된 문장 삭제
    df = df[~df['Review'].apply(contains_stopword)]
   
    # 리뷰 분석: 사전 학습된 모델을 불러와 분석
    path = r"C:/ITWILL/3_TextMining/"
    model_path = os.path.join(path, 'naive_bayes_model.pkl')
    vectorizer_path = os.path.join(path, 'tfidf_vectorizer.pkl')
    model = load(model_path)
    vectorizer = load(vectorizer_path)
    
    # 리뷰 텍스트 전처리 및 TF-IDF 변환
    reviews_df = pd.DataFrame(reviews, columns=['Review'])
    X = vectorizer.transform(reviews_df['Review'])
    predictions = model.predict(X)
    
    # 가장 많이 나온 예측 라벨 찾기
    most_common_label = Counter(predictions).most_common(1)[0][0]
    label_dict = {0: "기쁜", 1: "신뢰의", 2: "불안한", 7: "기대의"}
    mood = label_dict.get(most_common_label, "기본")

    # 불용어 제거 
    for keyword in [" 저자(글)", "원작"]:
        if keyword in author_text:
            author_text = author_text.split(keyword)[0]
            break  # 첫 번째 조건을 충족하면 루프 중단
            
    if "] " in book_title:
        book_title = book_title.split("] ", 1)[1]


    return book_title, mood, book_image_url, author_text, df


# wordcloud 이미지 저장
matplotlib.use('Agg')

okt = Okt()

def wordcloud_img(df, book_title):
    # 1. 리뷰 텍스트 병합
    data = " ".join(df['Review'].astype(str))

    # 2. 명사 추출
    nouns = okt.nouns(data)
    # print("추출된 명사:", nouns)

    # 3. 단어 카운트 및 전처리: 단어 길이 제한
    nouns_count = {}
    for noun in nouns:
        if len(noun) > 1:  # 2음절 이상만 포함
            nouns_count[noun] = nouns_count.get(noun, 0) + 1

    # 4. 상위 50개 단어 추출
    top50_word = sorted(nouns_count.items(), key=lambda x: x[1], reverse=True)[:50]

    # 5. 단어 구름 생성
    base_dir = os.path.abspath(os.path.dirname(__file__))  # 프로젝트 디렉토리 경로
    img_path = os.path.join(base_dir, "static", "images", "wc_mask.jpg")
    
    # 마스크 이미지 로드
    wc_mask = np.array(Image.open(img_path))

    # 사용자 정의 색상 목록
    colors = ["#f5d6d6", "#f7e2d5", "#f6e9a7", "#e3efcd", "#b1deb8", "#a2d8ce", "#c7e3f9", "#dadff3", "#d6cce3", "#f0e0f0"]
    
    # 사용자 정의 컬러맵 생성
    custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", colors)
    
    # 워드 클라우드 설정
    wc = WordCloud(
        font_path='C:/Windows/Fonts/malgun.ttf',
        colormap=custom_cmap,
        width=500, height=400,
        max_words=100, max_font_size=150,
        background_color='#faf4e1',  # 배경색 설정
        mask=wc_mask
    )

    # 단어 구름 생성
    wc_result = wc.generate_from_frequencies(dict(top50_word))

    # 이미지 저장 경로 설정
    save_dir = os.path.join(base_dir, 'static', 'images')
    os.makedirs(save_dir, exist_ok=True)  # 폴더가 없으면 생성
    save_path = os.path.join(save_dir, f"{book_title}.png")
    
    print("이미지 저장 경로:", save_path)

    # 6. 단어 구름 시각화 및 저장
    plt.figure(figsize=(10, 8))
    plt.imshow(wc_result, interpolation='bilinear')
    plt.axis('off')  # 축 눈금 제거
    plt.savefig(save_path, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close()  # plt.show() 대신 닫기
    print("저장 완료")


# 피클 파일을 저장할 디렉토리 경로 설정
PICKLE_DIR = r"C:\ITWILL\3_TextMining\project1\static\mypickle"
os.makedirs(PICKLE_DIR, exist_ok=True)

# 책정보를 피클 파일로 저장
def save_book_info(book_title, author_text, music_file, book_image_url):
    book_details = [book_title, author_text, music_file, book_image_url]
    filename = os.path.join(PICKLE_DIR, f"{book_title}.pkl")
    with open(filename, 'wb') as file:
        pickle.dump(book_details, file)
    print(f"{filename} 파일로 저장되었습니다.")

# 책정보 피클 파일을 불러오기
def load_book_info(book_title):
    filename = os.path.join(PICKLE_DIR, f"{book_title}.pkl")
    try:
        with open(filename, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return None

# 피클 파일 존재 확인
def check_pickle_exists(book_title):
    filename = os.path.join(PICKLE_DIR, f"{book_title}.pkl")
    return os.path.exists(filename)

# 1. 메인 페이지: 도서 검색
@app.route('/')
def home():
    book_df = get_image_urls()  # DataFrame 생성
    book_data = list(zip(book_df['Title'].tolist(), book_df['Image_URL'].tolist()))  # 튜플 리스트로 변환
    print(book_data)
    return render_template('page_1.html', book_data=book_data)


# 2. 검색된 책 제목과 분석된 감정으로 음악 재생
@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')

    # 피클 파일이 있는지 확인
    if check_pickle_exists(query):
        # 피클 파일이 존재하면 데이터를 로드하고 재생 페이지로 이동
        book_details = load_book_info(query)
        if book_details:
            book_title, author_text, music_file, book_image_url = book_details
            return render_template('page_2.html', book_title=book_title,
                                   author_text=author_text, music_file=music_file, book_image_url=book_image_url)
        else:
            # 피클 파일이 있지만 로드 실패한 경우
            abort(404, description="Error loading book details from pickle file.")
    else:
        # 피클 파일이 없으면 검색 실행
        # 여기서 collect_and_analyze_reviews 함수를 호출해 검색 및 분석 실행
        book_title, mood, book_image_url, author_text, df = collect_and_analyze_reviews(query)
        wordcloud_img(df, book_title)
        
        # 음악 파일 경로 가져오기 (예시)
        mood_label_map = {"기쁜": 0, "신뢰의": 1, "불안한": 2, "기대의": 7}
        mood_code = mood_label_map.get(mood, None)
        music_file = url_for('static', filename=music_files.get(mood_code, ""))

        # 검색 결과를 피클 파일로 저장
        save_book_info(book_title, author_text, music_file, book_image_url)

        # 분석된 감정과 책 제목을 page_2.html로 전달
        return render_template('page_2.html', book_title=book_title, 
                               author_text=author_text, music_file=music_file, book_image_url=book_image_url)
 
 

# 3. 나의 책장 페이지: 저장된 책을 표시
@app.route('/bookshelf')
def bookshelf():
    return render_template('page_3.html')


# 4. 저장한 책 다시 노래듣기
@app.route('/replay/<book_title>')
def replay(book_title):
    # .pkl 파일에서 책 정보를 불러옴
    book_details = load_book_info(book_title)
    
    if book_details:
        book_title, author_text, music_file, book_image_url = book_details

        return render_template('page_2.html', book_title=book_title, 
                               author_text=author_text, music_file=music_file, book_image_url=book_image_url)
    else:
        # 파일이 없을 경우 404 에러 반환
        abort(404, description="Book not found")


# 5. 피클 파일 존재 여부 확인 API
@app.route('/check_pickle')
def check_pickle():
    title = request.args.get('title')
    exists = check_pickle_exists(title)
    return jsonify({'exists': exists})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80)