# AdNabu Test Store — QA Submission

> **Store URL:** https://adnabuteststore.myshopify.com  
> **Store Password:** AdNabuQA  
> **Automated scenario:** Search for a product → open product page → Add to Cart

---

## Table of Contents
1. [Task 1 — Test Design](#task-1--test-design)
2. [Task 2 — Test Automation](#task-2--test-automation)
3. [Setup & Run Guide](#setup--run-guide)
4. [Project Structure](#project-structure)
5. [Test Report](#test-report)

---

## Task 1 — Test Design

### A. Product Search — Test Cases

---

**TC-S-01 · Search with a valid keyword (Positive)**

| Field | Detail |
|---|---|
| **Precondition** | Store is unlocked; user is on the homepage |
| **Steps** | 1. Click the search icon  2. Type `shirt`  3. Press Enter |
| **Expected Result** | Search results page loads and displays ≥ 1 product card containing the word "shirt" in the title or description |

---

**TC-S-02 · Search with an invalid / non-existent keyword (Negative)**

| Field | Detail |
|---|---|
| **Precondition** | Store is unlocked; user is on the homepage |
| **Steps** | 1. Click the search icon  2. Type `xyznonexistentproduct123`  3. Press Enter |
| **Expected Result** | Results page shows 0 products and displays a "no results found" message; no error/crash occurs |

---

**TC-S-03 · Search with an empty query (Edge Case)**

| Field | Detail |
|---|---|
| **Precondition** | Store is unlocked; search field is visible |
| **Steps** | 1. Click the search icon  2. Leave the input blank  3. Press Enter |
| **Expected Result** | Either the form submission is prevented (field stays focused with a validation hint) OR the store shows all products / a default results page — the page must not throw a 4xx/5xx error |

---

**TC-S-04 · Search with special characters (Edge Case)**

| Field | Detail |
|---|---|
| **Precondition** | Store is unlocked; user is on the homepage |
| **Steps** | 1. Click the search icon  2. Type `<script>alert(1)</script>`  3. Press Enter |
| **Expected Result** | Input is safely escaped; no alert dialog fires; page displays 0 results or a "no results" message without exposing raw HTML |

---

**TC-S-05 · Search result card navigates to correct product (Positive)**

| Field | Detail |
|---|---|
| **Precondition** | A search for `shirt` returns results |
| **Steps** | 1. Perform a search for `shirt`  2. Click the first product card |
| **Expected Result** | Browser navigates to the product detail page (URL contains `/products/`); the page title matches the clicked product card's title |

---

**TC-S-06 · Search is case-insensitive (Positive)**

| Field | Detail |
|---|---|
| **Precondition** | Store is unlocked; searching `shirt` returns N results |
| **Steps** | 1. Search for `SHIRT`  2. Compare result count with a search for `shirt` |
| **Expected Result** | Both searches return the same set of products (result count is equal); case does not affect search results |

---

### B. Add to Cart — Test Cases

---

**TC-C-01 · Add a single in-stock product to cart (Positive)**

| Field | Detail |
|---|---|
| **Precondition** | User is on a product detail page for an in-stock item |
| **Steps** | 1. (Select a variant if required)  2. Click "Add to Cart" |
| **Expected Result** | Cart icon counter increments by 1; a success notification (e.g. slide-out drawer or toast) appears confirming the item was added |

---

**TC-C-02 · Add the same product multiple times (Positive)**

| Field | Detail |
|---|---|
| **Precondition** | User has already added the product once; still on the PDP |
| **Steps** | 1. Click "Add to Cart" a second time |
| **Expected Result** | Cart quantity for that line item increases to 2 (not a duplicate line); cart total updates accordingly |

---

**TC-C-03 · Attempt to add an out-of-stock product (Negative)**

| Field | Detail |
|---|---|
| **Precondition** | User is on a PDP where the item / selected variant is out of stock |
| **Steps** | 1. Observe the "Add to Cart" button |
| **Expected Result** | The "Add to Cart" button is disabled or replaced with "Sold Out"; clicking it (if somehow enabled) does not add anything to the cart |

---

**TC-C-04 · Add to cart without selecting a required variant (Negative)**

| Field | Detail |
|---|---|
| **Precondition** | Product has required variants (e.g. Size); none is selected |
| **Steps** | 1. Click "Add to Cart" without selecting any variant |
| **Expected Result** | An inline validation message prompts the user to select a variant (e.g. "Please select a size"); item is NOT added to the cart |

---

**TC-C-05 · Cart persists after page refresh (Edge Case)**

| Field | Detail |
|---|---|
| **Precondition** | User has added 1 item to the cart |
| **Steps** | 1. Add a product  2. Refresh the page (F5)  3. Check the cart icon counter |
| **Expected Result** | Cart count still shows 1 after page reload; navigating to `/cart` still shows the item (cart state is persisted via cookie/session) |

---

**TC-C-06 · View cart after adding a product (Positive)**

| Field | Detail |
|---|---|
| **Precondition** | At least one item has been added to the cart |
| **Steps** | 1. Click the cart icon in the header  2. Review the cart page / drawer |
| **Expected Result** | Cart displays the correct product name, variant (if applicable), quantity, unit price, and line-item total; a checkout CTA is visible |

---

## Task 2 — Test Automation

**Automated scenario:** Search for a product (`shirt`) → click the first result → add it to the cart → verify cart count > 0 and cart page contains a line item.

### Technology Stack

| Component | Choice |
|---|---|
| Language | Python 3.9+ |
| Test runner | pytest |
| Browser automation | Selenium 4 |
| Driver management | webdriver-manager (auto-downloads ChromeDriver) |
| Waits | `WebDriverWait` + `expected_conditions` — **no `time.sleep()`** |
| Reporting | pytest-html |

### Key Design Decisions

- **Modular helpers** — `open_search`, `enter_search_query`, `get_first_product_link`, `add_to_cart`, `get_cart_count` are standalone functions, making the test steps readable and reusable.
- **Multi-selector fallback lists** — Shopify themes vary; each helper tries several CSS selectors in order so the suite works across theme versions.
- **Fixture-scoped driver** — one browser instance per module; store password is entered once via `autouse` fixture.
- **Headless by default** — runs in CI without a display; remove `--headless=new` to watch the browser.

---

## Setup & Run Guide

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9 or higher |
| Google Chrome | Latest stable |
| pip | bundled with Python |

> ChromeDriver is **auto-downloaded** by `webdriver-manager` — no manual installation required.

### 1 · Clone the repository

```bash
git clone https://github.com/SimhadriPandurangaRao/AdNabuQAAssignment.git
cd AdNabuQAAssignment
```

### 2 · Create a virtual environment (recommended)

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3 · Install dependencies

```bash
pip install -r requirements.txt
```

### 4 · Run the tests

```bash
pytest
```

This will:
- Run all tests in `tests/`
- Print verbose output to the terminal
- Generate an HTML report at `reports/report.html`

#### Run with a visible browser (non-headless)

Open `tests/test_search_and_cart.py`, remove (or comment out) the line:

```python
chrome_options.add_argument("--headless=new")
```

then run `pytest` as normal.

#### Run a single test

```bash
pytest tests/test_search_and_cart.py::TestSearchAndAddToCart::test_add_to_cart_increases_count -v
```

---

## Project Structure

```
adnabu-qa/
├── tests/
│   └── test_search_and_cart.py   # Automated test suite
├── reports/
│   └── report.html               # Generated after running pytest
├── conftest.py                   # Pytest root config
├── pytest.ini                    # Pytest settings + HTML report path
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Test Report

After running `pytest`, open the generated report:

```bash
open reports/report.html        # macOS
xdg-open reports/report.html   # Linux
start reports/report.html      # Windows
```

The HTML report (via `pytest-html`) includes:
- Pass / Fail / Error status per test
- Duration of each test
- Full traceback for any failures
- Environment metadata (Python version, platform, pytest version)
