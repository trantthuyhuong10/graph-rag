import requests
from bs4 import BeautifulSoup
import time
import json

class Crawler:
    def __init__(self):
        self.base_url = "https://hanoipetadoption.com/vi/nhan-nuoi"
        self.delay=5
        self.headers={
            "User-Agent": 
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
        }
        self.session=requests.Session()
        self.session.headers.update(
            self.headers
        )
        self.visited_urls=set()
        self.pets=[]
        
    def fetch_page(self, url):
        try:
            if url in self.visited_urls:
                return None
            response=self.session.get(url, timeout=10)
            response.raise_for_status()
            self.visited_urls.add(url)
            time.sleep(self.delay)
            return response.text
        except Exception as e:
            print(e)
            return None
    
    def parse_page(self, html):
        soup = BeautifulSoup(html, "html.parser")
        return soup
    
    def extract_data(self, soup):
        pet_elements = soup.select(".caption-adoption")
        for pet in pet_elements:
            try:
                a_tag = pet.select_one("a.text-capitalize")
                href = a_tag["href"]
                name = a_tag.text.strip()
                item = {"name": name, "url": href}
                self.pets.append(item)
                print(item)
            except:
                continue
            
    def crawl(self, total=5):
        for page in range(1, total + 1):
            url = f"{self.base_url}?page={page}"
            html = self.fetch_page(url)
            if html:
                soup = self.parse_page(html)
                self.extract_data(soup)
            
    def save_json(self):
        with open("data/pet_details.json", "w", encoding="utf-8") as f:
            json.dump(self.pets, f, ensure_ascii=False, indent=2)
            
if __name__ == "__main__":
    crawler = Crawler()
    crawler.crawl()
    crawler.save_json()