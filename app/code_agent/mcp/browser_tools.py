import json
import time
from typing import Any, Dict
from langsmith import traceable
from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

mcp = FastMCP()

@traceable(run_type="tool", name="search in browser")
@mcp.tool(name="web_search", description="search query word in duckduckgo")
def search_in_duckduckgo(query: str, max_pages: int) -> Dict[str, Any]:
    driver = webdriver.Chrome()
    try:
        driver.get("https://html.duckduckgo.com/html/")

        text_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

        text_box.send_keys(query)
        text_box.submit()

        all_results = []

        for page in range(max_pages):
            # Wait for results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result"))
            )

            print(f"Parsing page {page + 1}")

            results = driver.find_elements(By.CLASS_NAME, "result")

            for result in results:
                try:
                    title = result.find_element(
                        By.CLASS_NAME,
                        "result__title"
                    ).text

                    url = result.find_element(
                        By.TAG_NAME,
                        "a"
                    ).get_attribute("href")

                    snippet = ""

                    try:
                        snippet = result.find_element(
                            By.CLASS_NAME,
                            "result__snippet"
                        ).text
                    except:
                        pass

                    all_results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })

                except Exception as e:
                    print("Parse result failed:", e)
            # Try to find next page button
            try:
                next_button = driver.find_element(
                    By.XPATH,
                    "//input[@type='submit' and contains(@value, 'Next')]"
                )

                # Scroll to button
                driver.execute_script(
                    "arguments[0].scrollIntoView();",
                    next_button
                )

                time.sleep(1)

                next_button.click()

                time.sleep(2)

            except Exception:
                print("No next page found.")
                break

        return {
            "query": query,
            "raw": all_results,
            "text": json.dumps(all_results, ensure_ascii=False)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    mcp.run(transport="stdio")
    # print(search_in_duckduckgo("today is weather", 3))