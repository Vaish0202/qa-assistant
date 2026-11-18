"""
Synthetic failure generator: builds realistic failing tests by "injecting" a
known fault into a template, so the label is known for certain.

Labeling rule (same as the rest of the project):
    bug              the APPLICATION is wrong: the developer must fix app code
    failed_testcase  the TEST is wrong: wrong locator, missing wait, wrong
                     test data, broken fixture/mock, or the test environment
                     (e.g. database not running) - the QA engineer must fix it

Each scenario is a small function that picks random names, values, URLs and
line numbers, so no two generated cases are the same. Some scenarios are
deliberately "hard": the surface error points one way while the real cause
is the other (e.g. a timeout caused by the app returning a 500).

Usage (from the project root):
    python -m evaluation.datasets.inject --per-stratum 12 --dataset v1
    python -m evaluation.datasets.inject --per-stratum 2 --dry-run   # print samples

Then:
    python -m evaluation.datasets.split --dataset v1
    python -m evaluation.datasets.validate --dataset v1
"""
import argparse
import random
import textwrap
from collections import defaultdict

from evaluation.datasets import dataset_io

# --------------------------------------------------------------------- pools
PAGES = [("login", "Login"), ("checkout", "Checkout"), ("profile", "Profile"),
         ("cart", "Cart"), ("signup", "Sign up"), ("dashboard", "Dashboard"),
         ("orders", "Orders"), ("settings", "Settings"), ("search", "Search"),
         ("invoice", "Invoice")]
ELEMENTS = ["submit-btn", "email-input", "password-input", "place-order",
            "save-changes", "add-to-cart", "search-box", "apply-coupon",
            "confirm-btn", "username", "qty-input", "next-step"]
RESOURCES = [("users", "user", ["id", "email", "name", "role"]),
             ("orders", "order", ["id", "total", "status", "items"]),
             ("products", "product", ["id", "price", "stock", "sku"]),
             ("invoices", "invoice", ["id", "amount", "currency", "due_date"]),
             ("payments", "payment", ["id", "amount", "status", "method"]),
             ("tickets", "ticket", ["id", "title", "priority", "assignee"])]
TABLES = [("User", "users", "email"), ("Order", "orders", "order_ref"),
          ("Product", "products", "sku"), ("Invoice", "invoices", "number"),
          ("Account", "accounts", "username"), ("Coupon", "coupons", "code")]
HOSTS = ["staging.shop.local", "qa.app.internal", "localhost:8000",
         "test-env.example.com", "127.0.0.1:5000"]
UNIT_FUNCS = [("calculate_discount", "pricing", "price, percent"),
              ("calculate_tax", "billing", "amount, rate"),
              ("convert_currency", "fx", "amount, rate"),
              ("apply_coupon", "cart", "total, coupon"),
              ("compute_shipping", "shipping", "weight, zone"),
              ("prorate_refund", "refunds", "amount, days_used")]


def dedent(s):
    return textwrap.dedent(s).strip("\n")


def line(rng):
    return rng.randint(12, 140)


# ----------------------------------------------------------------- registry
SCENARIOS = defaultdict(list)   # (framework, label) -> [(name, fn)]


def scenario(framework, label, name):
    def register(fn):
        SCENARIOS[(framework, label)].append((name, fn))
        return fn
    return register

# ================================================================ SELENIUM
@scenario("selenium", "failed_testcase", "wrong_locator")
def sel_wrong_locator(rng):
    page, title = rng.choice(PAGES)
    real = rng.choice(ELEMENTS)
    typo = rng.choice([real.replace("-", "_"), real + "-button", "btn-" + real, real[:-1]])
    n = line(rng)
    return dict(
        description=f"Click {real.replace('-', ' ')} on the {title} page",
        code=dedent(f"""
            def test_{page}_{real.replace('-', '_')}(driver):
                driver.get("https://{rng.choice(HOSTS)}/{page}")
                driver.find_element(By.ID, "{typo}").click()
                assert "{title}" in driver.title
            """),
        log=dedent(f"""
            selenium.common.exceptions.NoSuchElementException: Message: no such element: Unable to locate element: {{"method":"css selector","selector":"[id="{typo}"]"}}
              (Session info: chrome=120.0.6099.109)
            FAILED tests/ui/test_{page}.py::test_{page}_{real.replace('-', '_')}
            """),
        stacktrace=dedent(f"""
            Traceback (most recent call last):
              File "tests/ui/test_{page}.py", line {n}, in test_{page}_{real.replace('-', '_')}
                driver.find_element(By.ID, "{typo}").click()
            Stacktrace:
            #0 0x55d1c2a4e5e3 <unknown>
            """),
    )


@scenario("selenium", "failed_testcase", "missing_wait")
def sel_missing_wait(rng):
    page, title = rng.choice(PAGES)
    el = rng.choice(ELEMENTS)
    n = line(rng)
    exc = rng.choice(["ElementNotInteractableException: Message: element not interactable",
                      "StaleElementReferenceException: Message: stale element reference: stale element not found",
                      "ElementClickInterceptedException: Message: element click intercepted: Element is not clickable at point (412, 380). Other element would receive the click: <div class=\"spinner-overlay\"></div>"])
    return dict(
        description=f"Submit the {title} form after it finishes loading",
        code=dedent(f"""
            def test_{page}_submit(driver):
                driver.get("https://{rng.choice(HOSTS)}/{page}")
                time.sleep(0.5)
                button = driver.find_element(By.ID, "{el}")
                button.click()
                assert driver.find_element(By.CLASS_NAME, "toast-success").is_displayed()
            """),
        log=f"selenium.common.exceptions.{exc}\nFAILED tests/ui/test_{page}.py::test_{page}_submit"
            + ("\nNote: test passes when re-run locally" if rng.random() < 0.5 else ""),
        stacktrace=dedent(f"""
            Traceback (most recent call last):
              File "tests/ui/test_{page}.py", line {n}, in test_{page}_submit
                button.click()
            """),
    )


@scenario("selenium", "failed_testcase", "outdated_expected_text")
def sel_outdated_text(rng):
    page, title = rng.choice(PAGES)
    old, new = rng.choice([("Sign In", "Log in"), ("Add to Basket", "Add to cart"),
                           ("Submit", "Save"), ("Proceed", "Continue"),
                           ("My Account", "Account")])
    n = line(rng)
    return dict(
        description=f"Button label on {title} page (copy was updated in the last release notes)",
        code=dedent(f"""
            def test_{page}_button_label(driver):
                driver.get("https://{rng.choice(HOSTS)}/{page}")
                label = driver.find_element(By.CSS_SELECTOR, "button.primary").text
                assert label == "{old}"
            """),
        log=dedent(f"""
            E       AssertionError: assert '{new}' == '{old}'
            E         - {old}
            E         + {new}
            FAILED tests/ui/test_{page}.py::test_{page}_button_label
            """),
        stacktrace=f'  File "tests/ui/test_{page}.py", line {n}, in test_{page}_button_label',
    )


@scenario("selenium", "bug", "server_error_page")
def sel_server_error(rng):
    page, title = rng.choice(PAGES)
    n = line(rng)
    return dict(
        description=f"{title} page should load for a logged-in user",
        code=dedent(f"""
            def test_{page}_loads(logged_in_driver):
                logged_in_driver.get("https://{rng.choice(HOSTS)}/{page}")
                assert "{title}" in logged_in_driver.title
            """),
        log=dedent(f"""
            E       AssertionError: assert '{title}' in '500 Internal Server Error'
            E        +  where '500 Internal Server Error' = <selenium.webdriver.chrome.webdriver.WebDriver>.title
            Browser console: GET https://app/api/{page} 500 (Internal Server Error)
            FAILED tests/ui/test_{page}.py::test_{page}_loads
            """),
        stacktrace=f'  File "tests/ui/test_{page}.py", line {n}, in test_{page}_loads',
    )


@scenario("selenium", "bug", "wrong_value_displayed")
def sel_wrong_value(rng):
    qty = rng.randint(2, 5)
    price = rng.choice([19.99, 24.50, 7.25, 120.00, 49.00])
    expected = round(qty * price, 2)
    shown = rng.choice([price, round(expected * 1.1, 2), round((qty - 1) * price, 2)])
    n = line(rng)
    return dict(
        description=f"Cart total should equal quantity x unit price ({qty} x {price})",
        code=dedent(f"""
            def test_cart_total(driver, product_page):
                product_page.set_quantity({qty})
                product_page.add_to_cart()
                total = driver.find_element(By.ID, "cart-total").text
                assert total == "${expected:.2f}"
            """),
        log=dedent(f"""
            E       AssertionError: assert '${shown:.2f}' == '${expected:.2f}'
            Cart shows wrong total after quantity update
            FAILED tests/ui/test_cart.py::test_cart_total
            """),
        stacktrace=f'  File "tests/ui/test_cart.py", line {n}, in test_cart_total',
    )


@scenario("selenium", "bug", "timeout_hides_app_error")   # hard: looks like a test issue
def sel_timeout_app_error(rng):
    page, title = rng.choice(PAGES)
    n = line(rng)
    return dict(
        description=f"Confirmation message appears after saving on the {title} page",
        code=dedent(f"""
            def test_{page}_save(driver):
                driver.get("https://{rng.choice(HOSTS)}/{page}")
                driver.find_element(By.ID, "save-changes").click()
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "toast-success")))
            """),
        log=dedent(f"""
            selenium.common.exceptions.TimeoutException: Message:
            Browser console: POST https://app/api/{page} 500 (Internal Server Error)
            Browser console: Uncaught (in promise) TypeError: Cannot read properties of null (reading 'id')
            FAILED tests/ui/test_{page}.py::test_{page}_save
            """),
        stacktrace=f'  File "tests/ui/test_{page}.py", line {n}, in test_{page}_save',
    )

# ============================================================== PLAYWRIGHT
@scenario("playwright", "failed_testcase", "strict_mode_violation")
def pw_strict(rng):
    page, title = rng.choice(PAGES)
    text = rng.choice(["Save", "Delete", "Edit", "Submit", "Remove"])
    count = rng.randint(2, 4)
    n = line(rng)
    return dict(
        description=f"Click the {text} button on the {title} page",
        code=dedent(f"""
            def test_{page}_{text.lower()}(page: Page):
                page.goto("https://{rng.choice(HOSTS)}/{page}")
                page.get_by_role("button", name="{text}").click()
                expect(page.get_by_text("{text}d successfully")).to_be_visible()
            """),
        log=dedent(f"""
            playwright._impl._errors.Error: Locator.click: Error: strict mode violation: get_by_role("button", name="{text}") resolved to {count} elements:
                1) <button class="btn">{text}</button> aka get_by_role("row").first.get_by_role("button", name="{text}")
                2) <button class="btn">{text}</button> aka get_by_role("row").nth(1).get_by_role("button", name="{text}")
            FAILED tests/e2e/test_{page}.py::test_{page}_{text.lower()}[chromium]
            """),
        stacktrace=f'  File "tests/e2e/test_{page}.py", line {n}, in test_{page}_{text.lower()}',
    )


@scenario("playwright", "failed_testcase", "wrong_selector_timeout")
def pw_wrong_selector(rng):
    page, title = rng.choice(PAGES)
    real = rng.choice(ELEMENTS)
    wrong = rng.choice([f"#{real}-old", f"[data-test='{real}']", f".{real.replace('-', '_')}"])
    n = line(rng)
    return dict(
        description=f"Fill and submit the {title} form",
        code=dedent(f"""
            def test_{page}_form(page: Page):
                page.goto("https://{rng.choice(HOSTS)}/{page}")
                page.locator("{wrong}").fill("qa-user@example.com")
                page.get_by_role("button", name="Continue").click()
            """),
        log=dedent(f"""
            playwright._impl._errors.TimeoutError: Locator.fill: Timeout 30000ms exceeded.
            Call log:
              - waiting for locator("{wrong}")
            FAILED tests/e2e/test_{page}.py::test_{page}_form[chromium]
            """),
        stacktrace=f'  File "tests/e2e/test_{page}.py", line {n}, in test_{page}_form',
    )


@scenario("playwright", "failed_testcase", "missing_await_navigation")
def pw_race(rng):
    page, title = rng.choice(PAGES)
    n = line(rng)
    return dict(
        description=f"After login the user lands on the {title} page",
        code=dedent(f"""
            def test_login_redirects_to_{page}(page: Page):
                page.goto("https://{rng.choice(HOSTS)}/login")
                page.fill("#email", "qa@example.com")
                page.fill("#password", "Secret123!")
                page.click("#submit-btn")
                assert page.url.endswith("/{page}")
            """),
        log=dedent(f"""
            E       AssertionError: assert False
            E        +  where False = <built-in method endswith of str object>('/{page}')
            E        +    where 'https://app/login' = <Page url='https://app/login'>.url
            Flaky: passed 3 of 5 runs in CI
            FAILED tests/e2e/test_auth.py::test_login_redirects_to_{page}[webkit]
            """),
        stacktrace=f'  File "tests/e2e/test_auth.py", line {n}, in test_login_redirects_to_{page}',
    )


@scenario("playwright", "bug", "error_redirect")
def pw_error_redirect(rng):
    page, title = rng.choice(PAGES)
    n = line(rng)
    return dict(
        description=f"Opening {title} should keep the user on /{page}",
        code=dedent(f"""
            def test_open_{page}(page: Page):
                page.goto("https://{rng.choice(HOSTS)}/{page}")
                expect(page).to_have_url(re.compile(".*/{page}"))
            """),
        log=dedent(f"""
            AssertionError: Page URL expected to match regex '.*/{page}'
            Actual value: https://app/error?code=500
            Call log:
              - waiting for navigation until "load"
              - navigated to "https://app/error?code=500"
            FAILED tests/e2e/test_{page}.py::test_open_{page}[chromium]
            """),
        stacktrace=f'  File "tests/e2e/test_{page}.py", line {n}, in test_open_{page}',
    )


@scenario("playwright", "bug", "nan_in_ui")
def pw_nan(rng):
    field = rng.choice(["Order total", "Subtotal", "Tax", "Balance", "Discount"])
    expected = f"${rng.randint(10, 400)}.{rng.randint(0, 99):02d}"
    got = rng.choice(["$NaN", "$undefined", "$0.00", "null"])
    n = line(rng)
    return dict(
        description=f"{field} is shown with the correct value",
        code=dedent(f"""
            def test_{field.lower().replace(' ', '_')}_shown(page: Page, seeded_order):
                page.goto(f"https://{rng.choice(HOSTS)}/orders/{{seeded_order.id}}")
                expect(page.get_by_test_id("{field.lower().replace(' ', '-')}")).to_have_text("{expected}")
            """),
        log=dedent(f"""
            AssertionError: Locator expected to have text '{expected}'
            Actual value: {got}
            Browser console: [error] Failed to format amount: received undefined
            FAILED tests/e2e/test_orders.py::test_{field.lower().replace(' ', '_')}_shown[firefox]
            """),
        stacktrace=f'  File "tests/e2e/test_orders.py", line {n}',
    )


@scenario("playwright", "bug", "api_500_during_flow")
def pw_api_500(rng):
    plural, single, _ = rng.choice(RESOURCES)
    n = line(rng)
    return dict(
        description=f"Creating a {single} from the UI shows it in the list",
        code=dedent(f"""
            def test_create_{single}(page: Page):
                page.goto("https://{rng.choice(HOSTS)}/{plural}/new")
                page.get_by_label("Name").fill("Automation {single} {rng.randint(100, 999)}")
                with page.expect_response("**/api/{plural}") as resp:
                    page.get_by_role("button", name="Create").click()
                assert resp.value.status == 201
            """),
        log=dedent(f"""
            E       assert 500 == 201
            E        +  where 500 = <Response url='https://app/api/{plural}' request=<Request method='POST'>>.status
            Response body: {{"error": "Internal Server Error", "trace_id": "{rng.randrange(16**8):08x}"}}
            FAILED tests/e2e/test_{plural}.py::test_create_{single}[chromium]
            """),
        stacktrace=f'  File "tests/e2e/test_{plural}.py", line {n}, in test_create_{single}',
    )

# ===================================================================== API
@scenario("api", "bug", "server_error")
def api_500(rng):
    plural, single, fields = rng.choice(RESOURCES)
    rid = rng.randint(1, 9999)
    n = line(rng)
    return dict(
        description=f"GET /{plural}/{{id}} returns the {single}",
        code=dedent(f"""
            def test_get_{single}(api_client, auth_headers):
                r = requests.get(f"{{BASE_URL}}/api/{plural}/{rid}", headers=auth_headers)
                assert r.status_code == 200
                assert r.json()["id"] == {rid}
            """),
        log=dedent(f"""
            E       assert 500 == 200
            E        +  where 500 = <Response [500]>.status_code
            requests.exceptions.HTTPError: 500 Server Error: Internal Server Error for url: http://{rng.choice(HOSTS)}/api/{plural}/{rid}
            FAILED tests/api/test_{plural}.py::test_get_{single}
            """),
        stacktrace=f'  File "tests/api/test_{plural}.py", line {n}, in test_get_{single}',
    )


@scenario("api", "bug", "changed_response_field")
def api_changed_field(rng):
    plural, single, fields = rng.choice(RESOURCES)
    field = rng.choice(fields[1:])
    renamed = rng.choice([f"{single}_{field}", field.upper(), field + "_value", "".join(
        w.capitalize() if i else w for i, w in enumerate(field.split("_")))])
    if renamed == field:
        renamed = field + "_v2"
    n = line(rng)
    return dict(
        description=f"Response of GET /{plural} contains '{field}' as documented in the API spec",
        code=dedent(f"""
            def test_list_{plural}_schema(api_client):
                r = api_client.get("/api/{plural}?limit=5")
                assert r.status_code == 200
                for item in r.json()["data"]:
                    assert item["{field}"] is not None
            """),
        log=dedent(f"""
            E       KeyError: '{field}'
            Response sample: {{"id": {rng.randint(1, 500)}, "{renamed}": ...}}
            API changelog: no change to '{field}' announced for this release
            FAILED tests/api/test_{plural}.py::test_list_{plural}_schema
            """),
        stacktrace=f'  File "tests/api/test_{plural}.py", line {n}, in test_list_{plural}_schema',
    )


@scenario("api", "bug", "validation_not_enforced")
def api_validation(rng):
    plural, single, fields = rng.choice(RESOURCES)
    bad = rng.choice([('"amount": -50', "negative amount"), ('"email": "not-an-email"', "invalid email"),
                      ('"quantity": 0', "zero quantity"), ('"price": "abc"', "non-numeric price")])
    n = line(rng)
    return dict(
        description=f"POST /{plural} must reject a {bad[1]} with 422",
        code=dedent(f"""
            def test_create_{single}_rejects_{bad[1].replace(' ', '_').replace('-', '_')}(api_client):
                r = api_client.post("/api/{plural}", json={{{bad[0]}}})
                assert r.status_code == 422
            """),
        log=dedent(f"""
            E       assert 201 == 422
            E        +  where 201 = <Response [201]>.status_code
            FAILED tests/api/test_{plural}.py::test_create_{single}_rejects_{bad[1].replace(' ', '_').replace('-', '_')}
            """),
        stacktrace=f'  File "tests/api/test_{plural}.py", line {n}',
    )


@scenario("api", "failed_testcase", "wrong_endpoint_in_test")
def api_wrong_path(rng):
    plural, single, _ = rng.choice(RESOURCES)
    wrong = rng.choice([single, plural + "s", f"v1/{plural}", plural.rstrip("s") + "-list"])
    n = line(rng)
    return dict(
        description=f"List {plural}",
        code=dedent(f"""
            def test_list_{plural}(api_client):
                r = api_client.get("/api/{wrong}")
                assert r.status_code == 200
            """),
        log=dedent(f"""
            E       assert 404 == 200
            E        +  where 404 = <Response [404]>.status_code
            Response body: {{"detail": "Not Found"}}
            FAILED tests/api/test_{plural}.py::test_list_{plural}
            """),
        stacktrace=f'  File "tests/api/test_{plural}.py", line {n}, in test_list_{plural}',
    )


@scenario("api", "failed_testcase", "missing_auth_header")
def api_missing_auth(rng):
    plural, single, _ = rng.choice(RESOURCES)
    n = line(rng)
    return dict(
        description=f"Authenticated user can list {plural}",
        code=dedent(f"""
            def test_user_lists_{plural}(base_url):
                r = requests.get(f"{{base_url}}/api/{plural}")
                assert r.status_code == 200
            """),
        log=dedent(f"""
            E       assert 401 == 200
            E        +  where 401 = <Response [401]>.status_code
            Response body: {{"detail": "Not authenticated"}}
            FAILED tests/api/test_{plural}.py::test_user_lists_{plural}
            """),
        stacktrace=f'  File "tests/api/test_{plural}.py", line {n}, in test_user_lists_{plural}',
    )


@scenario("api", "failed_testcase", "stale_test_data")
def api_stale_data(rng):
    plural, single, _ = rng.choice(RESOURCES)
    rid = rng.randint(1000, 99999)
    n = line(rng)
    return dict(
        description=f"Fetch {single} {rid} (hard-coded id from test data seeded last sprint)",
        code=dedent(f"""
            {single.upper()}_ID = {rid}   # created manually on staging

            def test_get_{single}_details(api_client):
                r = api_client.get(f"/api/{plural}/{{{single.upper()}_ID}}")
                assert r.status_code == 200
            """),
        log=dedent(f"""
            E       assert 404 == 200
            Response body: {{"detail": "{single.capitalize()} not found"}}
            FAILED tests/api/test_{plural}.py::test_get_{single}_details
            """),
        stacktrace=f'  File "tests/api/test_{plural}.py", line {n}',
    )

# ====================================================================== DB
@scenario("db", "failed_testcase", "db_not_running")
def db_down(rng):
    model, table, _ = rng.choice(TABLES)
    port = rng.choice([5432, 3306, 5433])
    n = line(rng)
    return dict(
        description=f"Saving a {model} persists it",
        code=dedent(f"""
            def test_save_{model.lower()}(db_session):
                obj = {model}(name="test-{rng.randint(1, 999)}")
                db_session.add(obj)
                db_session.commit()
                assert db_session.query({model}).count() == 1
            """),
        log=dedent(f"""
            sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "localhost" (127.0.0.1), port {port} failed: Connection refused
                Is the server running on that host and accepting TCP/IP connections?
            ERROR tests/db/test_{table}.py::test_save_{model.lower()}
            """),
        stacktrace=f'  File "tests/db/test_{table}.py", line {n}, in test_save_{model.lower()}',
    )


@scenario("db", "failed_testcase", "missing_teardown")
def db_no_cleanup(rng):
    model, table, col = rng.choice(TABLES)
    value = f"qa_{rng.randint(100, 999)}"
    n = line(rng)
    return dict(
        description=f"Create a {model} with a unique {col}",
        code=dedent(f"""
            def test_create_{model.lower()}(db_session):
                db_session.add({model}({col}="{value}"))
                db_session.commit()
                # no rollback / cleanup after the test
            """),
        log=dedent(f"""
            sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "{table}_{col}_key"
            DETAIL:  Key ({col})=({value}) already exists.
            FAILED tests/db/test_{table}.py::test_create_{model.lower()}
            """),
        stacktrace=f'  File "tests/db/test_{table}.py", line {n}',
    )


@scenario("db", "failed_testcase", "wrong_table_in_test")
def db_wrong_table(rng):
    model, table, _ = rng.choice(TABLES)
    wrong = rng.choice([table.rstrip("s"), table + "_tbl", model.lower(), "tbl_" + table])
    n = line(rng)
    return dict(
        description=f"Count rows in {table} after seeding",
        code=dedent(f"""
            def test_seed_{table}(db_session, seed_data):
                count = db_session.execute(text("SELECT COUNT(*) FROM {wrong}")).scalar()
                assert count == 3
            """),
        log=dedent(f"""
            sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "{wrong}" does not exist
            LINE 1: SELECT COUNT(*) FROM {wrong}
            FAILED tests/db/test_{table}.py::test_seed_{table}
            """),
        stacktrace=f'  File "tests/db/test_{table}.py", line {n}',
    )


@scenario("db", "bug", "cascade_not_applied")
def db_cascade(rng):
    parent, ptable, _ = rng.choice(TABLES)
    child = rng.choice(["Address", "LineItem", "Comment", "Session", "Payment"])
    left = rng.randint(1, 6)
    n = line(rng)
    return dict(
        description=f"Deleting a {parent} also deletes its {child} rows (ON DELETE CASCADE in the data model spec)",
        code=dedent(f"""
            def test_delete_{parent.lower()}_cascades(db_session, {parent.lower()}_with_children):
                service.delete_{parent.lower()}({parent.lower()}_with_children.id)
                remaining = db_session.query({child}).filter_by({parent.lower()}_id={parent.lower()}_with_children.id).count()
                assert remaining == 0
            """),
        log=dedent(f"""
            E       assert {left} == 0
            FAILED tests/db/test_{ptable}.py::test_delete_{parent.lower()}_cascades
            """),
        stacktrace=dedent(f"""
              File "tests/db/test_{ptable}.py", line {n}, in test_delete_{parent.lower()}_cascades
              File "app/services/{ptable}.py", line {line(rng)}, in delete_{parent.lower()}
            """),
    )


@scenario("db", "bug", "not_persisted")
def db_not_saved(rng):
    model, table, col = rng.choice(TABLES)
    new = f"updated-{rng.randint(10, 99)}"
    n = line(rng)
    return dict(
        description=f"Updating a {model}'s {col} through the service saves it",
        code=dedent(f"""
            def test_update_{model.lower()}_{col}(db_session, existing_{model.lower()}):
                service.update_{model.lower()}(existing_{model.lower()}.id, {col}="{new}")
                db_session.expire_all()
                assert db_session.get({model}, existing_{model.lower()}.id).{col} == "{new}"
            """),
        log=dedent(f"""
            E       AssertionError: assert 'original-value' == '{new}'
            FAILED tests/db/test_{table}.py::test_update_{model.lower()}_{col}
            """),
        stacktrace=dedent(f"""
              File "tests/db/test_{table}.py", line {n}
              File "app/services/{table}.py", line {line(rng)}, in update_{model.lower()}
            """),
    )


@scenario("db", "bug", "app_integrity_error")
def db_app_integrity(rng):
    model, table, col = rng.choice(TABLES)
    n = line(rng)
    return dict(
        description=f"Registering two different {table} via the API works",
        code=dedent(f"""
            def test_register_two_{table}(client, db_session):
                assert client.post("/api/{table}", json={{"{col}": "first-{rng.randint(1, 99)}"}}).status_code == 201
                assert client.post("/api/{table}", json={{"{col}": "second-{rng.randint(1, 99)}"}}).status_code == 201
            """),
        log=dedent(f"""
            sqlalchemy.exc.IntegrityError: (psycopg2.errors.NotNullViolation) null value in column "created_by" of relation "{table}" violates not-null constraint
            FAILED tests/db/test_{table}.py::test_register_two_{table}
            """),
        stacktrace=dedent(f"""
              File "tests/db/test_{table}.py", line {n}
              File "app/repositories/{table}.py", line {line(rng)}, in create_{model.lower()}
                session.commit()
            """),
    )

# ==================================================================== UNIT
@scenario("unit", "bug", "wrong_calculation")
def unit_wrong_calc(rng):
    func, module, args = rng.choice(UNIT_FUNCS)
    a = rng.choice([100, 250, 80, 59.99, 1200])
    b = rng.choice([10, 15, 20, 0.18, 0.05])
    expected = round(a * (1 - b / 100), 2) if b >= 1 else round(a * (1 + b), 2)
    got = round(expected + rng.choice([a * 0.01, -b, 1.0, a * 0.1]), 2)
    n = line(rng)
    return dict(
        description=f"{func} returns the value from the pricing spec",
        code=dedent(f"""
            from app.{module} import {func}

            def test_{func}_basic():
                assert {func}({a}, {b}) == {expected}
            """),
        log=dedent(f"""
            E       assert {got} == {expected}
            E        +  where {got} = {func}({a}, {b})
            FAILED tests/unit/test_{module}.py::test_{func}_basic
            """),
        stacktrace=f'  File "tests/unit/test_{module}.py", line {n}, in test_{func}_basic',
    )


@scenario("unit", "bug", "exception_in_app_code")
def unit_app_exception(rng):
    func, module, args = rng.choice(UNIT_FUNCS)
    exc, msg = rng.choice([("ZeroDivisionError", "division by zero"),
                           ("TypeError", "unsupported operand type(s) for *: 'NoneType' and 'float'"),
                           ("KeyError", "'currency'"), ("IndexError", "list index out of range")])
    n, m = line(rng), line(rng)
    return dict(
        description=f"{func} handles an empty or zero input",
        code=dedent(f"""
            from app.{module} import {func}

            def test_{func}_edge_case():
                assert {func}(0, 0) == 0
            """),
        log=f"E       {exc}: {msg}\nFAILED tests/unit/test_{module}.py::test_{func}_edge_case",
        stacktrace=dedent(f"""
            Traceback (most recent call last):
              File "tests/unit/test_{module}.py", line {n}, in test_{func}_edge_case
                assert {func}(0, 0) == 0
              File "app/{module}.py", line {m}, in {func}
            {exc}: {msg}
            """),
    )


@scenario("unit", "bug", "off_by_one")
def unit_off_by_one(rng):
    n_items = rng.randint(3, 12)
    page_size = rng.choice([2, 5, 10])
    pages = -(-n_items // page_size)
    n = line(rng)
    return dict(
        description=f"paginate() returns {pages} pages for {n_items} items with page size {page_size}",
        code=dedent(f"""
            from app.utils import paginate

            def test_paginate_page_count():
                assert len(paginate(list(range({n_items})), {page_size})) == {pages}
            """),
        log=dedent(f"""
            E       assert {pages - 1 if n_items % page_size else pages + 1} == {pages}
            E        +  where {pages - 1 if n_items % page_size else pages + 1} = len([...])
            FAILED tests/unit/test_utils.py::test_paginate_page_count
            """),
        stacktrace=f'  File "tests/unit/test_utils.py", line {n}, in test_paginate_page_count',
    )


@scenario("unit", "failed_testcase", "wrong_patch_target")
def unit_bad_mock(rng):
    func, module, _ = rng.choice(UNIT_FUNCS)
    dep = rng.choice(["get_rate", "fetch_config", "send_email", "now", "get_exchange_rate"])
    n = line(rng)
    return dict(
        description=f"{func} uses the mocked {dep}",
        code=dedent(f"""
            from unittest.mock import patch
            from app.{module} import {func}

            @patch("app.{module}.helpers.{dep}", return_value=1.0)
            def test_{func}_with_mock(mock_dep):
                assert {func}(100, 1) == 100
            """),
        log=dedent(f"""
            E       AttributeError: <module 'app.{module}' from '/src/app/{module}.py'> does not have the attribute 'helpers'
            FAILED tests/unit/test_{module}.py::test_{func}_with_mock
            """),
        stacktrace=dedent(f"""
              File "/usr/lib/python3.11/unittest/mock.py", line 1430, in __enter__
                original, local = self.get_original()
              File "tests/unit/test_{module}.py", line {n}
            """),
    )


@scenario("unit", "failed_testcase", "fixture_not_found")
def unit_fixture(rng):
    func, module, _ = rng.choice(UNIT_FUNCS)
    fixture = rng.choice(["sample_order", "pricing_config", "mock_rates", "user_factory"])
    n = line(rng)
    return dict(
        description=f"{func} with standard input data",
        code=dedent(f"""
            from app.{module} import {func}

            def test_{func}_standard({fixture}):
                assert {func}({fixture}.amount, {fixture}.rate) > 0
            """),
        log=dedent(f"""
            E       fixture '{fixture}' not found
            >       available fixtures: cache, capfd, capsys, monkeypatch, pytestconfig, tmp_path
            >       use 'pytest --fixtures [testpath]' for help on them.
            ERROR tests/unit/test_{module}.py::test_{func}_standard
            """),
        stacktrace=f'  file tests/unit/test_{module}.py, line {n}',
    )


@scenario("unit", "failed_testcase", "float_equality")
def unit_float(rng):
    func, module, _ = rng.choice(UNIT_FUNCS)
    exact = rng.choice([0.3, 1.1, 2.675, 0.7])
    shown = {0.3: "0.30000000000000004", 1.1: "1.1000000000000003",
             2.675: "2.6749999999999998", 0.7: "0.7000000000000001"}[exact]
    n = line(rng)
    return dict(
        description=f"{func} result for small values",
        code=dedent(f"""
            from app.{module} import {func}

            def test_{func}_small_values():
                assert {func}(0.1, 3) == {exact}
            """),
        log=dedent(f"""
            E       assert {shown} == {exact}
            E        +  where {shown} = {func}(0.1, 3)
            
            FAILED tests/unit/test_{module}.py::test_{func}_small_values
            """),
        stacktrace=f'  File "tests/unit/test_{module}.py", line {n}, in test_{func}_small_values',
    )

# ================================================================= generate
def generate(per_stratum: int, seed: int = 7) -> list:
    """Round-robin over the scenarios of each (framework, label) stratum."""
    rng = random.Random(seed)
    records = []
    for (framework, label) in sorted(SCENARIOS):
        options = SCENARIOS[(framework, label)]
        for i in range(per_stratum):
            name, fn = options[i % len(options)]
            case = fn(rng)
            records.append({
                "id": f"syn-{framework}-{label}-{i + 1:03d}",
                "framework": framework,
                "log": case["log"].strip(),
                "stacktrace": case["stacktrace"].strip(),
                "code_snippet": case["code"].strip(),
                "description": case["description"].strip(),
                "label": label,
                "source": "synthetic",
                "source_ref": f"inject.py:{name}",
                "split": "",
            })
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-stratum", type=int, default=12,
                    help="cases per framework x label (5 frameworks x 2 labels)")
    ap.add_argument("--dataset", default="v1")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true", help="print, don't write")
    args = ap.parse_args()

    new = generate(args.per_stratum, args.seed)
    if args.dry_run:
        for r in new:
            print(f"--- {r['id']}  [{r['source_ref']}]  label={r['label']}")
            print(r["log"], "\n")
        return

    existing = dataset_io.load(args.dataset)
    by_id = {r["id"]: r for r in existing}
    added = 0
    for r in new:
        if r["id"] in by_id:          # keep existing record and its split
            continue
        by_id[r["id"]] = r
        added += 1
    dataset_io.save(args.dataset, list(by_id.values()))
    print(f"Added {added} synthetic cases ({len(new) - added} already present). "
          f"Total: {len(by_id)}")
    print("Next: python -m evaluation.datasets.split --dataset v1")


if __name__ == "__main__":
    main()