from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://hanoipetadoption.com/vi/nhan-nuoi")

try:
    show_more_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.next.page-link"))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
    driver.execute_script("arguments[0].click();", show_more_button)
    time.sleep(2)
except:
    pass
    
pet_elements = driver.find_elements(By.CSS_SELECTOR, ".caption-adoption")
pets = []

print(len(pet_elements))
    
for pet in pet_elements:
    try:
        a_tag = pet.find_element(By.CSS_SELECTOR, "a.text-capitalize")
        href = a_tag.get_attribute("href")
        name = a_tag.text.strip()
            
        if name and href:
            pets.append({"name": name, "url": href})
    except:
        continue
        
with open("data/pet_details.json", "w", encoding="utf-8") as f:
        json.dump(pets, f, ensure_ascii=False, indent=2)
        
driver.quit()

