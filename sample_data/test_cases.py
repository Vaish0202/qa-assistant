TEST_CASES = [
    # ---- FAILED TESTCASE examples (bad test, not a bug) ----
    {
        "id": "TC001",
        "testcase_logs": """
FAILED test_login.py::test_submit_button
selenium.common.exceptions.NoSuchElementException: 
Message: no such element: Unable to locate element: {"method":"id","selector":"submit-btn"}
Stacktrace: at login_page.py line 45
        """,
        "testcase_description": "Test clicks submit button on login page after entering credentials",
        "testcase_code": """
def test_submit_button(driver):
    driver.find_element(By.ID, 'submit-btn').click()
""",
        "expected": "failed_testcase",
        "reason": "Wrong locator — button ID changed to 'btn-submit', test needs updating"
    },

    {
        "id": "TC002",
        "testcase_logs": """
FAILED test_cart.py::test_add_to_cart
TimeoutException: Message: Timeout waiting for element
Expected condition failed: waiting for visibility of element located by 
(By.CSS_SELECTOR, '.add-cart-btn') for 5 seconds
        """,
        "testcase_description": "Test adds item to cart by clicking add button",
        "testcase_code": """
def test_add_to_cart(driver):
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.add-cart-btn'))
    ).click()
""",
        "expected": "failed_testcase",
        "reason": "Wait time too short (5s), should be 10-15s for slow network"
    },

    {
        "id": "TC003",
        "testcase_logs": """
FAILED test_api.py::test_get_users
AssertionError: assert 200 == 201
  Where 200 = response.status_code
        """,
        "testcase_description": "Test checks user creation returns 201",
        "testcase_code": """
def test_get_users():
    response = requests.get('/api/users')
    assert response.status_code == 201
""",
        "expected": "failed_testcase",
        "reason": "GET should return 200 not 201 — wrong assertion in test"
    },

    # ---- BUG examples (test is correct, app is broken) ----
    {
        "id": "TC004",
        "testcase_logs": """
FAILED test_payment.py::test_checkout_total
AssertionError: assert 150.00 == 120.00
  Where 150.00 = actual cart total
  Where 120.00 = expected cart total (2 items x 60.00)
Cart contents: [item1=60.00, item2=60.00]
        """,
        "testcase_description": "Test verifies cart total is correct sum of items",
        "testcase_code": """
def test_checkout_total(driver):
    total = driver.find_element(By.ID, 'cart-total').text
    assert float(total) == 120.00
""",
        "expected": "bug",
        "reason": "Cart calculation is wrong in application — adds 30 extra"
    },

    {
        "id": "TC005",
        "testcase_logs": """
FAILED test_auth.py::test_login_valid_user
AssertionError: assert 'dashboard' in 'error-page'
After login with valid credentials admin@test.com / Admin@123
Response redirected to /error-page instead of /dashboard
        """,
        "testcase_description": "Test verifies valid user is redirected to dashboard after login",
        "testcase_code": """
def test_login_valid_user(driver):
    driver.find_element(By.ID, 'email').send_keys('admin@test.com')
    driver.find_element(By.ID, 'password').send_keys('Admin@123')
    driver.find_element(By.ID, 'login-btn').click()
    assert 'dashboard' in driver.current_url
""",
        "expected": "bug",
        "reason": "Login is broken in app — valid credentials rejected"
    },

    {
        "id": "TC006",
        "testcase_logs": """
FAILED test_profile.py::test_update_email
requests.exceptions.HTTPError: 500 Server Error: Internal Server Error
POST /api/user/update-email
Request body: {"email": "newuser@gmail.com"}
Server logs: NullPointerException at UserService.java:234
        """,
        "testcase_description": "Test updates user email via API",
        "testcase_code": """
def test_update_email():
    response = requests.post('/api/user/update-email', 
                            json={'email': 'newuser@gmail.com'})
    assert response.status_code == 200
""",
        "expected": "bug",
        "reason": "Server throws 500 — NullPointerException in backend code"
    },

    {
        "id": "TC007",
        "testcase_logs": """
FAILED test_search.py::test_search_results
StaleElementReferenceException: stale element reference: element is not attached to the page document
at test_search.py line 23
        """,
        "testcase_description": "Test searches for product and reads results",
        "testcase_code": """
def test_search_results(driver):
    results = driver.find_elements(By.CLASS_NAME, 'search-result')
    driver.find_element(By.ID, 'search-box').send_keys('laptop')
    driver.find_element(By.ID, 'search-btn').click()
    assert len(results) > 0
""",
        "expected": "failed_testcase",
        "reason": "Elements fetched before search — stale after page refresh. Bad test order."
    },

    {
        "id": "TC008",
        "testcase_logs": """
FAILED test_reports.py::test_export_pdf
AssertionError: PDF file size is 0 bytes
Expected: file size > 1000 bytes
File created at: /downloads/report_2024.pdf
        """,
        "testcase_description": "Test exports report as PDF and verifies file is not empty",
        "testcase_code": """
def test_export_pdf(driver):
    driver.find_element(By.ID, 'export-pdf-btn').click()
    time.sleep(2)
    file_size = os.path.getsize('/downloads/report_2024.pdf')
    assert file_size > 1000
""",
        "expected": "bug",
        "reason": "PDF export generates empty file — bug in export functionality"
    },

    {
        "id": "TC009",
        "testcase_logs": """
FAILED test_notifications.py::test_email_sent
AssertionError: assert 1 == 0
  Where 1 = len(mailbox.messages)
  Expected 0 emails (feature should be disabled for test env)
        """,
        "testcase_description": "Test verifies no emails sent in test environment",
        "testcase_code": """
def test_email_sent():
    trigger_signup('testuser@example.com')
    assert len(mailbox.messages) == 0
""",
        "expected": "failed_testcase",
        "reason": "Test environment config wrong — emails not disabled. Test setup issue."
    },

    {
        "id": "TC010",
        "testcase_logs": """
FAILED test_inventory.py::test_stock_deduction
AssertionError: assert 99 == 100
  Where 99 = current_stock
  Where 100 = expected_stock (no purchase made)
Stock was deducted without any order being placed
        """,
        "testcase_description": "Test verifies stock count unchanged when no purchase made",
        "testcase_code": """
def test_stock_deduction():
    initial_stock = get_stock('ITEM001')
    # no purchase action
    current_stock = get_stock('ITEM001')
    assert current_stock == initial_stock
""",
        "expected": "bug",
        "reason": "Stock decrements without purchase — real inventory bug"
    },
]