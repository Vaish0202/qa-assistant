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

    # API Testing cases
    {
        "id": "TC011",
        "testcase_logs": """FAILED test_api.py::test_create_user
AssertionError: assert 400 == 201
response.status_code = 400
response.json() = {'error': 'email already exists'}""",
        "testcase_description": "Test creates new user via POST API",
        "testcase_code": """def test_create_user():
    response = requests.post('/api/users',
        json={'email': 'existing@test.com', 'name': 'Test'})
    assert response.status_code == 201""",
        "expected": "failed_testcase",
        "reason": "Test uses already existing email — test data setup issue"
    },
    {
        "id": "TC012",
        "testcase_logs": """FAILED test_auth_api.py::test_protected_endpoint
AssertionError: assert 200 == 401
Unauthenticated request returned 200 instead of 401""",
        "testcase_description": "Test verifies protected endpoint rejects unauthenticated requests",
        "testcase_code": """def test_protected_endpoint():
    r = requests.get('/api/admin/users')
    assert r.status_code == 401""",
        "expected": "bug",
        "reason": "API not enforcing authentication — security bug"
    },
    {
        "id": "TC013",
        "testcase_logs": """FAILED test_api.py::test_get_user
requests.exceptions.ConnectionError: HTTPConnectionPool
Max retries exceeded with url: /api/users/1""",
        "testcase_description": "Test fetches user by ID from API",
        "testcase_code": """def test_get_user():
    r = requests.get('http://localhost:8000/api/users/1')
    assert r.status_code == 200""",
        "expected": "failed_testcase",
        "reason": "Server not running during test — environment setup issue"
    },
    {
        "id": "TC014",
        "testcase_logs": """FAILED test_payment_api.py::test_payment_deduction
AssertionError: assert 100.0 == 50.0
Balance not deducted after successful payment
Payment API returned 200 but balance unchanged""",
        "testcase_description": "Test verifies account balance deducted after payment",
        "testcase_code": """def test_payment_deduction():
    initial = get_balance()
    make_payment(50.0)
    final = get_balance()
    assert final == initial - 50.0""",
        "expected": "bug",
        "reason": "Payment processed but balance not updated — backend bug"
    },
    {
        "id": "TC015",
        "testcase_logs": """FAILED test_api.py::test_pagination
AssertionError: assert 10 == 5
GET /api/items?page=1&limit=5 returned 10 items instead of 5""",
        "testcase_description": "Test verifies pagination returns correct number of items",
        "testcase_code": """def test_pagination():
    r = requests.get('/api/items?page=1')
    assert len(r.json()['items']) == 5""",
        "expected": "failed_testcase",
        "reason": "Test missing limit parameter in URL — incomplete test code"
    },

    # DB Testing cases
    {
        "id": "TC016",
        "testcase_logs": """FAILED test_db.py::test_user_insert
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: users.email
INSERT INTO users (email) VALUES ('test@test.com')""",
        "testcase_description": "Test inserts new user into database",
        "testcase_code": """def test_user_insert(db):
    user = User(email='test@test.com')
    db.add(user)
    db.commit()
    assert db.query(User).count() == 1""",
        "expected": "failed_testcase",
        "reason": "Test not cleaning up data between runs — missing teardown"
    },
    {
        "id": "TC017",
        "testcase_logs": """FAILED test_db.py::test_cascade_delete
AssertionError: assert 0 == 3
Child records still exist after parent deleted
Expected 0 children but found 3""",
        "testcase_description": "Test verifies cascade delete removes child records",
        "testcase_code": """def test_cascade_delete(db):
    parent = db.query(Parent).first()
    db.delete(parent)
    db.commit()
    children = db.query(Child).filter_by(parent_id=parent.id).all()
    assert len(children) == 0""",
        "expected": "bug",
        "reason": "Cascade delete not configured — database schema bug"
    },
    {
        "id": "TC018",
        "testcase_logs": """FAILED test_db.py::test_update_persists
AssertionError: assert 'new_name' == 'old_name'
Update not persisted to database
After commit value still shows old data""",
        "testcase_description": "Test verifies name update persists after commit",
        "testcase_code": """def test_update_persists(db):
    user = db.query(User).first()
    user.name = 'new_name'
    db.commit()
    fresh = db.query(User).filter_by(id=user.id).first()
    assert fresh.name == 'new_name'""",
        "expected": "bug",
        "reason": "Database not persisting updates — ORM or DB configuration bug"
    },
    {
        "id": "TC019",
        "testcase_logs": """FAILED test_db.py::test_query_filter
OperationalError: no such column: users.role
SELECT * FROM users WHERE users.role = 'admin'""",
        "testcase_description": "Test queries users by role column",
        "testcase_code": """def test_query_filter(db):
    admins = db.query(User).filter_by(role='admin').all()
    assert len(admins) > 0""",
        "expected": "failed_testcase",
        "reason": "Column 'role' doesn't exist in schema — missing migration"
    },
    {
        "id": "TC020",
        "testcase_logs": """FAILED test_db.py::test_duplicate_prevention
AssertionError: assert 1 == 2
Duplicate order created for same transaction ID
Expected 1 order but found 2 with same transaction_id""",
        "testcase_description": "Test verifies duplicate orders prevented by unique constraint",
        "testcase_code": """def test_duplicate_prevention(db):
    create_order(transaction_id='TXN001')
    create_order(transaction_id='TXN001')
    count = db.query(Order).filter_by(transaction_id='TXN001').count()
    assert count == 1""",
        "expected": "bug",
        "reason": "Unique constraint missing on transaction_id — allows duplicates"
    },

]