import time
import json
import getpass
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)

# Base URL part - corrected yo_employment parameter
LOGIN_URL = "https://app.getprog.ai/login"
BASE_SEARCH_URL = "https://app.getprog.ai/search/results?countries[]=United%20States&locations[]=San%20Francisco%2C%20California,San%20Jose%2C%20California,Berkeley%2C%20California,Oakland%2C%20California,Palo%20Alto%2C%20California,Mountain%20View%2C%20California&text=Software%20Engineer%20–%20Data%20Infrastructure%20%28Pretraining%20Data%29%0AMust-Have%0APython%0AJAX%0ARust%0ASpark%0APB-scale%20high-throughput%20data%20processing%0ACloud%20cluster%20job%20management%0AAI%20training%20data%20preprocessing%20pipelines%0ANice-to-Have%0ANVIDIA%20tools%20%28Omniverse%20%2F%20IsaacSim%20%2F%20Unity%29%0AMulti-cloud%2C%20multi-modal%20data%20management%20experience%0AExperience%20designing%20distributed%20systems%20from%20scratch%0ARobotics%20Experience&yo_employment[]=0-3,3-5"

# Number of results per page
RESULTS_PER_PAGE = 20
MAX_CANDIDATES = 60


def setup_driver():
    """Set up and return a Chrome webdriver with appropriate options."""
    chrome_options = Options()
    # When testing login, it's better not to use headless mode for easier viewing of the login process
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def setup_driver_no_image():
    """Set up and return a Chrome webdriver with appropriate options, disabling images loading."""
    chrome_options = Options()
    # Disable image loading
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_experimental_option(
        "prefs", {"profile.managed_default_content_settings.images": 2}
    )

    # Other necessary configurations
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def save_page_source(driver, filename):
    """Save page source code for debugging"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"Page source code saved to {filename}")


def login(driver, email, password):
    """Handle step-by-step login process"""
    try:
        print("Accessing login page...")
        driver.get(LOGIN_URL)

        # Wait for page to load
        time.sleep(5)

        # Print all input fields to check login page structure
        print("Input elements on the page:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_placeholder = inp.get_attribute("placeholder")
            print(
                f"Input field {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}"
            )

        # Find email input field
        email_input = None
        try:
            email_input = driver.find_element(
                By.CSS_SELECTOR,
                "input[name='email'], input[placeholder='Email'], input[type='email']",
            )
            print("Found email input field")
        except NoSuchElementException:
            print("Email input field not found, trying to use first text input field")
            try:
                email_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            except NoSuchElementException:
                # Finally try any input field
                if inputs:
                    email_input = inputs[0]
                else:
                    raise Exception("No input fields found")

        # Enter email
        if email_input:
            email_input.clear()
            email_input.send_keys(email)
            print(f"Email entered: {email}")
        else:
            raise Exception("Email input field not found")

        # Find and click "Continue" button
        continue_button = None
        try:
            # Try multiple possible selectors to find "Continue" button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} buttons")

            for button in buttons:
                button_text = button.text.strip().lower()
                print(f"Button text: '{button_text}'")
                # Added common English continue/next button texts, removed Chinese
                if button_text in ["continue", "next"]:
                    continue_button = button
                    print(f"Found Continue button: {button_text}")
                    break

            # If no clear Continue button found, try submit form button
            if not continue_button:
                try:
                    continue_button = driver.find_element(
                        By.CSS_SELECTOR, "button[type='submit']"
                    )
                    print("Using submit button as Continue button")
                except NoSuchElementException:
                    # If still not found, try any clickable button
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            continue_button = button
                            print(
                                f"Using visible button as Continue button: {button.text}"
                            )
                            break

            if not continue_button and len(buttons) > 0:
                continue_button = buttons[0]  # Use first button
                print("Using first button as Continue button")

        except Exception as e:
            print(f"Error finding Continue button: {str(e)}")

        # Click Continue button
        if continue_button:
            print(f"Clicking '{continue_button.text}' button")
            continue_button.click()
        else:
            # If no button found, try pressing Enter to submit
            print("Continue button not found, trying to submit with Enter key")
            email_input.send_keys("\n")

        # Wait for password input field to appear
        print("Waiting for password input field to appear...")
        time.sleep(5)  # Give page enough time to load second step

        # Check input elements again
        print("Input elements on second step page:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_placeholder = inp.get_attribute("placeholder")
            print(
                f"Input field {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}"
            )

        # Find password input field
        password_input = None
        try:
            password_input = driver.find_element(
                By.CSS_SELECTOR,
                "input[type='password'], input[name='password'], input[placeholder='Password']",
            )
            print("Found password input field")
        except NoSuchElementException:
            print(
                "No clear password input field found, trying to find any newly appeared input field"
            )

            # Try to find any possible password input field
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                # Check if it's a password type
                if inp.get_attribute("type") == "password":
                    password_input = inp
                    print("Found password type input field")
                    break

            # If still not found, use any visible input field
            if not password_input and inputs:
                for inp in inputs:
                    if inp.is_displayed():
                        password_input = inp
                        print("Using visible input field as password input field")
                        break

        # Enter password
        if password_input:
            password_input.clear()
            password_input.send_keys(password)
            print("Password entered")
        else:
            raise Exception(
                "Password input field not found, please check login page second step"
            )

        # Find and click final login button
        login_button = None
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} buttons")

            for button in buttons:
                button_text = button.text.strip().lower()
                print(f"Button text: '{button_text}'")
                # Added common English login button texts, removed Chinese
                if button_text in ["sign in", "log in", "login", "signin"]:
                    login_button = button
                    print(f"Found login button: {button_text}")
                    break

            # If no clear login button found, try submit form button
            if not login_button:
                try:
                    login_button = driver.find_element(
                        By.CSS_SELECTOR, "button[type='submit']"
                    )
                    print("Using submit button as login button")
                except NoSuchElementException:
                    # If still not found, try any clickable button
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            login_button = button
                            print(
                                f"Using visible button as login button: {button.text}"
                            )
                            break
        except Exception as e:
            print(f"Error finding login button: {str(e)}")

        # Click login button
        if login_button:
            print(f"Clicking '{login_button.text}' button")
            login_button.click()
        else:
            # If no button found, try pressing Enter to submit
            print("Login button not found, trying to submit with Enter key")
            password_input.send_keys("\n")

        # Wait for login to complete
        print("Waiting for login to complete...")
        time.sleep(10)

        # Check if login was successful
        if "login" in driver.current_url.lower():
            print("Login may have failed, still on login page")  # Slightly rephrased
            return False

        print("Login successful!")
        return True

    except Exception as e:
        print(f"Login error: {str(e)}")
        return False


def get_search_url(page_number, size=20):
    """Construct search URL based on page number"""
    return f"{BASE_SEARCH_URL}&page={page_number+1}&size={size}"


def analyze_page_structure(driver, page_number):
    """Analyze page structure to find elements potentially containing candidate information"""
    print(f"==== Analyzing page structure for page {page_number+1} ====")

    # Find all div elements on the page
    all_divs = driver.find_elements(By.TAG_NAME, "div")
    print(f"Found {len(all_divs)} div elements on the page")

    # Print all class names on the page
    classes = set()
    for div in all_divs:
        class_name = div.get_attribute("class")
        if class_name:
            classes.add(class_name)

    print(f"Class names on page {page_number+1}:")
    for cls in classes:
        print(f"- {cls}")

    # Find possible table or list elements
    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"Found {len(tables)} table elements")

    lists = driver.find_elements(By.TAG_NAME, "ul")
    print(f"Found {len(lists)} list elements")

    # Find elements potentially containing search results
    result_candidates = []
    possible_result_classes = [
        "result",
        "search",
        "candidate",
        "profile",
        "card",
        "list",
        "container",
    ]
    for div in all_divs:
        class_name = div.get_attribute("class") or ""
        if any(term in class_name.lower() for term in possible_result_classes):
            try:
                text = div.text
                if (
                    text and len(text) > 50
                ):  # Only consider elements with significant text
                    result_candidates.append(
                        {"element": div, "class": class_name, "text_length": len(text)}
                    )
            except:
                pass

    print(
        f"Found {len(result_candidates)} elements potentially containing search results"
    )
    for i, candidate in enumerate(result_candidates):
        print(
            f"Potential result container {i+1}: class='{candidate['class']}', text length={candidate['text_length']}"
        )

    return result_candidates


def extract_info_from_element(element, page_number):
    """Extract candidate information from element, keep only clean data without HTML"""
    try:
        # Get raw text content
        element_text = element.text.strip()
        if not element_text:
            return None  # Return None if no text content

        # Filter out pure UI elements like buttons, labels, percentage matches, etc.
        if len(element_text) < 20:  # Too short text could be a UI element
            return None

        # Filter out text that looks like UI elements
        ui_patterns = [
            r"^\d+%\s*match$",  # Match percentage
            r"^\+\d+\s*more$",  # +N more button
            r"^[a-z\-]+$",  # Single lowercase tag like "python", "rust"
            r"^(?:python|rust|spark|scale|ai|jax|robotics|throughput|multimodal|preprocessing)$",  # Common skill tags
        ]

        if any(re.search(pattern, element_text.lower()) for pattern in ui_patterns):
            return None

        # Save raw text, but not HTML
        text_lines = element_text.split("\n")
        # Filter out empty lines and lines with only whitespace
        text_lines = [line.strip() for line in text_lines if line.strip()]

        if not text_lines:
            return None  # Return None if no valid content

        # Initialize candidate information
        candidate = {
            "page": page_number + 1,  # Record from which page
            "name": "Unknown",
            "position": "",
            "experience": "",
            "location": "",
            "github": "",
            "linkedin": "",
            "education": "",
            "skills": [],
        }

        # Try to extract title/position information (usually the first line)
        title_text = text_lines[0] if text_lines else ""

        # Detect name and position
        # Typical name pattern: Capitalized two or more words
        name_pattern = r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$"
        job_keywords = [
            "engineer",
            "developer",
            "scientist",
            "manager",
            "lead",
            "head",
            "architect",
            "specialist",
            "analyst",
            "consultant",
            "intern",
            "researcher",
            "software",
            "data",
            "system",
            "director",
            "@",
        ]

        # Name detection
        if re.match(name_pattern, title_text) and not any(
            keyword.lower() in title_text.lower() for keyword in job_keywords
        ):
            candidate["name"] = title_text

            # Find position (usually in the first line after name)
            for line in text_lines[1:]:
                if (
                    any(keyword.lower() in line.lower() for keyword in job_keywords)
                    and len(line) > 5
                ):
                    candidate["position"] = line
                    break
        else:
            # If first line is not name, it could be position
            if (
                any(keyword.lower() in title_text.lower() for keyword in job_keywords)
                and len(title_text) > 5
            ):
                candidate["position"] = title_text

                # See if name can be found from other lines
                for line in text_lines[1:]:
                    if re.match(name_pattern, line) and not any(
                        kw.lower() in line.lower() for kw in job_keywords
                    ):
                        candidate["name"] = line
                        break

        # Extract experience information
        for line in text_lines:
            # Match common experience representation
            exp_match = re.search(
                r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:experience|exp)?",
                line,
                re.IGNORECASE,
            )
            if exp_match:
                candidate["experience"] = f"{exp_match.group(1)} years"
                break

            # Short experience representation
            short_exp = re.search(r"(\d+)\s*y\s+experience", line, re.IGNORECASE)
            if short_exp:
                candidate["experience"] = f"{short_exp.group(1)} years"
                break

        # Extract location information
        for line in text_lines:
            # Try to match California city
            location_match = re.search(
                r"((?:San Francisco|San Jose|Berkeley|Oakland|Palo Alto|Mountain View)(?:,\s*(?:California|CA))?)",
                line,
                re.IGNORECASE,
            )
            if location_match:
                location = location_match.group(1)
                # Ensure state name is included
                if (
                    "california" not in location.lower()
                    and "ca" not in location.lower().split()
                ):
                    location += ", California"
                candidate["location"] = location
                break

        # Extract LinkedIn and GitHub links
        github_elements = element.find_elements(
            By.CSS_SELECTOR, "a[href*='github.com']"
        )
        if github_elements:
            candidate["github"] = github_elements[0].get_attribute("href")

        linkedin_elements = element.find_elements(
            By.CSS_SELECTOR, "a[href*='linkedin.com']"
        )
        if linkedin_elements:
            candidate["linkedin"] = linkedin_elements[0].get_attribute("href")

        # Extract education information
        edu_keywords = [
            "University",
            "College",
            "Bachelor",
            "Master",
            "PhD",
            "B.S.",
            "M.S.",
            "Ph.D.",
        ]
        for line in text_lines:
            if any(keyword.lower() in line.lower() for keyword in edu_keywords):
                candidate["education"] = line
                break

        # Extract skill keywords
        skills = []
        skill_keywords = [
            "Python",
            "Java",
            "JavaScript",
            "C++",
            "Rust",
            "Go",
            "SQL",
            "Spark",
            "Hadoop",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "Kubernetes",
            "React",
            "Angular",
            "Vue",
            "Data Science",
            "Machine Learning",
            "AI",
            "Deep Learning",
            "Cloud",
            "Big Data",
        ]

        for line in text_lines:
            for skill in skill_keywords:
                if re.search(r"\b" + re.escape(skill) + r"\b", line, re.IGNORECASE):
                    skills.append(skill)

        # Remove duplicates and sort
        candidate["skills"] = sorted(list(set(skills)))

        # If no obvious information was captured, it might not be a real candidate
        non_empty_fields = sum(
            1
            for field in [
                "name",
                "position",
                "location",
                "experience",
                "github",
                "linkedin",
            ]
            if candidate[field] and candidate[field] != "Unknown"
        )

        if (
            non_empty_fields < 2
            and not candidate["github"]
            and not candidate["linkedin"]
        ):
            return None  # Information too little, possibly mis-extracted

        return candidate
    except Exception as e:
        print(f"Error extracting information from element: {str(e)}")
        return None


def extract_candidate_info_from_page(driver, page_number):
    """Extract candidate information from current page"""
    candidates = []

    # First analyze page structure
    result_containers = analyze_page_structure(driver, page_number)

    # Try using multiple methods to extract data
    try:
        # Wait longer time to ensure page fully loads
        print("Waiting for page elements to load...")
        time.sleep(10)  # Increased wait time

        # Track processed elements to avoid repeats
        processed_elements = set()

        # 1. Try to find complete candidate card - most reliable method
        try:
            print("Trying to find complete candidate card...")
            # More comprehensive selectors for candidate cards
            profile_cards = driver.find_elements(
                By.CSS_SELECTOR,
                "div[class*='candidate-card'], div[class*='profile-card'], div[class*='item'], div[class*='row'], div[class*='ProfileRow']",
            )

            # Filter out duplicates and invalid cards
            valid_cards = []
            for card in profile_cards:
                # Check if already processed
                element_id = card.id
                if element_id in processed_elements:
                    continue

                # Check if it's a valid card
                text = card.text.strip()
                if len(text) > 50 and "\n" in text:  # Reduced minimum text length
                    valid_cards.append(card)
                    processed_elements.add(element_id)

            print(f"Found {len(valid_cards)} valid candidate cards")

            # Extract candidate information
            for card in valid_cards:
                candidate = extract_info_from_element(card, page_number)
                if candidate:
                    candidates.append(candidate)

            # If we have enough candidates, return them
            if len(candidates) >= RESULTS_PER_PAGE:
                print(
                    f"Successfully extracted {len(candidates)} candidates using card layout"
                )
                return candidates[:RESULTS_PER_PAGE]

        except Exception as e:
            print(f"Error extracting candidate card: {str(e)}")

        # 2. If card method didn't work, try finding explicit candidate rows
        if len(candidates) < RESULTS_PER_PAGE:
            try:
                print("Trying to find ProfileRow elements...")
                # More comprehensive selectors for profile rows
                main_profile_rows = driver.find_elements(
                    By.CSS_SELECTOR,
                    "tr[class*='ProfileRow'], div[class*='search-result-item'], div[class*='profile-row'], div[class*='profile_row']",
                )

                # Filter out possible child elements, only keep main rows
                valid_rows = []
                for row in main_profile_rows:
                    # If element already processed, skip
                    element_id = row.id
                    if element_id in processed_elements:
                        continue

                    # Check if it contains enough content
                    text = row.text.strip()
                    if len(text) > 50:  # Reduced minimum text length
                        valid_rows.append(row)
                        processed_elements.add(element_id)

                print(f"Found {len(valid_rows)} valid candidate rows")

                # Extract information from valid rows
                for row in valid_rows:
                    candidate = extract_info_from_element(row, page_number)
                    if candidate:
                        candidates.append(candidate)

            except Exception as e:
                print(f"Error extracting data using ProfileRow selector: {str(e)}")

        # 3. If still not enough candidates, try extracting from page structure
        if len(candidates) < RESULTS_PER_PAGE and result_containers:
            print("Trying to extract candidates from page structure...")
            # Sort by text length, prioritize longer containers
            result_containers.sort(key=lambda x: x["text_length"], reverse=True)

            for container_info in result_containers[
                :3
            ]:  # Try first 3 most likely containers
                container = container_info["element"]
                try:
                    # Find possible candidate elements in container
                    potential_elements = container.find_elements(
                        By.CSS_SELECTOR,
                        "div[class*='item'], div[class*='row'], div[class*='card'], div[class*='profile']",
                    )

                    # Filter elements
                    for el in potential_elements:
                        # Check if already processed
                        element_id = el.id
                        if element_id in processed_elements:
                            continue

                        # Check if it's a valid element
                        text = el.text.strip()
                        if (
                            len(text) > 50 and "\n" in text
                        ):  # Reduced minimum text length
                            candidate = extract_info_from_element(el, page_number)
                            if candidate:
                                candidates.append(candidate)
                                processed_elements.add(element_id)

                                # Stop when reach per page limit
                                if len(candidates) >= RESULTS_PER_PAGE:
                                    break

                    if len(candidates) >= RESULTS_PER_PAGE:
                        break
                except Exception as e:
                    print(f"Error extracting information from container: {str(e)}")

    except Exception as e:
        print(f"Error extracting candidate information: {str(e)}")

    # Return extracted candidate information, up to per page limit
    candidates = candidates[:RESULTS_PER_PAGE]
    print(f"Extracted {len(candidates)} candidates from page {page_number+1}")
    return candidates


def find_pagination_elements(driver):
    """Find all possible pagination elements and return detailed information"""
    pagination_elements = []

    # Try multiple selectors to find pagination elements
    selectors = [
        ".pagination",
        "[class*='pagination']",
        "[role='navigation']",
        "nav",
        "[class*='nav']",
        "[class*='pager']",
        "[class*='pages']",
    ]

    # Find all possible containers containing pagination
    containers = []
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            containers.extend(elements)
        except Exception as e:
            print(f"Error finding pagination container ({selector}): {str(e)}")

    print(f"Found {len(containers)} possible pagination containers")

    # Extract buttons from each container
    for container in containers:
        try:
            # Find all buttons and links
            buttons = container.find_elements(By.TAG_NAME, "button")
            links = container.find_elements(By.TAG_NAME, "a")

            # Process buttons
            for button in buttons:
                try:
                    text = button.text.strip()
                    aria_label = button.get_attribute("aria-label") or ""
                    is_disabled = button.get_attribute("disabled") is not None
                    classname = button.get_attribute("class") or ""

                    # Determine button type
                    button_type = "unknown"
                    # Removed Chinese pagination text checks
                    if "next" in text.lower() or ">" in text or "→" in text:
                        button_type = "next"
                    elif "prev" in text.lower() or "<" in text or "←" in text:
                        button_type = "prev"
                    elif text.isdigit():
                        button_type = "page"

                    # If button has no text, try to determine based on aria-label and class
                    if not text and button_type == "unknown":
                        # Removed Chinese aria-label checks
                        if any(
                            term in aria_label.lower() for term in ["next", "next page"]
                        ):
                            button_type = "next"
                        elif any(
                            term in classname.lower() for term in ["next", "forward"]
                        ):
                            button_type = "next"

                    pagination_elements.append(
                        {
                            "element": button,
                            "text": text,
                            "type": button_type,
                            "is_disabled": is_disabled,
                            "element_type": "button",
                        }
                    )
                except Exception as e:
                    print(f"Error processing pagination button: {str(e)}")

            # Process links
            for link in links:
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href") or ""
                    aria_label = link.get_attribute("aria-label") or ""
                    classname = link.get_attribute("class") or ""

                    # Determine link type
                    link_type = "unknown"
                    # Removed Chinese pagination text checks
                    if "next" in text.lower() or ">" in text or "→" in text:
                        link_type = "next"
                    elif "prev" in text.lower() or "<" in text or "←" in text:
                        link_type = "prev"
                    elif text.isdigit():
                        link_type = "page"

                    # If link has no text, try to determine based on href, aria-label and class
                    if not text and link_type == "unknown":
                        if (
                            "page=" in href
                            and href.split("page=")[1].split("&")[0].isdigit()
                        ):
                            page_num = href.split("page=")[1].split("&")[0]
                            link_type = "page"
                            text = page_num
                        # Removed Chinese aria-label checks
                        elif any(
                            term in aria_label.lower() for term in ["next", "next page"]
                        ):
                            link_type = "next"
                        elif any(
                            term in classname.lower() for term in ["next", "forward"]
                        ):
                            link_type = "next"

                    pagination_elements.append(
                        {
                            "element": link,
                            "text": text,
                            "type": link_type,
                            "href": href,
                            "element_type": "link",
                        }
                    )
                except Exception as e:
                    print(f"Error processing pagination link: {str(e)}")

        except Exception as e:
            print(f"Error extracting pagination elements from container: {str(e)}")

    # Find next page button based on SVG icons (if still not found)
    if not any(el["type"] == "next" for el in pagination_elements):
        try:
            # Try to find possible elements containing arrow icons
            svg_containers = driver.find_elements(
                By.CSS_SELECTOR,
                "button svg, a svg, [class*='next'] svg, [class*='arrow'] svg",
            )

            for container in svg_containers:
                parent = container
                # Find parent 5 levels up, looking for clickable parent element
                for _ in range(5):
                    try:
                        parent = parent.find_element(By.XPATH, "./..")
                        if parent.tag_name in ["button", "a"]:
                            pagination_elements.append(
                                {
                                    "element": parent,
                                    "text": "SVG Icon",
                                    "type": "next",
                                    "element_type": parent.tag_name,
                                }
                            )
                            print("Found next page button based on SVG icon")
                            break
                    except:
                        break
        except Exception as e:
            print(f"Error finding SVG icon pagination button: {str(e)}")

    # Print found pagination elements information
    print(f"Found {len(pagination_elements)} pagination elements")
    for i, el in enumerate(pagination_elements):
        print(
            f"Pagination element {i+1}: type={el['type']}, text='{el['text']}', element type={el['element_type']}"
        )

    return pagination_elements


def navigate_to_page(driver, page_number):
    """Navigate to specified page number"""
    current_url = driver.current_url

    if page_number == 0:
        # First page, visit directly
        url = BASE_SEARCH_URL
        print(f"Navigating to page 1: {url}")
        driver.get(url)
    else:
        # Subsequent pages attempt to navigate using multiple methods
        print(f"Attempting to navigate to page {page_number+1}")

        # First check if already on the correct page
        if f"page={page_number+1}" in current_url:
            print(f"Already on page {page_number+1}, no navigation needed")
            return True

        # Attempt to navigate by clicking pagination button
        try:
            # Find and analyze all pagination elements
            pagination_elements = find_pagination_elements(driver)

            # First find the button for the specified page number
            page_button = None
            for el in pagination_elements:
                if el["type"] == "page" and el["text"] == str(page_number + 1):
                    page_button = el
                    print(f"Found button for page {page_number+1}")
                    break

            # If the specified page number is not found, try using the "Next page" button
            if not page_button and page_number > 0:
                # Find the "Next page" button
                next_buttons = [
                    el for el in pagination_elements if el["type"] == "next"
                ]

                if next_buttons:
                    # Prioritize using non-disabled buttons
                    active_next_buttons = [
                        btn for btn in next_buttons if not btn.get("is_disabled", False)
                    ]
                    if active_next_buttons:
                        page_button = active_next_buttons[0]
                        print(f"Found next page button: {page_button['text']}")
                    elif next_buttons:
                        page_button = next_buttons[0]
                        print(
                            f"Found next page button (possibly disabled): {page_button['text']}"
                        )

            # Attempt to click the found button
            if page_button:
                element = page_button["element"]
                # Scroll element into view
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                )
                time.sleep(2)

                try:
                    # Attempt to click the button
                    print(
                        f"Attempting to click pagination element: {page_button['text']}"
                    )
                    element.click()
                    print(f"Pagination element clicked")
                    # Wait for page to load
                    time.sleep(5)

                    # Check if URL changed
                    new_url = driver.current_url
                    if new_url != current_url:
                        print(f"URL changed: {new_url}")
                        return True
                    else:
                        print("URL did not change after click, trying JavaScript click")
                        # Attempt to use JavaScript click
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(5)

                        # Check URL again
                        if driver.current_url != current_url:
                            print(
                                f"URL changed after JavaScript click: {driver.current_url}"
                            )
                            return True

                except (
                    ElementNotInteractableException,
                    ElementClickInterceptedException,
                ) as e:
                    print(f"Direct click failed: {str(e)}, trying JavaScript click")
                    try:
                        # Attempt to use JavaScript click
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(5)

                        # Check if URL changed
                        if driver.current_url != current_url:
                            print(
                                f"URL changed after JavaScript click: {driver.current_url}"
                            )
                            return True
                    except Exception as js_e:
                        print(f"JavaScript click also failed: {str(js_e)}")

                except Exception as e:
                    print(f"Error clicking pagination element: {str(e)}")

        except Exception as e:
            print(f"Error navigating via pagination button: {str(e)}")

        # If click navigation fails, try direct URL navigation
        print("Navigation via button failed, attempting direct URL visit")
        url = get_search_url(page_number)
        driver.get(url)

    # Wait for page to load (increased wait time)
    print(f"Waiting for page {page_number+1} to load...")
    time.sleep(10)  # Wait 10 seconds first

    # Check if page content actually loaded
    try:
        # Wait for candidate information to appear on the page
        WebDriverWait(driver, 10).until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='profile'], [class*='candidate'], [class*='card'], [class*='result-item']",
                )
            )
            > 2
        )
    except TimeoutException:
        print(
            f"Timeout waiting for candidate information, attempting to refresh page..."
        )
        driver.refresh()
        time.sleep(10)

    # Scroll page to load all content
    print(f"Scrolling page {page_number+1} to load all content...")
    # Scroll multiple times to ensure all content is loaded
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(5):  # Increase scroll count
        scroll_point = total_height * (i + 1) / 6
        driver.execute_script(f"window.scrollTo(0, {scroll_point});")
        print(f"Scrolled to position: {scroll_point}")
        time.sleep(3)  # Wait a moment after each scroll

    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    # Check if the page actually displays search results
    profile_elements = driver.find_elements(
        By.CSS_SELECTOR,
        "[class*='profile'], [class*='candidate'], [class*='card'], [class*='result-item']",
    )
    print(f"Found {len(profile_elements)} potential candidate elements on the page")

    if len(profile_elements) < 3:
        print(
            "Warning: Too few candidate elements found, page may not have loaded correctly"
        )
        return False

    # Check again if the page contains expected content
    content = driver.page_source
    # Removed Chinese "没有结果" check
    if "No results" in content and page_number > 0:
        print(
            f"Warning: Page {page_number+1} shows no results, possibly requires re-login"
        )
        return False
    elif (
        len(content) < 5000 and page_number > 0
    ):  # Too little content might mean page didn't load
        print(
            f"Warning: Page {page_number+1} has unusually little content, possibly did not load correctly"
        )
        return False

    print(f"Page {page_number+1} loaded successfully")
    return True


def clean_data(candidates):
    """Clean and check data quality"""
    cleaned = []

    for candidate in candidates:
        # Ensure all necessary fields exist
        required_fields = [
            "name",
            "position",
            "github",
            "linkedin",
            "location",
            "experience",
            "education",
            "skills",
            "page",
        ]
        for field in required_fields:
            if field not in candidate:
                candidate[field] = "" if field != "skills" else []

        # Clean experience field, ensure format consistency
        if candidate["experience"]:
            # If experience field looks like it contains location information, fix it
            if any(
                city in candidate["experience"].lower()
                for city in [
                    "san francisco",
                    "san jose",
                    "oakland",
                    "berkeley",
                    "palo alto",
                    "mountain view",
                ]
            ):
                # Move experience value to location field
                if not candidate["location"]:
                    candidate["location"] = candidate["experience"]
                # Clear experience field
                candidate["experience"] = ""

        # If name field contains position information, fix it
        if candidate["name"] != "Unknown":
            job_indicators = [
                "engineer",
                "developer",
                "programmer",
                "lead",
                "senior",
                "software",
                "data scientist",
                "@",
            ]
            if any(
                indicator.lower() in candidate["name"].lower()
                for indicator in job_indicators
            ):
                # If name contains position information, possibly wrong, move to position field
                if not candidate["position"]:
                    candidate["position"] = candidate["name"]
                candidate["name"] = "Unknown"

        # Check position field whether it's actually name
        if candidate["position"] and candidate["name"] == "Unknown":
            # Name usually capitalized 2-3 word
            name_pattern = r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$"
            job_indicators = [
                "engineer",
                "developer",
                "scientist",
                "manager",
                "lead",
                "senior",
                "@",
            ]

            if re.match(name_pattern, candidate["position"]) and not any(
                ind.lower() in candidate["position"].lower() for ind in job_indicators
            ):
                candidate["name"] = candidate["position"]
                candidate["position"] = ""

        # For position field, ensure key position words capitalized
        if candidate["position"]:
            terms_to_capitalize = [
                "engineer",
                "developer",
                "scientist",
                "manager",
                "lead",
                "architect",
                "senior",
                "data",
            ]
            position = candidate["position"]
            for term in terms_to_capitalize:
                # Replace term with capitalized form
                pattern = re.compile(r"\b" + term + r"\b", re.IGNORECASE)
                position = pattern.sub(term.capitalize(), position)
            candidate["position"] = position.strip()

        # Filter out entries that seem like meaningless UI elements
        if (
            candidate["position"]
            in [
                "scale",
                "+1 more",
                "+2 more",
                "+3 more",
                "+6 more",
                "throughput",
                "preprocessing",
            ]
            or candidate["position"].lower() in ["python", "rust", "spark", "ai"]
            or re.match(r"^\d+% match$", candidate["position"])
        ):
            continue

        # Add to cleaned list
        cleaned.append(candidate)

    return cleaned


def merge_candidate_entries(entries):
    """Merge multiple candidate entries"""
    if not entries:
        return None

    # Use first entry as base
    merged = entries[0].copy()

    # Iterate over remaining entries to fill missing information
    for entry in entries[1:]:
        for field in [
            "name",
            "position",
            "location",
            "experience",
            "github",
            "linkedin",
            "education",
        ]:
            # If current field is empty but other entries have value, fill
            if (
                (not merged[field] or merged[field] == "Unknown")
                and entry[field]
                and entry[field] != "Unknown"
            ):
                merged[field] = entry[field]

        # Merge skills
        if entry["skills"]:
            merged["skills"] = sorted(list(set(merged["skills"] + entry["skills"])))

    # Ensure name is not "Unknown" if there are other identifier information
    if merged["name"] == "Unknown" and (merged["github"] or merged["linkedin"]):
        # Try extracting username from GitHub or LinkedIn URL
        if merged["github"]:
            github_username = merged["github"].split("/")[-1]
            if github_username and github_username != "":
                merged["name"] = github_username + " (from GitHub)"
        elif merged["linkedin"]:
            linkedin_parts = merged["linkedin"].split("/")
            if len(linkedin_parts) > 4:
                merged["name"] = linkedin_parts[-1] + " (from LinkedIn)"

    return merged


def remove_duplicates(candidates):
    """Remove duplicate candidate information and merge related entries"""
    print("Starting duplicate removal...")

    # First step: Group by GitHub and LinkedIn
    grouped_by_links = {}

    # First handle candidates with GitHub or LinkedIn
    for candidate in candidates:
        key = None
        if candidate["github"]:
            key = f"github:{candidate['github']}"
        elif candidate["linkedin"]:
            key = f"linkedin:{candidate['linkedin']}"

        if key:
            if key not in grouped_by_links:
                grouped_by_links[key] = []
            grouped_by_links[key].append(candidate)

    # Second step: Group remaining candidates by name
    name_grouped = {}
    for candidate in candidates:
        if (
            candidate["name"] != "Unknown"
            and not candidate["github"]
            and not candidate["linkedin"]
        ):
            key = f"name:{candidate['name']}"
            if key not in name_grouped:
                name_grouped[key] = []
            name_grouped[key].append(candidate)

    # Third step: Merge entries
    merged_candidates = []

    # Merge GitHub/LinkedIn groups
    for key, group in grouped_by_links.items():
        if len(group) == 1:
            merged_candidates.append(group[0])
        else:
            # Merge multiple entries
            merged = merge_candidate_entries(group)
            merged_candidates.append(merged)

    # Merge name groups
    for key, group in name_grouped.items():
        if len(group) == 1:
            # Check if this candidate already added via GitHub/LinkedIn
            name = group[0]["name"]
            is_duplicate = False
            for cand in merged_candidates:
                if cand["name"] == name:
                    is_duplicate = True
                    break

            if not is_duplicate:
                merged_candidates.append(group[0])
        else:
            # Merge multiple entries
            merged = merge_candidate_entries(group)

            # Check if already exists
            is_duplicate = False
            for cand in merged_candidates:
                if cand["name"] == merged["name"]:
                    is_duplicate = True
                    break

            if not is_duplicate:
                merged_candidates.append(merged)

    # Add remaining unclassified candidates (no GitHub, LinkedIn, name Unknown cases)
    position_grouped = {}
    for candidate in candidates:
        if (
            candidate["name"] == "Unknown"
            and not candidate["github"]
            and not candidate["linkedin"]
            and candidate["position"]
            and len(candidate["position"]) > 10
        ):

            # Use position and location as key
            key = f"pos:{candidate['position']}|loc:{candidate['location']}"
            if key not in position_grouped:
                position_grouped[key] = []
            position_grouped[key].append(candidate)

    # Merge position groups unique entries
    for key, group in position_grouped.items():
        if len(group) > 0:
            merged = merge_candidate_entries(group)

            # Check if duplicate with existing entries (based on position and location)
            is_duplicate = False
            for cand in merged_candidates:
                if (
                    cand["position"] == merged["position"]
                    and cand["location"] == merged["location"]
                    and cand["experience"] == merged["experience"]
                ):
                    is_duplicate = True
                    break

            if not is_duplicate:
                merged_candidates.append(merged)

    print(
        f"Before removing duplicates: {len(candidates)} records, After removing duplicates: {len(merged_candidates)} records"
    )
    return merged_candidates


def main():
    """Run main program, complete login and data scraping"""
    try:
        # Set up WebDriver, use the version that disables images
        driver = setup_driver_no_image()

        # Get login credentials
        email = input("Please enter your getprog.ai login email: ")
        password = getpass.getpass("Please enter your password: ")

        # Try to login
        login_success = login(driver, email, password)

        if not login_success:
            print("Login failed, please check credentials and try again.")
            driver.quit()
            return

        # Scrape multiple pages of candidate information
        all_candidates = []
        page_number = 0
        max_pages = 3  # We want exactly 3 pages
        max_retries = 3  # Maximum number of retries per page
        retry_delay = 10  # Seconds to wait between retries

        # Main scraping loop
        while page_number < max_pages:
            print(f"\n==== Processing page {page_number+1} ====")
            retry_count = 0
            page_success = False

            while retry_count < max_retries and not page_success:
                # Navigate to specified page
                page_loaded = navigate_to_page(driver, page_number)

                # If page load fails, session might have expired, try to login again
                if not page_loaded:
                    print("Page load failed, trying to login again...")
                    login_success = login(driver, email, password)
                    if login_success:
                        # Try navigation again
                        page_loaded = navigate_to_page(driver, page_number)
                        if not page_loaded:
                            print(
                                f"Still unable to load page {page_number+1} after re-login"
                            )
                            retry_count += 1
                            if retry_count < max_retries:
                                print(
                                    f"Retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})"
                                )
                                time.sleep(retry_delay)
                            continue
                    else:
                        print("Re-login failed, terminating program")
                        break

                # Extract candidate information
                candidates = extract_candidate_info_from_page(driver, page_number)

                # Check if we got enough candidates
                if (
                    len(candidates) >= RESULTS_PER_PAGE * 0.8
                ):  # At least 80% of expected candidates
                    page_success = True
                    # Clean data
                    candidates = clean_data(candidates)
                    # Add to total list
                    all_candidates.extend(candidates)
                    print(
                        f"Page {page_number+1}: Retrieved {len(candidates)} candidates, Total: {len(all_candidates)}"
                    )
                    page_number += 1
                else:
                    print(
                        f"Retrieved only {len(candidates)} candidates, expected {RESULTS_PER_PAGE}"
                    )
                    retry_count += 1
                    if retry_count < max_retries:
                        print(
                            f"Retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})"
                        )
                        time.sleep(retry_delay)
                    else:
                        print(
                            f"Failed to get enough candidates after {max_retries} attempts, moving to next page"
                        )
                        page_number += 1

            # Pause between pages to avoid too rapid requests
            if page_number < max_pages:
                print(
                    f"Waiting {retry_delay} seconds before loading page {page_number+1}..."
                )
                time.sleep(retry_delay)

        # Remove duplicates
        unique_candidates = remove_duplicates(all_candidates)

        # Save results to JSON file
        output_file = "getprog_candidates.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unique_candidates, f, ensure_ascii=False, indent=2)

        print(
            f"\nScraping complete! Retrieved {len(unique_candidates)} unique candidate profiles, saved to {output_file}"
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Close browser
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
