# 도서 리뷰를 수집하고, 수집한 리뷰를 CSV 파일로 저장
# 각 도서의 리뷰 개수, 리뷰 내용을 수집하며 페이지별 제한과 책별 리뷰 개수를 설정

from selenium import webdriver  # 웹 드라이버를 불러옴
from selenium.webdriver.chrome.service import Service  # Chrome 서비스 설정
from webdriver_manager.chrome import ChromeDriverManager  # 크롬 드라이버 관리자
from selenium.webdriver.common.by import By  # 요소를 찾기 위한 By 모듈
from selenium.webdriver.support.ui import WebDriverWait  # 명시적 대기를 위한 WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # 특정 조건이 충족될 때까지 대기
import os 
import time  # 대기 시간 설정
import re  # 정규 표현식 모듈
import csv  # CSV 파일로 저장하기 위한 모듈
from selenium.webdriver.common.keys import Keys  # 키보드 조작 모듈
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException  # 예외 처리 모듈

# 1. Chrome 드라이버 설정 및 생성
driver_path = ChromeDriverManager().install()  # ChromeDriverManager를 통해 크롬 드라이버 설치 경로를 가져옴
correct_driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe")  # 드라이버 경로를 OS에 맞게 설정
driver = webdriver.Chrome(service=Service(executable_path=correct_driver_path))  # Chrome 드라이버 생성

# 2. URL 설정 및 리뷰 수집 관련 변수 초기화
TOTAL_PAGES = 2  # 수집할 페이지 수 설정
TOTAL_BOOKS = 20 * TOTAL_PAGES  # 페이지당 20권의 책이므로 총 수집할 책 수 설정
all_reviews = []  # 모든 리뷰를 저장할 리스트
MAX_REVIEWS_PER_BOOK = 3  # 각 책당 최대 수집할 리뷰 개수
MAX_TOTAL_REVIEWS = 5000  # 전체 리뷰가 이 개수를 넘으면 종료

# 페이지 반복
for page in range(1, TOTAL_PAGES + 1):  # 지정한 페이지 수만큼 반복

    # 각 페이지의 URL 설정
    url = f"https://store.kyobobook.co.kr/bestseller/steady/domestic?page={page}"
    driver.get(url)  # 설정한 URL로 이동
    print(f'접속한 URL = {url}')
    
    driver.implicitly_wait(6)  # 페이지 로딩 대기
    driver.maximize_window()  # 브라우저 전체화면

    # 페이지 배율을 50%로 조정하여 더 많은 정보를 화면에 표시
    driver.execute_script("""document.body.style.transform = 'scale(0.5)'; document.body.style.transformOrigin = '0 0';""")

    # 각 페이지의 책 20권에 대해 반복
    for i in range(1, 21):  
        
        # 전체 리뷰 수가 최대 수집 개수에 도달하면 종료
        if len(all_reviews) >= MAX_TOTAL_REVIEWS:
            break
        
        try:
            # 페이지 상단과 하단 섹션을 나누어 책 제목을 가져옴
            if i <= 10:  # 상단 섹션
                book_title_element = driver.find_element(By.XPATH, f'/html/body/div[1]/main/section/div/div/section/ol[1]/li[{i}]/div/div[2]/div[2]/a')
            else:  # 하단 섹션
                book_title_element = driver.find_element(By.XPATH, f'/html/body/div[1]/main/section/div/div/section/ol[2]/li[{i - 10}]/div/div[2]/div[2]/a')
    
            # 도서 제목 텍스트 가져오기 및 파일명에 사용 불가한 문자 제거
            book_title = book_title_element.text.replace(':', ' ').replace('/', ' ').strip()
            print(f"도서 제목: {book_title}")
    
            # 도서 제목 요소가 클릭 가능할 때까지 대기한 후 클릭
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[1]/main/section/div/div/section/ol[{1 if i <= 10 else 2}]/li[{i if i <= 10 else i - 10}]/div/div[2]/div[1]/a/div/img')))
            book_title_element.click()  # 클릭하여 도서 상세 페이지로 이동
    
            driver.implicitly_wait(3)  # 자원 로딩을 위해 3초 대기
    
            # 페이지 배율을 50%로 조정하여 전체 페이지가 보이도록 설정
            driver.execute_script("""document.body.style.transform = 'scale(0.5)'; document.body.style.transformOrigin = '0 0';""")
    
        except NoSuchElementException:
            # 요소가 존재하지 않을 경우 다음 책으로 넘어감
            print(f"{i}번째 책을 찾지 못했습니다. 다음 책으로 넘어갑니다.")
            continue
        except Exception as e:
            # 다른 오류 발생 시 오류 메시지 출력 후 다음 책으로 넘어감
            print(f"오류 발생: {e}")
            continue
        
        # 개별 도서의 리뷰 개수를 가져와서 수집 시작
        try:
            review_count_element = driver.find_element(By.CLASS_NAME, 'num')  # 리뷰 개수 요소 찾기
            review_text = review_count_element.text  # 리뷰 개수 텍스트 가져오기 (예: "(380)")
            print('리뷰 텍스트:', review_text)
    
            # 정규 표현식을 사용하여 숫자만 추출하여 리뷰 개수로 변환
            review_count = int(re.search(r'\d+', review_text).group())
            print(f'리뷰 개수: {review_count}')
            
            # 전체 리뷰 보기 버튼 클릭
            all_review_button = driver.find_element(By.XPATH, '/html/body/div[3]/main/section[2]/div[2]/div[2]/div[1]/section[3]/div[1]/div[3]/div[1]/ul/li[1]/button')
            all_review_button.send_keys(Keys.ENTER)  # Enter 키를 이용해 클릭
    
            # 개별 도서의 리뷰를 저장할 리스트 초기화
            book_reviews = [] 
            
            # 페이지별 리뷰 수집
            for p in range(1, (review_count // 10) + 1):  # 페이지 수에 따라 반복
                if len(book_reviews) >= MAX_REVIEWS_PER_BOOK:  # 설정한 개수만큼 수집하면 종료
                    break
                  
                # 각 페이지에서 리뷰 수집
                for r in range(1, 11):  # 각 페이지에서 최대 10개의 리뷰 수집
                    if len(book_reviews) >= MAX_REVIEWS_PER_BOOK:  # 설정한 개수만큼 수집하면 종료
                        break
    
                    try:
                        # 리뷰 요소를 찾고 텍스트를 수집하여 리스트에 추가
                        review = driver.find_element(By.XPATH, f'//*[@id="ReviewList1"]/div[3]/div[2]/div/div[1]/div[{r}]/div[2]/div/div/div/div')
                        book_reviews.append(review.text)
                        time.sleep(0.5)  # 수집 속도 조정을 위한 대기
                    except StaleElementReferenceException:
                        # 요소가 더 이상 유효하지 않은 경우 다시 시도
                        print(f"리뷰 {r}이(가) 더 이상 유효하지 않습니다. 다시 시도합니다.")
                        review = driver.find_element(By.XPATH, f'//*[@id="ReviewList1"]/div[3]/div[2]/div/div[1]/div[{r}]/div[2]/div/div/div/div')
                        book_reviews.append(review.text)
                        time.sleep(0.5)  # 수집 속도 조정
    
                # 다음 페이지 버튼 클릭
                if len(book_reviews) < MAX_REVIEWS_PER_BOOK :
                    try:
                        page_tag = driver.find_element(By.XPATH, '//*[@id="ReviewList1"]/div[3]/div[2]/div/div[2]/button[2]')
                        page_tag.click()  # 버튼 클릭으로 다음 페이지로 이동
                        time.sleep(0.2)  # 페이지 로딩 대기
                    except StaleElementReferenceException:
                        # 페이지 버튼이 더 이상 유효하지 않을 경우 재시도
                        print("페이지 버튼이 더 이상 유효하지 않습니다. 다시 시도합니다.")
                        page_tag = driver.find_element(By.XPATH, '//*[@id="ReviewList1"]/div[3]/div[2]/div/div[2]/button[2]')
                        page_tag.click()  # 재시도 클릭
                        time.sleep(0.2)  # 페이지 로딩 대기
            
            # 현재 책의 모든 리뷰를 전체 리뷰 리스트에 추가
            all_reviews.extend(book_reviews)                
    
        except Exception as e:
            # 리뷰 수집 과정에서 오류 발생 시 오류 메시지 출력
            print(f"오류 발생: {e}")
          
        
        # 이전 페이지로 돌아가기
        driver.back()
            
        # 대기 후 배율 조정 (이전 페이지가 완전히 로드된 후 배율 조정)
        time.sleep(1)  # 페이지 로딩 대기
        driver.execute_script("""document.body.style.transform = 'scale(0.5)';document.body.style.transformOrigin = '0 0';""")

# 드라이버 종료
driver.quit()

# 최종 리뷰 수와 리뷰 내용 출력
print(f"총 수집된 리뷰 개수: {len(all_reviews)}")
for idx, review in enumerate(all_reviews, 1):
    print(f"review {idx}: {review}\n")
         
# 리뷰를 CSV 파일로 저장하기 위한 경로 설정
csv_file_path = fr'C:\ITWILL\project_wc\all_reviews.csv'
os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)  # 디렉토리가 없으면 생성

# 수집한 리뷰를 CSV 파일에 저장
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["Review"])  # 헤더 추가
    for review in all_reviews:
        writer.writerow([review])  # 각 리뷰를 행으로 추가
print(f"모든 리뷰가 {csv_file_path}에 저장되었습니다.")
