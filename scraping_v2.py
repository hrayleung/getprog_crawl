import time
import json
import getpass
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException

# URL基础部分 - 修正yo_employment参数
LOGIN_URL = "https://app.getprog.ai/login"
BASE_SEARCH_URL = "https://app.getprog.ai/search/results?countries[]=United%20States&locations[]=San%20Francisco%2C%20California,San%20Jose%2C%20California,Berkeley%2C%20California,Oakland%2C%20California,Palo%20Alto%2C%20California,Mountain%20View%2C%20California,California&page=0&size=100&text=AI%20Engineer%20%26%20Researcher%20%E2%80%93%20Multimodal%0AMust-Have%0APython%0AJAX%0ARust%0AMultimodal%20%28image%2Fvideo%2Faudio%29%20understanding%20and%20generation%0AData%20filtering%2C%20generation%2C%20and%20quality%20evaluation%0AInternal%20benchmark%20%28benchmarking%29%20construction%0ANice-to-Have%0ALarge-scale%20distributed%20ML%20system%20experience%0AEnd-to-end%20experiment%20design%20and%20iterative%20debugging%0AResearch%20paper%20authorship%20and%20results%20publication%0ARobotics%20Experience%0ALocation%3A%20San%20Francisco%2C%20California%20San%20Jose%2C%20California%20Berkeley%2C%20California%20Oakland%2C%20California%20Palo%20Alto%2C%20California%20Mountain%20View%2C%20California&yo_employment[]=0-3,3-5&yo_experience[]=0-3,5-10,3-5"

# 每页显示的结果数量
RESULTS_PER_PAGE = 100
MAX_CANDIDATES = 9000


def setup_driver():
    """Set up and return a Chrome webdriver with appropriate options."""
    chrome_options = Options()
    # 在测试登录时，最好不使用headless模式，便于查看登录过程
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def setup_driver_no_image():
    """Set up and return a Chrome webdriver with appropriate options, disabling images loading."""
    chrome_options = Options()
    # 禁用图片加载
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    
    # 其他必要的配置
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def save_page_source(driver, filename):
    """保存页面源代码用于调试"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"已保存页面源代码到 {filename}")

def login(driver, email, password):
    """处理分步登录过程"""
    try:
        print("正在访问登录页面...")
        driver.get(LOGIN_URL)
        
        # 等待页面加载完成
        time.sleep(5)
        
        # 打印所有输入框检查登录页结构
        print("页面上的输入元素:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_placeholder = inp.get_attribute("placeholder")
            print(f"输入框 {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
        
        # 查找邮箱输入框
        email_input = None
        try:
            email_input = driver.find_element(By.CSS_SELECTOR, "input[name='email'], input[placeholder='Email'], input[type='email']")
            print("找到邮箱输入框")
        except NoSuchElementException:
            print("未找到邮箱输入框，尝试使用第一个文本输入框")
            try:
                email_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            except NoSuchElementException:
                # 最后尝试任何输入框
                if inputs:
                    email_input = inputs[0]
                else:
                    raise Exception("找不到任何输入框")
        
        # 输入邮箱
        if email_input:
            email_input.clear()
            email_input.send_keys(email)
            print(f"已输入邮箱: {email}")
        else:
            raise Exception("找不到邮箱输入框")
        
        # 查找并点击"Continue"按钮
        continue_button = None
        try:
            # 尝试多种可能的选择器查找"Continue"按钮
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"找到 {len(buttons)} 个按钮")
            
            for button in buttons:
                button_text = button.text.strip().lower()
                print(f"按钮文本: '{button_text}'")
                if button_text in ["continue", "next", "下一步", "继续"]:
                    continue_button = button
                    print(f"找到Continue按钮: {button_text}")
                    break
            
            # 如果没找到明确的Continue按钮，尝试提交表单按钮
            if not continue_button:
                try:
                    continue_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    print("使用提交按钮作为Continue按钮")
                except NoSuchElementException:
                    # 如果仍然没有找到，尝试任何可点击的按钮
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            continue_button = button
                            print(f"使用可见按钮作为Continue按钮: {button.text}")
                            break
            
            if not continue_button and len(buttons) > 0:
                continue_button = buttons[0]  # 使用第一个按钮
                print("使用第一个按钮作为Continue按钮")
                
        except Exception as e:
            print(f"查找Continue按钮时出错: {str(e)}")
        
        # 点击Continue按钮
        if continue_button:
            print(f"点击 '{continue_button.text}' 按钮")
            continue_button.click()
        else:
            # 如果找不到按钮，尝试按回车键提交
            print("找不到Continue按钮，尝试按回车键提交")
            email_input.send_keys("\n")
        
        # 等待密码输入框出现
        print("等待密码输入框出现...")
        time.sleep(5)  # 给页面足够时间加载第二步
        
        # 再次检查输入元素
        print("第二步页面上的输入元素:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_placeholder = inp.get_attribute("placeholder")
            print(f"输入框 {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
        
        # 查找密码输入框
        password_input = None
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password'], input[placeholder='Password']")
            print("找到密码输入框")
        except NoSuchElementException:
            print("未找到明确的密码输入框，尝试查找任何新出现的输入框")
            
            # 尝试查找任何可能的密码输入框
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                # 检查是否为密码类型
                if inp.get_attribute("type") == "password":
                    password_input = inp
                    print("找到密码类型输入框")
                    break
            
            # 如果仍未找到，使用任何可见的输入框
            if not password_input and inputs:
                for inp in inputs:
                    if inp.is_displayed():
                        password_input = inp
                        print("使用可见输入框作为密码输入框")
                        break
        
        # 输入密码
        if password_input:
            password_input.clear()
            password_input.send_keys(password)
            print("已输入密码")
        else:
            raise Exception("找不到密码输入框，请检查登录页面的第二步")
        
        # 查找并点击最终的登录按钮
        login_button = None
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"找到 {len(buttons)} 个按钮")
            
            for button in buttons:
                button_text = button.text.strip().lower()
                print(f"按钮文本: '{button_text}'")
                if button_text in ["sign in", "log in", "login", "登录", "signin"]:
                    login_button = button
                    print(f"找到登录按钮: {button_text}")
                    break
            
            # 如果没找到明确的登录按钮，尝试提交按钮
            if not login_button:
                try:
                    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    print("使用提交按钮作为登录按钮")
                except NoSuchElementException:
                    # 如果仍然没有找到，尝试任何可点击的按钮
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            login_button = button
                            print(f"使用可见按钮作为登录按钮: {button.text}")
                            break
        except Exception as e:
            print(f"查找登录按钮时出错: {str(e)}")
        
        # 点击登录按钮
        if login_button:
            print(f"点击 '{login_button.text}' 按钮")
            login_button.click()
        else:
            # 如果找不到按钮，尝试按回车键提交
            print("找不到登录按钮，尝试按回车键提交")
            password_input.send_keys("\n")
        
        # 等待登录成功
        print("等待登录完成...")
        time.sleep(10)
        
        # 检查是否登录成功
        if "login" in driver.current_url.lower():
            print("登录可能失败，请检查登录页面截图")
            return False
        
        print("登录成功!")
        return True
        
    except Exception as e:
        print(f"登录过程中出错: {str(e)}")
        return False

def get_search_url(page_number, size=20):
    """根据页码构建搜索URL"""
    return f"{BASE_SEARCH_URL}&page={page_number+1}&size={size}"

def analyze_page_structure(driver, page_number):
    """分析页面结构，查找可能包含候选人信息的元素"""
    print(f"==== 分析第 {page_number+1} 页页面结构... ====")
    
    # 查找页面上的所有div元素
    all_divs = driver.find_elements(By.TAG_NAME, "div")
    print(f"页面上共有 {len(all_divs)} 个div元素")
    
    # 打印页面上所有class名称
    classes = set()
    for div in all_divs:
        class_name = div.get_attribute("class")
        if class_name:
            classes.add(class_name)
    
    print(f"第 {page_number+1} 页上的class名称列表:")
    for cls in classes:
        print(f"- {cls}")
    
    # 查找可能的表格或列表元素
    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"找到 {len(tables)} 个表格元素")
    
    lists = driver.find_elements(By.TAG_NAME, "ul")
    print(f"找到 {len(lists)} 个列表元素")
    
    # 查找可能包含搜索结果的元素
    result_candidates = []
    possible_result_classes = ["result", "search", "candidate", "profile", "card", "list", "container"]
    for div in all_divs:
        class_name = div.get_attribute("class") or ""
        if any(term in class_name.lower() for term in possible_result_classes):
            try:
                text = div.text
                if text and len(text) > 50:  # 只考虑包含一定文本的元素
                    result_candidates.append({
                        "element": div,
                        "class": class_name,
                        "text_length": len(text)
                    })
            except:
                pass
    
    print(f"找到 {len(result_candidates)} 个可能包含搜索结果的元素")
    for i, candidate in enumerate(result_candidates):
        print(f"候选结果容器 {i+1}: class='{candidate['class']}', 文本长度={candidate['text_length']}")
    
    return result_candidates

def extract_info_from_element(element, page_number):
    """从元素中提取候选人信息，只保留干净的数据，不包含HTML"""
    try:
        # 获取原始文本内容
        element_text = element.text.strip()
        if not element_text:
            return None  # 如果没有文本内容，返回None
            
        # 过滤掉纯UI元素如按钮、标签、百分比匹配等
        if len(element_text) < 20:  # 太短的文本可能是UI元素
            return None
            
        # 过滤掉看起来像UI元素的文本
        ui_patterns = [
            r'^\d+%\s*match$',  # 匹配百分比
            r'^\+\d+\s*more$',   # +N more 按钮
            r'^[a-z\-]+$',       # 单个小写标签如 "python", "rust"
            r'^(?:python|rust|spark|scale|ai|jax|robotics|throughput|multimodal|preprocessing)$',  # 常见技能标签
        ]
        
        if any(re.search(pattern, element_text.lower()) for pattern in ui_patterns):
            return None
        
        # 保存原始文本，但不保存HTML
        text_lines = element_text.split('\n')
        # 过滤掉空行和只有空格的行
        text_lines = [line.strip() for line in text_lines if line.strip()]
        
        if not text_lines:
            return None  # 如果没有有效内容，返回None
            
        # 初始化候选人信息
        candidate = {
            "page": page_number + 1,  # 记录来自哪一页
            "name": "Unknown",
            "position": "",
            "experience": "",
            "location": "",
            "github": "",
            "linkedin": "",
            "education": "",
            "skills": []
        }
            
        # 尝试提取标题/职位信息 (通常是第一行)
        title_text = text_lines[0] if text_lines else ""
        
        # 识别姓名和职位
        # 典型的名字模式: 首字母大写的两个或更多单词
        name_pattern = r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$'
        job_keywords = ["engineer", "developer", "scientist", "manager", "lead", "head", 
                       "architect", "specialist", "analyst", "consultant", "intern", "researcher", 
                       "software", "data", "system", "director", "@"]
        
        # 姓名检测
        if re.match(name_pattern, title_text) and not any(keyword.lower() in title_text.lower() for keyword in job_keywords):
            candidate["name"] = title_text
            
            # 找职位 (通常在姓名后的第一行)
            for line in text_lines[1:]:
                if any(keyword.lower() in line.lower() for keyword in job_keywords) and len(line) > 5:
                    candidate["position"] = line
                    break
        else:
            # 如果第一行不是名字，可能是职位
            if any(keyword.lower() in title_text.lower() for keyword in job_keywords) and len(title_text) > 5:
                candidate["position"] = title_text
                
                # 看看是否可以从其他行找到名字
                for line in text_lines[1:]:
                    if re.match(name_pattern, line) and not any(kw.lower() in line.lower() for kw in job_keywords):
                        candidate["name"] = line
                        break
        
        # 提取经验信息
        for line in text_lines:
            # 匹配常见的经验表示形式
            exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:experience|exp)?', line, re.IGNORECASE)
            if exp_match:
                candidate["experience"] = f"{exp_match.group(1)} years"
                break
            
            # 简短的经验表示
            short_exp = re.search(r'(\d+)\s*y\s+experience', line, re.IGNORECASE)
            if short_exp:
                candidate["experience"] = f"{short_exp.group(1)} years"
                break
        
        # 提取位置信息
        for line in text_lines:
            # 尝试匹配加州城市
            location_match = re.search(r'((?:San Francisco|San Jose|Berkeley|Oakland|Palo Alto|Mountain View)(?:,\s*(?:California|CA))?)', line, re.IGNORECASE)
            if location_match:
                location = location_match.group(1)
                # 确保包含州名
                if "california" not in location.lower() and "ca" not in location.lower().split():
                    location += ", California"
                candidate["location"] = location
                break
        
        # 提取LinkedIn和GitHub链接
        github_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='github.com']")
        if github_elements:
            candidate["github"] = github_elements[0].get_attribute("href")
            
        linkedin_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='linkedin.com']")
        if linkedin_elements:
            candidate["linkedin"] = linkedin_elements[0].get_attribute("href")
        
        # 提取教育信息
        edu_keywords = ["University", "College", "Bachelor", "Master", "PhD", "B.S.", "M.S.", "Ph.D."]
        for line in text_lines:
            if any(keyword.lower() in line.lower() for keyword in edu_keywords):
                candidate["education"] = line
                break
        
        # 提取技能关键词
        skills = []
        skill_keywords = ["Python", "Java", "JavaScript", "C++", "Rust", "Go", "SQL", "Spark", "Hadoop", 
                         "AWS", "Azure", "GCP", "Docker", "Kubernetes", "React", "Angular", "Vue", 
                         "Data Science", "Machine Learning", "AI", "Deep Learning", "Cloud", "Big Data"]
        
        for line in text_lines:
            for skill in skill_keywords:
                if re.search(r'\b' + re.escape(skill) + r'\b', line, re.IGNORECASE):
                    skills.append(skill)
        
        # 去除重复技能并排序
        candidate["skills"] = sorted(list(set(skills)))
        
        # 如果没有抓取到明显的信息，可能不是真正的候选人
        non_empty_fields = sum(1 for field in ["name", "position", "location", "experience", "github", "linkedin"] 
                              if candidate[field] and candidate[field] != "Unknown")
        
        if non_empty_fields < 2 and not candidate["github"] and not candidate["linkedin"]:
            return None  # 信息太少，可能是误提取
        
        print(f"提取到的候选人信息: {candidate}")
        return candidate
    except Exception as e:
        print(f"从元素提取信息时出错: {str(e)}")
        return None

def extract_candidate_info_from_page(driver, page_number):
    """从当前页面提取候选人信息"""
    candidates = []
    
    # 首先分析页面结构
    result_containers = analyze_page_structure(driver, page_number)
    
    # 尝试使用多种方式提取数据
    try:
        # 等待一些时间确保页面完全加载
        print("等待页面元素加载...")
        time.sleep(5)
        
        # 跟踪已处理的元素，避免重复
        processed_elements = set()
        
        # 1. 优先查找明确的候选人行 - ProfileRow元素
        try:
            print("尝试查找ProfileRow元素...")
            # 寻找最顶层的ProfileRow元素，通常是直接包含候选人完整信息的元素
            # 修改选择器以更精确地匹配主要候选人行
            main_profile_rows = driver.find_elements(By.CSS_SELECTOR, 
                "tr[class*='ProfileRow_profile'], div[class*='search-result-item']")
            
            if not main_profile_rows or len(main_profile_rows) < RESULTS_PER_PAGE / 2:
                # 尝试其他常见的选择器
                main_profile_rows = driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='profile-row'], [class*='profile_row'], [class*='ProfileRow']")
            
            # 过滤掉可能的子元素，只保留主要行
            valid_rows = []
            for row in main_profile_rows:
                # 如果元素已经处理过，跳过
                element_id = row.id
                if element_id in processed_elements:
                    continue
                    
                # 检查是否包含足够的内容
                text = row.text.strip()
                if len(text) > 100:  # 主要候选人行通常包含较多文本
                    valid_rows.append(row)
                    processed_elements.add(element_id)
            
            print(f"找到 {len(valid_rows)} 个有效的候选人行")
            
            # 如果找到的行数接近预期的每页数量，使用这些行
            if len(valid_rows) >= min(10, RESULTS_PER_PAGE / 2):
                for row in valid_rows:
                    candidate = extract_info_from_element(row, page_number)
                    if candidate:
                        print(f"页面 {page_number+1} 提取到 (ProfileRow): {candidate['name']} - {candidate['position']}")
                        candidates.append(candidate)
                        
                # 如果候选人数已经接近预期数量，直接返回
                if len(candidates) >= min(15, RESULTS_PER_PAGE * 0.75):
                    print(f"通过ProfileRow选择器已提取 {len(candidates)} 个候选人，接近预期")
                    return candidates[:RESULTS_PER_PAGE]  # 最多返回RESULTS_PER_PAGE个
        except Exception as e:
            print(f"使用ProfileRow选择器提取数据时出错: {str(e)}")
        
        # 2. 尝试查找卡片布局
        if len(candidates) < RESULTS_PER_PAGE / 2:
            try:
                print("尝试查找完整的候选人卡片...")
                # 修改选择器以更精确地匹配候选人卡片
                profile_cards = driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='candidate-card'], div[class*='profile-card'], div[class*='item']")
                
                # 过滤重复和无效的卡片
                valid_cards = []
                for card in profile_cards:
                    # 检查是否已处理
                    element_id = card.id
                    if element_id in processed_elements:
                        continue
                        
                    # 检查是否为有效卡片
                    text = card.text.strip()
                    if len(text) > 100 and '\n' in text:
                        valid_cards.append(card)
                        processed_elements.add(element_id)
                
                print(f"找到 {len(valid_cards)} 个有效候选人卡片")
                
                # 提取候选人信息
                for card in valid_cards:
                    candidate = extract_info_from_element(card, page_number)
                    if candidate:
                        print(f"页面 {page_number+1} 提取到 (Card): {candidate['name']} - {candidate['position']}")
                        candidates.append(candidate)
                        
                # 最多保留RESULTS_PER_PAGE个候选人
                if len(candidates) > RESULTS_PER_PAGE:
                    print(f"提取了 {len(candidates)} 个候选人，超过每页预期，截取为 {RESULTS_PER_PAGE}")
                    candidates = candidates[:RESULTS_PER_PAGE]
            except Exception as e:
                print(f"提取候选人卡片时出错: {str(e)}")
        
        # 如果找到了足够的候选人，返回结果
        if candidates:
            print(f"从第 {page_number+1} 页成功提取 {len(candidates)} 个候选人信息")
            return candidates[:RESULTS_PER_PAGE]  # 确保不超过每页上限
        
        # 3. 如果以上方法都失败，最后尝试从页面结构提取
        print("尝试从页面结构中提取候选人...")
        if result_containers:
            # 按文本长度排序，优先考虑文本较长的容器
            result_containers.sort(key=lambda x: x["text_length"], reverse=True)
            
            for container_info in result_containers[:2]:  # 只尝试前2个最可能的容器
                container = container_info["element"]
                try:
                    # 查找容器中可能的候选人元素
                    potential_elements = container.find_elements(By.CSS_SELECTOR, 
                        "div[class*='item'], div[class*='row'], div[class*='card']")
                    
                    # 过滤元素
                    for el in potential_elements:
                        # 检查是否已处理
                        element_id = el.id
                        if element_id in processed_elements:
                            continue
                            
                        # 检查是否为有效元素
                        text = el.text.strip()
                        if len(text) > 100 and '\n' in text:
                            candidate = extract_info_from_element(el, page_number)
                            if candidate:
                                print(f"页面 {page_number+1} 提取到 (Container Element): {candidate['name']} - {candidate['position']}")
                                candidates.append(candidate)
                                processed_elements.add(element_id)
                                
                                # 达到每页上限后停止
                                if len(candidates) >= RESULTS_PER_PAGE:
                                    break
                                    
                    if len(candidates) >= RESULTS_PER_PAGE:
                        break
                except Exception as e:
                    print(f"从容器提取信息时出错: {str(e)}")
    
    except Exception as e:
        print(f"提取候选人信息时出错: {str(e)}")
    
    # 返回提取的候选人信息，最多不超过每页上限
    candidates = candidates[:RESULTS_PER_PAGE]
    print(f"从第 {page_number+1} 页成功提取 {len(candidates)} 个候选人信息")
    return candidates

def find_pagination_elements(driver):
    """寻找所有可能的分页元素并返回详细信息"""
    pagination_elements = []
    
    # 尝试多种选择器以找到分页元素
    selectors = [
        ".pagination", 
        "[class*='pagination']",
        "[role='navigation']", 
        "nav",
        "[class*='nav']",
        "[class*='pager']",
        "[class*='pages']"
    ]
    
    # 找出所有可能包含分页的容器
    containers = []
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            containers.extend(elements)
        except Exception as e:
            print(f"查找分页容器时出错 ({selector}): {str(e)}")
    
    print(f"找到 {len(containers)} 个可能的分页容器")
    
    # 从每个容器中提取按钮
    for container in containers:
        try:
            # 查找所有按钮和链接
            buttons = container.find_elements(By.TAG_NAME, "button")
            links = container.find_elements(By.TAG_NAME, "a")
            
            # 处理按钮
            for button in buttons:
                try:
                    text = button.text.strip()
                    aria_label = button.get_attribute("aria-label") or ""
                    is_disabled = button.get_attribute("disabled") is not None
                    classname = button.get_attribute("class") or ""
                    
                    # 判断按钮类型
                    button_type = "unknown"
                    if "next" in text.lower() or "下一页" in text or ">" in text or "→" in text:
                        button_type = "next"
                    elif "prev" in text.lower() or "上一页" in text or "<" in text or "←" in text:
                        button_type = "prev"
                    elif text.isdigit():
                        button_type = "page"
                    
                    # 如果按钮上没有文本，尝试根据aria-label和class判断
                    if not text and button_type == "unknown":
                        if any(term in aria_label.lower() for term in ["next", "下一页"]):
                            button_type = "next"
                        elif any(term in classname.lower() for term in ["next", "forward"]):
                            button_type = "next"
                    
                    pagination_elements.append({
                        "element": button,
                        "text": text,
                        "type": button_type,
                        "is_disabled": is_disabled,
                        "element_type": "button"
                    })
                except Exception as e:
                    print(f"处理分页按钮时出错: {str(e)}")
            
            # 处理链接
            for link in links:
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href") or ""
                    aria_label = link.get_attribute("aria-label") or ""
                    classname = link.get_attribute("class") or ""
                    
                    # 判断链接类型
                    link_type = "unknown"
                    if "next" in text.lower() or "下一页" in text or ">" in text or "→" in text:
                        link_type = "next"
                    elif "prev" in text.lower() or "上一页" in text or "<" in text or "←" in text:
                        link_type = "prev"
                    elif text.isdigit():
                        link_type = "page"
                    
                    # 如果链接上没有文本，尝试根据href、aria-label和class判断
                    if not text and link_type == "unknown":
                        if "page=" in href and href.split("page=")[1].split("&")[0].isdigit():
                            page_num = href.split("page=")[1].split("&")[0]
                            link_type = "page"
                            text = page_num
                        elif any(term in aria_label.lower() for term in ["next", "下一页"]):
                            link_type = "next"
                        elif any(term in classname.lower() for term in ["next", "forward"]):
                            link_type = "next"
                    
                    pagination_elements.append({
                        "element": link,
                        "text": text,
                        "type": link_type,
                        "href": href,
                        "element_type": "link"
                    })
                except Exception as e:
                    print(f"处理分页链接时出错: {str(e)}")
                    
        except Exception as e:
            print(f"从容器提取分页元素时出错: {str(e)}")
    
    # 根据SVG图标查找下一页按钮(如果还没找到)
    if not any(el["type"] == "next" for el in pagination_elements):
        try:
            # 尝试查找可能包含箭头图标的元素
            svg_containers = driver.find_elements(By.CSS_SELECTOR, 
                "button svg, a svg, [class*='next'] svg, [class*='arrow'] svg")
            
            for container in svg_containers:
                parent = container
                # 向上查找5层，寻找可点击的父元素
                for _ in range(5):
                    try:
                        parent = parent.find_element(By.XPATH, "./..")
                        if parent.tag_name in ["button", "a"]:
                            pagination_elements.append({
                                "element": parent,
                                "text": "SVG Icon",
                                "type": "next",
                                "element_type": parent.tag_name
                            })
                            print("找到基于SVG图标的下一页按钮")
                            break
                    except:
                        break
        except Exception as e:
            print(f"查找SVG图标分页按钮时出错: {str(e)}")
    
    # 打印找到的分页元素信息
    print(f"找到 {len(pagination_elements)} 个分页元素")
    for i, el in enumerate(pagination_elements):
        print(f"分页元素 {i+1}: 类型={el['type']}, 文本='{el['text']}', 元素类型={el['element_type']}")
    
    return pagination_elements

def navigate_to_page(driver, page_number):
    """导航到指定页面"""
    current_url = driver.current_url
    
    if page_number == 0:
        # 首页直接访问
        url = BASE_SEARCH_URL
        print(f"正在导航到第 1 页: {url}")
        driver.get(url)
    else:
        # 后续页面尝试通过多种方式导航
        print(f"尝试导航到第 {page_number+1} 页")
        
        # 首先检查是否已经在正确的页面上
        if f"page={page_number+1}" in current_url:
            print(f"已经在第 {page_number+1} 页，无需导航")
            return True
        
        # 尝试通过点击分页按钮导航
        try:
            # 查找并分析所有分页元素
            pagination_elements = find_pagination_elements(driver)
            
            # 首先查找指定页码的按钮
            page_button = None
            for el in pagination_elements:
                if el["type"] == "page" and el["text"] == str(page_number+1):
                    page_button = el
                    print(f"找到第 {page_number+1} 页的按钮")
                    break
            
            # 如果找不到指定页码，尝试使用"下一页"按钮
            if not page_button and page_number > 0:
                # 找到"下一页"按钮
                next_buttons = [el for el in pagination_elements if el["type"] == "next"]
                
                if next_buttons:
                    # 优先使用未禁用的按钮
                    active_next_buttons = [btn for btn in next_buttons if not btn.get("is_disabled", False)]
                    if active_next_buttons:
                        page_button = active_next_buttons[0]
                        print(f"找到下一页按钮: {page_button['text']}")
                    elif next_buttons:
                        page_button = next_buttons[0]
                        print(f"找到下一页按钮(可能已禁用): {page_button['text']}")
            
            # 尝试点击找到的按钮
            if page_button:
                element = page_button["element"]
                # 滚动到按钮可见
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(2)
                
                try:
                    # 尝试点击按钮
                    print(f"尝试点击分页元素: {page_button['text']}")
                    element.click()
                    print(f"已点击分页元素")
                    # 等待页面加载
                    time.sleep(5)
                    
                    # 检查URL是否变化
                    new_url = driver.current_url
                    if new_url != current_url:
                        print(f"URL已变化: {new_url}")
                        return True
                    else:
                        print("点击后URL未变化，尝试JavaScript点击")
                        # 尝试使用JavaScript点击
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(5)
                        
                        # 再次检查URL
                        if driver.current_url != current_url:
                            print(f"JavaScript点击后URL已变化: {driver.current_url}")
                            return True
                
                except (ElementNotInteractableException, ElementClickInterceptedException) as e:
                    print(f"直接点击失败: {str(e)}，尝试JavaScript点击")
                    try:
                        # 尝试使用JavaScript点击
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(5)
                        
                        # 检查URL是否变化
                        if driver.current_url != current_url:
                            print(f"JavaScript点击后URL已变化: {driver.current_url}")
                            return True
                    except Exception as js_e:
                        print(f"JavaScript点击也失败: {str(js_e)}")
                
                except Exception as e:
                    print(f"点击分页元素时出错: {str(e)}")
        
        except Exception as e:
            print(f"通过分页按钮导航时出错: {str(e)}")
        
        # 如果点击导航失败，尝试直接通过URL导航
        print("通过按钮导航失败，尝试直接访问URL")
        url = get_search_url(page_number)
        driver.get(url)
    
    # 等待页面加载完成(增加等待时间)
    print(f"等待第 {page_number+1} 页加载...")
    time.sleep(10)  # 先等10秒
    
    # 检查页面内容是否实际加载了
    try:
        # 等待页面上出现候选人信息
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "[class*='profile'], [class*='candidate'], [class*='card'], [class*='result-item']")) > 2
        )
    except TimeoutException:
        print(f"等待候选人信息超时，尝试刷新页面...")
        driver.refresh()
        time.sleep(10)
    
    # 滚动页面加载所有内容
    print(f"滚动第 {page_number+1} 页加载所有内容...")
    # 多次滚动确保所有内容加载
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(5):  # 增加滚动次数
        scroll_point = total_height * (i + 1) / 6
        driver.execute_script(f"window.scrollTo(0, {scroll_point});")
        print(f"滚动到位置: {scroll_point}")
        time.sleep(3)  # 每次滚动后等待一下
    
    # 滚动回顶部
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # 检查页面是否确实显示了搜索结果
    profile_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='profile'], [class*='candidate'], [class*='card'], [class*='result-item']")
    print(f"页面上找到 {len(profile_elements)} 个可能的候选人元素")
    
    if len(profile_elements) < 3:
        print("警告: 找到的候选人元素太少，可能页面未正确加载")
        return False
    
    # 再次检查页面是否包含预期的内容
    content = driver.page_source
    if ("没有结果" in content or "No results" in content) and page_number > 0:
        print(f"警告: 第 {page_number+1} 页显示没有结果，可能需要重新登录")
        return False
    elif len(content) < 5000 and page_number > 0:  # 内容太少可能是页面未加载
        print(f"警告: 第 {page_number+1} 页内容异常少，可能未正确加载")
        return False
    
    print(f"第 {page_number+1} 页成功加载")
    return True

def clean_data(candidates):
    """清理和检查数据质量"""
    cleaned = []
    print("\n==== 开始数据清理 ====")
    
    for i, candidate in enumerate(candidates):
        print(f"清理前 ({i+1}/{len(candidates)}): {candidate}")
        # 确保所有必要字段存在
        required_fields = ["name", "position", "github", "linkedin", "location", "experience", "education", "skills", "page"]
        for field in required_fields:
            if field not in candidate:
                candidate[field] = "" if field != "skills" else []
        
        # 清理经验字段，确保格式一致
        if candidate["experience"]:
            # 如果经验字段看起来包含了位置信息，修复它
            if any(city in candidate["experience"].lower() for city in ["san francisco", "san jose", "oakland", "berkeley", "palo alto", "mountain view"]):
                # 将经验值移动到位置字段
                if not candidate["location"]:
                    candidate["location"] = candidate["experience"]
                # 清空经验字段
                candidate["experience"] = ""
                
        # 如果姓名字段包含职位信息，修复它
        if candidate["name"] != "Unknown":
            job_indicators = ["engineer", "developer", "programmer", "lead", "senior", "software", "data scientist", "@"]
            if any(indicator.lower() in candidate["name"].lower() for indicator in job_indicators):
                # 如果名字包含职位信息，可能是错误的，将其移至职位字段
                if not candidate["position"]:
                    candidate["position"] = candidate["name"]
                candidate["name"] = "Unknown"
                
        # 检查职位字段是否实际上是名字
        if candidate["position"] and candidate["name"] == "Unknown":
            # 名字通常是首字母大写的2-3个单词
            name_pattern = r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$'
            job_indicators = ["engineer", "developer", "scientist", "manager", "lead", "senior", "@"]
            
            if re.match(name_pattern, candidate["position"]) and not any(ind.lower() in candidate["position"].lower() for ind in job_indicators):
                candidate["name"] = candidate["position"]
                candidate["position"] = ""
        
        # 对于职位字段，确保关键职位单词首字母大写
        if candidate["position"]:
            terms_to_capitalize = ["engineer", "developer", "scientist", "manager", "lead", "architect", "senior", "data"]
            position = candidate["position"]
            for term in terms_to_capitalize:
                # 将术语替换为首字母大写形式
                pattern = re.compile(r'\b' + term + r'\b', re.IGNORECASE)
                position = pattern.sub(term.capitalize(), position)
            candidate["position"] = position.strip()
        
        # 过滤掉似乎是无意义UI元素的条目
        if (candidate["position"] in ["scale", "+1 more", "+2 more", "+3 more", "+6 more", "throughput", "preprocessing"] or 
            candidate["position"].lower() in ["python", "rust", "spark", "ai"] or 
            re.match(r'^\d+% match$', candidate["position"])):
            print(f"过滤掉UI元素: {candidate['position']}")
            continue
            
        print(f"清理后 ({i+1}/{len(candidates)}): {candidate}")
        # 添加到清理后的列表
        cleaned.append(candidate)
    
    print(f"==== 数据清理完成，清理后记录数: {len(cleaned)} ====")
    return cleaned

def merge_candidate_entries(entries):
    """合并多个候选人条目"""
    if not entries:
        return None
    
    print(f"\n-- 开始合并 {len(entries)} 个条目 --")
    for i, entry in enumerate(entries):
        print(f"待合并条目 {i+1}: {entry}")
        
    # 使用第一个条目作为基础
    merged = entries[0].copy()
    
    # 遍历其余条目来填充缺失信息
    for entry in entries[1:]:
        for field in ["name", "position", "location", "experience", "github", "linkedin", "education"]:
            # 如果当前字段为空而其他条目有值，则填充
            if (not merged[field] or merged[field] == "Unknown") and entry[field] and entry[field] != "Unknown":
                merged[field] = entry[field]
        
        # 合并技能
        if entry["skills"]:
            merged["skills"] = sorted(list(set(merged["skills"] + entry["skills"])))
    
    # 确保名字不是"Unknown"如果有其他标识信息
    if merged["name"] == "Unknown" and (merged["github"] or merged["linkedin"]):
        # 尝试从GitHub或LinkedIn URL中提取用户名
        if merged["github"]:
            github_username = merged["github"].split("/")[-1]
            if github_username and github_username != "":
                merged["name"] = github_username + " (from GitHub)"
        elif merged["linkedin"]:
            linkedin_parts = merged["linkedin"].split("/")
            if len(linkedin_parts) > 4:
                merged["name"] = linkedin_parts[-1] + " (from LinkedIn)"
    
    print(f"合并后结果: {merged}")
    print("-- 条目合并完成 --")
    return merged

def remove_duplicates(candidates):
    """移除重复的候选人信息并合并相关条目"""
    print("\n==== 开始去重处理 ====")
    print(f"去重前共 {len(candidates)} 条记录")
    
    # 第一步：按GitHub和LinkedIn分组
    grouped_by_links = {}
    print("\n-- 按GitHub/LinkedIn链接分组 --")
    
    # 先处理有GitHub或LinkedIn的候选人
    for candidate in candidates:
        key = None
        if candidate["github"]:
            key = f"github:{candidate['github']}"
        elif candidate["linkedin"]:
            key = f"linkedin:{candidate['linkedin']}"
            
        if key:
            print(f"候选人 {candidate.get('name', 'N/A')} (Page: {candidate.get('page', 'N/A')}) 加入链接分组 {key}")
            if key not in grouped_by_links:
                grouped_by_links[key] = []
            grouped_by_links[key].append(candidate)
    
    # 第二步：按姓名分组剩余候选人
    name_grouped = {}
    print("\n-- 按姓名分组 (无链接的候选人) --")
    for candidate in candidates:
        if candidate["name"] != "Unknown" and not candidate["github"] and not candidate["linkedin"]:
            key = f"name:{candidate['name']}"
            print(f"候选人 {candidate['name']} (Page: {candidate.get('page', 'N/A')}) 加入姓名分组 {key}")
            if key not in name_grouped:
                name_grouped[key] = []
            name_grouped[key].append(candidate)
    
    # 第三步：合并条目
    merged_candidates = []
    print("\n-- 合并链接分组的条目 --")
    
    # 合并GitHub/LinkedIn分组
    for key, group in grouped_by_links.items():
        if len(group) == 1:
            print(f"链接分组 {key} 只有一个条目，直接添加: {group[0].get('name', 'N/A')}")
            merged_candidates.append(group[0])
        else:
            print(f"链接分组 {key} 有 {len(group)} 个条目，进行合并")
            # 合并多个条目
            merged = merge_candidate_entries(group)
            merged_candidates.append(merged)
    
    print("\n-- 合并姓名分组的条目 --")
    # 合并姓名分组
    for key, group in name_grouped.items():
        if len(group) == 1:
            # 检查这个候选人是否已通过GitHub/LinkedIn添加
            name = group[0]["name"]
            is_duplicate = False
            for cand in merged_candidates:
                if cand["name"] == name and (cand["github"] or cand["linkedin"]):
                    print(f"姓名分组 {key} 的 {name} 已通过链接存在，标记为重复")
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                print(f"姓名分组 {key} 只有一个条目且不重复，直接添加: {name}")
                merged_candidates.append(group[0])
            else:
                print(f"姓名分组 {key} 的 {name} 为重复项，已跳过")
        else:
            # 合并多个条目
            print(f"姓名分组 {key} 有 {len(group)} 个条目，进行合并")
            merged = merge_candidate_entries(group)
            
            # 检查是否已存在
            is_duplicate = False
            for cand in merged_candidates:
                if cand["name"] == merged["name"] and (cand["github"] or cand["linkedin"]):
                    print(f"合并后的姓名条目 {merged['name']} 已通过链接存在，标记为重复")
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                print(f"合并后的姓名条目 {merged['name']} 不重复，添加")
                merged_candidates.append(merged)
            else:
                print(f"合并后的姓名条目 {merged['name']} 为重复项，已跳过")
    
    # 添加剩余没有归类的候选人（没有GitHub、LinkedIn，名字为Unknown的情况）
    position_grouped = {}
    print("\n-- 按职位/地点分组 (无链接且名字为Unknown的候选人) --")
    for candidate in candidates:
        if (candidate["name"] == "Unknown" and not candidate["github"] and not candidate["linkedin"] and 
            candidate["position"] and len(candidate["position"]) > 10):
            
            # 使用职位和位置作为键
            key = f"pos:{candidate['position']}|loc:{candidate['location']}"
            print(f"候选人 (Position: {candidate['position']}, Location: {candidate['location']}, Page: {candidate.get('page', 'N/A')}) 加入职位/地点分组 {key}")
            if key not in position_grouped:
                position_grouped[key] = []
            position_grouped[key].append(candidate)
    
    print("\n-- 合并职位/地点分组的条目 --")
    # 合并职位分组中的唯一条目
    for key, group in position_grouped.items():
        if len(group) > 0:
            print(f"职位/地点分组 {key} 有 {len(group)} 个条目，进行合并")
            merged = merge_candidate_entries(group)
            
            # 检查是否与已有条目重复（基于职位和位置）
            is_duplicate = False
            for cand in merged_candidates:
                if (cand["position"] == merged["position"] and 
                    cand["location"] == merged["location"] and 
                    cand["experience"] == merged["experience"] and
                    (cand["github"] or cand["linkedin"] or cand["name"] != "Unknown")):
                    print(f"合并后的职位/地点条目 (Pos: {merged['position']}, Loc: {merged['location']}) 与已有条目重复，标记为重复")
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                print(f"合并后的职位/地点条目 (Pos: {merged['position']}, Loc: {merged['location']}) 不重复，添加")
                merged_candidates.append(merged)
            else:
                print(f"合并后的职位/地点条目 (Pos: {merged['position']}, Loc: {merged['location']}) 为重复项，已跳过")
    
    print(f"\n==== 去重处理完成 ====")
    print(f"去重前: {len(candidates)} 条记录, 去重后: {len(merged_candidates)} 条记录")
    return merged_candidates

def main():
    """运行主程序，完成登录和数据抓取"""
    try:
        # 设置WebDriver，使用禁用图片的版本
        driver = setup_driver_no_image()
        
        # 获取登录凭据
        email = input("请输入你的 getprog.ai 登录邮箱: ")
        password = getpass.getpass("请输入密码: ")
        
        # 尝试登录
        login_success = login(driver, email, password)
        
        if not login_success:
            print("登录失败，请检查凭据并重试。")
            driver.quit()
            return
        
        # 抓取多页候选人信息
        all_candidates = []
        page_number = 0
        # 增加最大页数到150页，确保即使每页只提取20人也能达到3000人
        max_pages = 900
        
        # 主抓取循环
        while page_number < max_pages and len(all_candidates) < MAX_CANDIDATES:
            print(f"\n==== 正在处理第 {page_number+1} 页 ====")
            
            # 导航到指定页面
            page_loaded = navigate_to_page(driver, page_number)
            
            # 如果页面加载失败，可能是会话过期，尝试重新登录
            if not page_loaded:
                print("页面加载失败，尝试重新登录...")
                login_success = login(driver, email, password)
                if login_success:
                    # 重新尝试导航
                    page_loaded = navigate_to_page(driver, page_number)
                    if not page_loaded:
                        print(f"重登录后仍然无法加载第 {page_number+1} 页，跳过")
                        # 尝试继续下一页
                        page_number += 1
                        continue
                else:
                    print("重新登录失败，终止程序")
                    break
            
            # 提取候选人信息
            candidates = extract_candidate_info_from_page(driver, page_number)
            
            # 如果获取到的候选人太少（少于5个），可能是页面加载问题，重试一次
            if len(candidates) < 5 and page_number > 0:
                print(f"第 {page_number+1} 页提取的候选人太少，尝试重新加载...")
                navigate_to_page(driver, page_number)
                candidates = extract_candidate_info_from_page(driver, page_number)
                
                # 如果仍然太少，可能是已经到达结果末尾
                if len(candidates) < 3:
                    print(f"重试后仍然没有足够的候选人，可能已到达结果末尾")
                    # 保存现有结果并退出循环
                    break
            
            # 清理数据
            candidates = clean_data(candidates)
            
            # 添加到总列表
            all_candidates.extend(candidates)
            
            print(f"第 {page_number+1} 页共获取 {len(candidates)} 个候选人信息，总计: {len(all_candidates)}/{MAX_CANDIDATES}")
            
            # 准备进入下一页
            page_number += 1
            
            # 在页面之间暂停，避免请求过快
            if page_number < max_pages and len(all_candidates) < MAX_CANDIDATES:
                print(f"等待5秒后加载第 {page_number+1} 页...")
                time.sleep(5)
        
        # 去重处理
        unique_candidates = remove_duplicates(all_candidates)
        
        # 保存结果到JSON文件
        output_file = "getprog_candidates.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unique_candidates, f, ensure_ascii=False, indent=2)
        
        print(f"\n抓取完成! 共获取 {len(unique_candidates)} 个唯一候选人信息，保存到 {output_file}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭浏览器
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main() 