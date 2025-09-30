from selenium import webdriver
from selenium.webdriver.common.by import By
import time, os, re
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse

# 保存フォルダ（指定通り）
CSV_DIR = r"C:\Users\uenoshu\adidas\Sales BP&O - ドキュメント\Operation\★CategorySales\FTB\KAMO_Ranking\Kamo_Ranking_CSV"
DEBUG_DIR = r"C:\Users\uenoshu\adidas\Sales BP&O - ドキュメント\Operation\★CategorySales\FTB\KAMO_Ranking\Kamo_Ranking_debug"

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

url = "https://www.sskamo.co.jp/s/"
driver = webdriver.Chrome()
driver.get(url)
time.sleep(5)

today = datetime.now().strftime("%Y-%m-%d")
results = []

def extract_price(text):
    m = re.search(r"\d[\d,]*", text)
    if m:
        return int(m.group(0).replace(",", ""))
    return None

def extract_product_code(link):
    """商品URLから商品コードを抽出"""
    try:
        path = urlparse(link).path  # /s/g/gKKSENP104-NS/
        code = path.split("/")[-2]  # gKKSENP104-NS
        return code[1:] if code.startswith("g") else code
    except:
        return ""

def get_clean_name(item):
    try:
        alt_txt = item.find_element(By.TAG_NAME, "img").get_attribute("alt")
        if alt_txt and not re.fullmatch(r"\d+", alt_txt):
            return alt_txt.strip()
    except:
        pass
    for sel in [".silveregg-ranking--goods-name", ".item_name", ".goods-name", "[class*='name']"]:
        try:
            txt = item.find_element(By.CSS_SELECTOR, sel).text.strip()
            if txt and not re.fullmatch(r"\d+", txt):
                return txt
        except:
            pass
    return None

# optionリストを事前に取得
options = []
for opt in driver.find_elements(By.CSS_SELECTOR, '[name="silveregg-ranking-select"] option'):
    options.append({"value": opt.get_attribute("value"), "text": opt.text.strip()})

for option in options:
    category = option["text"]
    value = option["value"]

    print(f"\n=== {category} ===")

    # 毎回 select を取得して option をクリック
    select_box = driver.find_element(By.NAME, "silveregg-ranking-select")
    opt_elem = select_box.find_element(By.CSS_SELECTOR, f'option[value="{value}"]')
    opt_elem.click()
    time.sleep(3)

    block_id = f"js-silveregg-anchor-pc131--{value}"
    container = driver.execute_script("return arguments[0].nextElementSibling;",
                                      driver.find_element(By.ID, block_id))

    # debug HTML保存
    html = container.get_attribute("innerHTML")
    debug_file = os.path.join(DEBUG_DIR, f"debug_{value}.html")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(html or "")

    items = container.find_elements(By.CSS_SELECTOR, "li")
    print(f"{category}: {len(items)}件 (raw)")

    rank = 1
    for item in items:
        name = get_clean_name(item)
        if not name:
            continue

        brand = ""
        for sel in [".silveregg-ranking--goods-brand_name", ".brand_name", "[class*='brand']"]:
            try:
                brand = item.find_element(By.CSS_SELECTOR, sel).text.strip()
                if brand:
                    break
            except:
                pass

        price_text = ""
        for sel in [".silveregg-ranking--goods-price", ".price", "[class*='price']"]:
            try:
                price_text = item.find_element(By.CSS_SELECTOR, sel).text
                if price_text:
                    break
            except:
                pass
        price_value = extract_price(price_text if price_text else item.text)

        img = ""
        for img_el in item.find_elements(By.TAG_NAME, "img"):
            src = img_el.get_attribute("src")
            if src and "/img/goods/" in src:
                img = src
                break

        try:
            link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            link = ""

        # 商品コードはURLから抽出
        product_code = extract_product_code(link) if link else ""

        results.append({
            "data取得日": today,
            "カテゴリー": category,
            "順位": rank,
            "ブランド": brand,
            "商品名": name,
            "税込み価格": price_value,
            "画像URL": img,
            "URL": link,
            "商品コード": product_code
        })

        print(f"  {rank}位: {brand} {name} - {price_value}円 / {product_code}")
        rank += 1

driver.quit()

# CSV保存
df = pd.DataFrame(results)
csv_file = os.path.join(CSV_DIR, f"KAMO_Ranking_{today}.csv")
df.to_csv(csv_file, index=False, encoding="utf-8-sig")

print(f"\n✅ CSV保存完了: {csv_file}")
print(f"📝 debug HTML保存先: {DEBUG_DIR}")
