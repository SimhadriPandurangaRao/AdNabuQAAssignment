"""
Shopify Store - Search & Add to Cart Automation (v6 - With HTML Report)
URL  : https://adnabu-store-assignment1.myshopify.com
Pass : AdNabuQA

After every run an HTML report is saved to:
    reports/report_YYYY-MM-DD_HH-MM-SS.html
"""

import json
import os
import time
import traceback
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ── Constants ──────────────────────────────────────────────────────────────────
STORE_URL   = "https://adnabu-store-assignment1.myshopify.com"
STORE_PASS  = "AdNabuQA"
SEARCH_TERM = "board"
TIMEOUT     = 15
REPORTS_DIR = "reports"

# ── Confirmed selectors ────────────────────────────────────────────────────────
PRODUCT_LINK_SELECTORS = [
    "li.grid__item h3 a",
    ".card__heading a",
    "a[href*='/products/']",
]

ADD_TO_CART_SELECTORS = [
    "button[name='add']",
    "#AddToCart",
    "form[action*='/cart/add'] button[type='submit']",
    ".product-form__submit",
]


# ══════════════════════════════════════════════════════════════════════════════
# REPORT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class TestReport:
    """Collects step results and writes a self-contained HTML report."""

    def __init__(self, title: str):
        self.title      = title
        self.started_at = datetime.now()
        self.steps: list[dict] = []
        self._step_start: datetime | None = None

    # ── Step recording ────────────────────────────────────────────────────────
    def begin_step(self, name: str):
        self._step_start = datetime.now()
        self._current_step_name = name

    def pass_step(self, name: str = "", detail: str = ""):
        name = name or getattr(self, "_current_step_name", "")
        duration = self._elapsed()
        self.steps.append({"name": name, "status": "PASS", "detail": detail, "duration": duration})
        print(f"✅ {name}" + (f"  —  {detail}" if detail else ""))

    def fail_step(self, name: str = "", detail: str = ""):
        name = name or getattr(self, "_current_step_name", "")
        duration = self._elapsed()
        self.steps.append({"name": name, "status": "FAIL", "detail": detail, "duration": duration})
        print(f"❌ {name}" + (f"  —  {detail}" if detail else ""))

    def _elapsed(self) -> str:
        if self._step_start:
            ms = int((datetime.now() - self._step_start).total_seconds() * 1000)
            return f"{ms} ms"
        return "—"

    # ── Summary ───────────────────────────────────────────────────────────────
    @property
    def overall_status(self) -> str:
        return "FAIL" if any(s["status"] == "FAIL" for s in self.steps) else "PASS"

    @property
    def total_duration(self) -> str:
        ms = int((datetime.now() - self.started_at).total_seconds() * 1000)
        return f"{ms / 1000:.2f} s"

    # ── HTML writer ───────────────────────────────────────────────────────────
    def save(self) -> str:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp   = self.started_at.strftime("%Y-%m-%d_%H-%M-%S")
        filename    = f"report_{timestamp}.html"
        filepath    = os.path.join(REPORTS_DIR, filename)
        html        = self._render_html(timestamp)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n📄 Report saved → {os.path.abspath(filepath)}")
        return filepath

    def _render_html(self, timestamp: str) -> str:
        status_color = "#22c55e" if self.overall_status == "PASS" else "#ef4444"
        status_bg    = "#f0fdf4" if self.overall_status == "PASS" else "#fef2f2"

        rows = ""
        for i, step in enumerate(self.steps, 1):
            s = step["status"]
            icon      = "✅" if s == "PASS" else "❌"
            row_bg    = "#ffffff" if i % 2 == 0 else "#f9fafb"
            badge_col = "#16a34a" if s == "PASS" else "#dc2626"
            badge_bg  = "#dcfce7" if s == "PASS" else "#fee2e2"
            detail_html = f'<span style="color:#6b7280;font-size:12px;">{step["detail"]}</span>' if step["detail"] else ""
            rows += f"""
            <tr style="background:{row_bg};">
              <td style="padding:10px 14px;color:#6b7280;font-size:13px;">{i}</td>
              <td style="padding:10px 14px;font-weight:500;">{icon} {step['name']}</td>
              <td style="padding:10px 14px;">
                <span style="background:{badge_bg};color:{badge_col};padding:2px 10px;
                      border-radius:999px;font-size:12px;font-weight:700;">{s}</span>
              </td>
              <td style="padding:10px 14px;">{detail_html}</td>
              <td style="padding:10px 14px;color:#6b7280;font-size:13px;">{step['duration']}</td>
            </tr>"""

        passed = sum(1 for s in self.steps if s["status"] == "PASS")
        failed = len(self.steps) - passed

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Test Report — {timestamp}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f1f5f9; color: #1e293b; min-height: 100vh; padding: 32px 24px; }}
    .card {{ background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08);
             padding: 28px 32px; max-width: 960px; margin: 0 auto 24px; }}
    h1    {{ font-size: 22px; font-weight: 700; color: #0f172a; }}
    .meta {{ color: #64748b; font-size: 13px; margin-top: 6px; }}
    .badge-overall {{ display:inline-block; padding: 6px 20px; border-radius: 999px;
                      font-weight: 700; font-size: 15px; margin-top: 14px;
                      background: {status_bg}; color: {status_color};
                      border: 1px solid {status_color}; }}
    .stats {{ display: flex; gap: 20px; margin-top: 20px; }}
    .stat  {{ background: #f8fafc; border-radius: 8px; padding: 14px 20px; flex: 1; text-align: center; }}
    .stat-num  {{ font-size: 28px; font-weight: 800; }}
    .stat-label{{ font-size: 12px; color: #64748b; margin-top: 2px; }}
    table  {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    thead th {{ background: #1e293b; color: #fff; padding: 11px 14px;
                text-align: left; font-weight: 600; font-size: 13px; }}
    thead th:first-child {{ border-radius: 8px 0 0 0; }}
    thead th:last-child  {{ border-radius: 0 8px 0 0; }}
    tr:hover td {{ background: #f0f9ff !important; }}
    .footer {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 8px; }}
  </style>
</head>
<body>

  <div class="card">
    <h1>🧪 {self.title}</h1>
    <p class="meta">
      <strong>Store:</strong> {STORE_URL} &nbsp;|&nbsp;
      <strong>Search term:</strong> "{SEARCH_TERM}" &nbsp;|&nbsp;
      <strong>Run at:</strong> {self.started_at.strftime("%d %b %Y, %H:%M:%S")} &nbsp;|&nbsp;
      <strong>Duration:</strong> {self.total_duration}
    </p>
    <div class="badge-overall">Overall: {self.overall_status}</div>

    <div class="stats">
      <div class="stat">
        <div class="stat-num" style="color:#0f172a;">{len(self.steps)}</div>
        <div class="stat-label">Total Steps</div>
      </div>
      <div class="stat">
        <div class="stat-num" style="color:#16a34a;">{passed}</div>
        <div class="stat-label">Passed</div>
      </div>
      <div class="stat">
        <div class="stat-num" style="color:#dc2626;">{failed}</div>
        <div class="stat-label">Failed</div>
      </div>
      <div class="stat">
        <div class="stat-num" style="color:#2563eb;">{self.total_duration}</div>
        <div class="stat-label">Total Duration</div>
      </div>
    </div>
  </div>

  <div class="card">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Step</th>
          <th>Status</th>
          <th>Detail</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <p class="footer">Generated by Selenium Automation · {timestamp}</p>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ══════════════════════════════════════════════════════════════════════════════
def js_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def find_first(driver, selectors, wait_secs=2):
    for sel in selectors:
        try:
            el = WebDriverWait(driver, wait_secs).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            return el
        except TimeoutException:
            continue
    raise TimeoutException("No element found. Tried:\n" + "\n".join(f"  • {s}" for s in selectors))


def find_first_clickable(driver, selectors, wait_secs=TIMEOUT):
    for sel in selectors:
        try:
            el = WebDriverWait(driver, wait_secs).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            return el
        except TimeoutException:
            continue
    raise TimeoutException("No clickable element. Tried:\n" + "\n".join(f"  • {s}" for s in selectors))


def get_cart_item_count(driver):
    for sel in ["[data-cart-count]", ".cart-count", ".cart__count", ".cart-item-count"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text.isdigit():
                return int(text)
        except NoSuchElementException:
            continue
    return None


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ACTIONS
# ══════════════════════════════════════════════════════════════════════════════
def unlock_store(driver, wait, report: TestReport):
    report.begin_step("Unlock storefront")
    try:
        driver.get(f"{STORE_URL}/password")
        pwd = wait.until(EC.presence_of_element_located((By.ID, "password")))
        pwd.clear()
        pwd.send_keys(STORE_PASS)
        pwd.send_keys(Keys.RETURN)
        wait.until(lambda d: "/password" not in d.current_url)
        report.pass_step("Unlock storefront", f"Landed on: {driver.current_url}")
    except Exception as e:
        report.fail_step("Unlock storefront", str(e))
        raise


def search_for_product(driver, wait, term: str, report: TestReport):
    report.begin_step(f"Search for '{term}'")
    try:
        driver.get(f"{STORE_URL}/search?q={term}&type=product")
        wait.until(EC.url_contains("/search"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/products/']")))
        report.pass_step(f"Search for '{term}'", f"Results page loaded: {driver.current_url}")
    except Exception as e:
        report.fail_step(f"Search for '{term}'", str(e))
        raise


def select_first_product(driver, wait, report: TestReport) -> str:
    report.begin_step("Open first search result")
    try:
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        el    = find_first(driver, PRODUCT_LINK_SELECTORS)
        href  = el.get_attribute("href") or ""
        label = el.text.strip() or href.split("/products/")[-1].split("?")[0].replace("-", " ").title()
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        js_click(driver, el)
        wait.until(EC.url_contains("/products/"))
        report.pass_step("Open first search result", f"Product: '{label}'")
        return label
    except Exception as e:
        report.fail_step("Open first search result", str(e))
        raise


def select_all_variants(driver, wait, report: TestReport):
    report.begin_step("Select product variants")
    selected = []
    try:
        groups = driver.find_elements(
            By.CSS_SELECTOR,
            "fieldset.product-form__input, .product-form__option, [data-section-type] fieldset"
        )
        for group in groups:
            inputs    = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            available = [i for i in inputs if not i.get_attribute("disabled")]
            if available:
                js_click(driver, available[0])
                selected.append("radio")
    except Exception:
        pass

    try:
        from selenium.webdriver.support.ui import Select
        for dd in driver.find_elements(By.CSS_SELECTOR, "select[name='id'], .product-form select"):
            sel_obj = Select(dd)
            valid   = [o for o in sel_obj.options
                       if o.get_attribute("value") and "choose" not in o.text.lower()
                       and not o.get_attribute("disabled")]
            if valid:
                sel_obj.select_by_value(valid[0].get_attribute("value"))
                selected.append(f"dropdown='{valid[0].text}'")
    except Exception:
        pass

    detail = f"Selected: {', '.join(selected)}" if selected else "No variant groups found (single variant product)"
    report.pass_step("Select product variants", detail)

    try:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ", ".join(ADD_TO_CART_SELECTORS))))
    except TimeoutException:
        pass


def add_to_cart(driver, wait, report: TestReport):
    report.begin_step("Add product to cart")
    count_before = get_cart_item_count(driver)
    try:
        btn = find_first_clickable(driver, ADD_TO_CART_SELECTORS)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        js_click(driver, btn)

        confirmed_by = None

        # 1. Cart notification / drawer
        cart_ui = (
            ".cart-notification, .cart-notification-product, "
            "[id*='cart-notification'], [class*='cart-notification'], "
            ".cart-drawer.active, .cart-drawer[open], .cart-popup, "
            ".mini-cart--open, .ajax-cart--is-open"
        )
        try:
            WebDriverWait(driver, 8).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, cart_ui))
            )
            confirmed_by = "cart notification/drawer appeared"
        except TimeoutException:
            pass

        # 2. Redirect to /cart
        if not confirmed_by:
            try:
                WebDriverWait(driver, 5).until(EC.url_contains("/cart"))
                confirmed_by = "redirected to /cart"
            except TimeoutException:
                pass

        # 3. Cart count increased
        if not confirmed_by:
            try:
                def count_increased(d):
                    c = get_cart_item_count(d)
                    return c is not None and (c > (count_before or 0))
                WebDriverWait(driver, 5).until(count_increased)
                confirmed_by = f"cart count increased (was {count_before})"
            except TimeoutException:
                pass

        # 4. Button text changed
        if not confirmed_by:
            try:
                def btn_changed(d):
                    try:
                        b   = d.find_element(By.CSS_SELECTOR, ", ".join(ADD_TO_CART_SELECTORS))
                        txt = (b.text or b.get_attribute("value") or "").lower()
                        return any(w in txt for w in ["added", "in cart", "view cart"])
                    except Exception:
                        return False
                WebDriverWait(driver, 5).until(btn_changed)
                confirmed_by = "button text changed to Added/In cart"
            except TimeoutException:
                pass

        # 5. /cart.json API
        if not confirmed_by:
            try:
                current_url = driver.current_url
                driver.get(f"{STORE_URL}/cart.json")
                body      = driver.find_element(By.TAG_NAME, "pre").text
                cart_data = json.loads(body)
                driver.get(current_url)
                if cart_data.get("item_count", 0) > 0:
                    confirmed_by = f"/cart.json: {cart_data['item_count']} item(s)"
            except Exception:
                pass

        if confirmed_by:
            report.pass_step("Add product to cart", f"Confirmed via: {confirmed_by}")
        else:
            raise AssertionError("No confirmation detected across all 5 strategies.")

    except Exception as e:
        report.fail_step("Add product to cart", str(e))
        raise


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
def test_search_and_add_to_cart():
    report = TestReport("Search & Add to Cart — adnabu-store-assignment1.myshopify.com")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)
    wait   = WebDriverWait(driver, TIMEOUT)

    try:
        unlock_store(driver, wait, report)
        search_for_product(driver, wait, SEARCH_TERM, report)
        product_name = select_first_product(driver, wait, report)
        select_all_variants(driver, wait, report)
        add_to_cart(driver, wait, report)

        print(f"\n🎉 Test PASSED — '{product_name}' successfully added to cart.")

    except Exception as exc:
        print(f"\n❌ Test FAILED — {exc}")

    finally:
        driver.quit()
        report.save()   # ← always runs, pass or fail


if __name__ == "__main__":
    test_search_and_add_to_cart()