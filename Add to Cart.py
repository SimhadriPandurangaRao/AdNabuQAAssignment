"""
Shopify Store - Search & Add to Cart Automation (v5 - Final)
URL  : https://adnabu-store-assignment1.myshopify.com
Pass : AdNabuQA
"""

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

# ── Confirmed selectors (from debug runs) ──────────────────────────────────────
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



def js_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def find_first(driver, selectors, wait_secs=2):
    """Try selectors individually; return first match or raise TimeoutException."""
    for sel in selectors:
        try:
            el = WebDriverWait(driver, wait_secs).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            print(f"   ↳ matched: {sel!r}")
            return el
        except TimeoutException:
            continue
    raise TimeoutException("No element found. Tried:\n" + "\n".join(f"  • {s}" for s in selectors))


def find_first_clickable(driver, selectors, wait_secs=TIMEOUT):
    """Try selectors individually; return first clickable element."""
    for sel in selectors:
        try:
            el = WebDriverWait(driver, wait_secs).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            print(f"   ↳ matched: {sel!r}")
            return el
        except TimeoutException:
            continue
    raise TimeoutException("No clickable element. Tried:\n" + "\n".join(f"  • {s}" for s in selectors))


# ── Page Actions
def unlock_store(driver, wait):
    driver.get(f"{STORE_URL}/password")
    pwd = wait.until(EC.presence_of_element_located((By.ID, "password")))
    pwd.clear()
    pwd.send_keys(STORE_PASS)
    pwd.send_keys(Keys.RETURN)
    wait.until(lambda d: "/password" not in d.current_url)
    print(f"✅ Store unlocked  →  {driver.current_url}")


def search_for_product(driver, wait, term):
    """Navigate directly to search URL — no theme toggle needed."""
    driver.get(f"{STORE_URL}/search?q={term}&type=product")
    wait.until(EC.url_contains("/search"))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/products/']")))
    print(f"✅ Search results loaded for: '{term}'")


def select_first_product(driver, wait):
    """JS-click the first product card; return its name."""
    print("   Locating first product link...")
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    el = find_first(driver, PRODUCT_LINK_SELECTORS)
    href = el.get_attribute("href") or ""
    label = el.text.strip() or href.split("/products/")[-1].split("?")[0].replace("-", " ").title()

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    js_click(driver, el)

    wait.until(EC.url_contains("/products/"))
    print(f"✅ Product page opened: '{label}'")
    return label


def select_all_variants(driver, wait):
    """
    Select the first valid option for every variant group on the page.
    Covers: radio buttons (swatches), and <select> dropdowns.
    Waits briefly after each selection so the page can react.
    """
    print("   Selecting variants...")



    try:
        groups = driver.find_elements(
            By.CSS_SELECTOR,
            "fieldset.product-form__input, .product-form__option, [data-section-type] fieldset"
        )
        for group in groups:
            inputs = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            # Filter to only enabled options
            available = [i for i in inputs if not i.get_attribute("disabled")]
            if available:
                js_click(driver, available[0])
                print(f"   ↳ selected radio variant")
    except Exception as e:
        print(f"   ↳ radio variant step skipped: {e}")

    # ── <select> dropdowns
    try:
        from selenium.webdriver.support.ui import Select
        dropdowns = driver.find_elements(
            By.CSS_SELECTOR,
            "select[name='id'], .product-form select, select.product-form__input"
        )
        for dd in dropdowns:
            sel_obj = Select(dd)
            # Skip placeholder options (empty value or "Choose")
            valid_opts = [
                o for o in sel_obj.options
                if o.get_attribute("value") and "choose" not in o.text.lower()
                and not o.get_attribute("disabled")
            ]
            if valid_opts:
                sel_obj.select_by_value(valid_opts[0].get_attribute("value"))
                print(f"   ↳ selected dropdown variant: '{valid_opts[0].text}'")
    except Exception as e:
        print(f"   ↳ dropdown variant step skipped: {e}")

    # Wait for page to react to variant selection (price/button may update)
    try:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ", ".join(ADD_TO_CART_SELECTORS))))
    except TimeoutException:
        pass


def get_cart_item_count(driver):
    """Read the current cart item count from the header badge."""
    for sel in [
        "[data-cart-count]",
        ".cart-count",
        ".cart__count",
        ".cart-item-count",
        "a[href='/cart'] .count",
        ".header__icon--cart .visually-hidden",
    ]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text.isdigit():
                return int(text)
        except NoSuchElementException:
            continue
    return None


def add_to_cart(driver, wait):
    """Click Add to Cart and assert the cart registered the item."""
    print("   Locating Add to Cart button...")

    count_before = get_cart_item_count(driver)

    btn = find_first_clickable(driver, ADD_TO_CART_SELECTORS)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    js_click(driver, btn)

    print("   Waiting for cart confirmation...")

    # ── Strategy 1: any cart notification / drawer becomes visible ─────────────
    cart_ui_selectors = (
        ".cart-notification, "
        ".cart-notification-product, "
        "[id*='cart-notification'], "
        "[class*='cart-notification'], "
        ".cart-drawer.active, "
        ".cart-drawer[open], "
        ".cart-popup, "
        ".mini-cart--open, "
        ".ajax-cart--is-open"
    )
    try:
        WebDriverWait(driver, 8).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, cart_ui_selectors))
        )
        print("   ↳ confirmed: cart notification/drawer appeared")
        return
    except TimeoutException:
        pass

    # ── Strategy 2: redirected to /cart page ──────────────────────────────────
    try:
        WebDriverWait(driver, 5).until(EC.url_contains("/cart"))
        print("   ↳ confirmed: redirected to /cart")
        return
    except TimeoutException:
        pass

    # ── Strategy 3: cart count increased ─────────────────────────────────────
    try:
        def count_increased(d):
            current = get_cart_item_count(d)
            if current is None:
                return False
            if count_before is None:
                return current > 0
            return current > count_before

        WebDriverWait(driver, 5).until(count_increased)
        print("   ↳ confirmed: cart count increased")
        return
    except TimeoutException:
        pass

    # ── Strategy 4: button text changed (e.g. "Added!" or "In cart") ─────────
    try:
        def btn_text_changed(d):
            try:
                b = d.find_element(By.CSS_SELECTOR, ", ".join(ADD_TO_CART_SELECTORS))
                txt = (b.text or b.get_attribute("value") or "").lower()
                return any(word in txt for word in ["added", "in cart", "view cart"])
            except Exception:
                return False

        WebDriverWait(driver, 5).until(btn_text_changed)
        print("   ↳ confirmed: button text changed to 'Added/In cart'")
        return
    except TimeoutException:
        pass

    # ── Strategy 5: verify via /cart.json (headless cart API) ────────────────
    try:
        current_url = driver.current_url
        driver.get(f"{STORE_URL}/cart.json")
        import json
        body = driver.find_element(By.TAG_NAME, "pre").text
        cart_data = json.loads(body)
        item_count = cart_data.get("item_count", 0)
        driver.get(current_url)   # navigate back
        if item_count > 0:
            print(f"   ↳ confirmed: /cart.json shows {item_count} item(s)")
            return
    except Exception:
        pass

    raise AssertionError(
        "Add to Cart clicked but no confirmation detected across all 5 strategies.\n"
        "The variant may still be unselected, or the button may be disabled."
    )


# ── Orchestrator ───────────────────────────────────────────────────────────────
def test_search_and_add_to_cart():
    """
    E2E: unlock → search 'board' → open first result
         → select all variants → add to cart → assert success.
    """
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)
    wait   = WebDriverWait(driver, TIMEOUT)

    try:
        unlock_store(driver, wait)
        search_for_product(driver, wait, SEARCH_TERM)
        product_name = select_first_product(driver, wait)
        select_all_variants(driver, wait)
        add_to_cart(driver, wait)
        print(f"\n🎉 Test PASSED — '{product_name}' successfully added to cart.")

    except Exception as exc:
        print(f"\n❌ Test FAILED — {exc}")
        raise

    finally:
        driver.quit()


if __name__ == "__main__":
    test_search_and_add_to_cart()