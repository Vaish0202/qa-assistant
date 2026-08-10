TRAINING_DATA = [
    # ─── FAILED TESTCASE examples ───

    # Selenium / UI
    {
        "logs": "NoSuchElementException: Unable to locate element by ID submit-btn",
        "description": "Test clicks submit button on login page",
        "code": "driver.find_element(By.ID, 'submit-btn').click()",
        "label": "failed_testcase"
    },
    {
        "logs": "TimeoutException: waiting for element visibility for 5 seconds",
        "description": "Test waits for dropdown to appear",
        "code": "WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.dropdown')))",
        "label": "failed_testcase"
    },
    {
        "logs": "StaleElementReferenceException: element is not attached to page",
        "description": "Test reads search results after clicking search",
        "code": "results = driver.find_elements(By.CLASS_NAME, 'result')\ndriver.find_element(By.ID, 'search').click()\nprint(len(results))",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 201 == 200\nWhere 201 = response.status_code",
        "description": "Test checks GET users returns 200",
        "code": "response = requests.get('/api/users')\nassert response.status_code == 200",
        "label": "failed_testcase"
    },
    {
        "logs": "ElementClickInterceptedException: element click intercepted by another element",
        "description": "Test clicks checkout button",
        "code": "driver.find_element(By.ID, 'checkout').click()",
        "label": "failed_testcase"
    },
    {
        "logs": "NoSuchWindowException: no such window: target window already closed",
        "description": "Test switches to popup window",
        "code": "driver.switch_to.window(driver.window_handles[1])",
        "label": "failed_testcase"
    },
    {
        "logs": "InvalidSelectorException: invalid CSS selector .my class",
        "description": "Test finds element by CSS selector",
        "code": "driver.find_element(By.CSS_SELECTOR, '.my class')",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'Welcome' in 'Home Page'\nTitle mismatch",
        "description": "Test checks page title after login",
        "code": "assert 'Welcome' in driver.title",
        "label": "failed_testcase"
    },
    {
        "logs": "WebDriverException: Chrome not reachable, session not created",
        "description": "Test opens browser and navigates to app",
        "code": "driver = webdriver.Chrome()\ndriver.get('http://localhost:3000')",
        "label": "failed_testcase"
    },
    {
        "logs": "MoveTargetOutOfBoundsException: move target out of bounds",
        "description": "Test hovers over menu item",
        "code": "ActionChains(driver).move_to_element(menu).perform()",
        "label": "failed_testcase"
    },

    # API testing failed testcases
    {
        "logs": "AssertionError: assert 'email' in response.json()\nKeyError: email not in response",
        "description": "Test checks email field in user response",
        "code": "r = requests.get('/api/user/1')\nassert 'email' in r.json()",
        "label": "failed_testcase"
    },
    {
        "logs": "JSONDecodeError: Expecting value at line 1 column 1",
        "description": "Test parses API response as JSON",
        "code": "data = response.json()\nassert data['status'] == 'ok'",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 10 == 5\nlen(response.json()) = 10, expected 5",
        "description": "Test checks pagination returns 5 items",
        "code": "r = requests.get('/api/items?page=1')\nassert len(r.json()) == 5",
        "label": "failed_testcase"
    },
    {
        "logs": "ConnectionRefusedError: [WinError 10061] No connection could be made",
        "description": "Test calls local API endpoint",
        "code": "r = requests.post('http://localhost:8000/api/login')",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'Bearer' in headers\nAuthorization header missing",
        "description": "Test verifies auth header is set",
        "code": "assert 'Bearer' in response.request.headers.get('Authorization', '')",
        "label": "failed_testcase"
    },

    # DB testing failed testcases
    {
        "logs": "AssertionError: assert 1 == 0\nExpected 0 rows but found 1",
        "description": "Test verifies deleted record is gone",
        "code": "count = db.query(User).filter_by(id=1).count()\nassert count == 0",
        "label": "failed_testcase"
    },
    {
        "logs": "OperationalError: no such table: users_temp",
        "description": "Test queries temporary table",
        "code": "result = db.execute('SELECT * FROM users_temp')",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'active' == 'inactive'\nStatus mismatch after update",
        "description": "Test checks user status after deactivation",
        "code": "user = db.query(User).first()\nassert user.status == 'inactive'",
        "label": "failed_testcase"
    },

    # ─── BUG examples ───

    # UI/Selenium bugs
    {
        "logs": "AssertionError: assert 'dashboard' in 'error-page'\nValid login redirects to error",
        "description": "Test verifies valid user redirected to dashboard after login",
        "code": "driver.find_element(By.ID, 'email').send_keys('admin@test.com')\ndriver.find_element(By.ID, 'login-btn').click()\nassert 'dashboard' in driver.current_url",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 150.00 == 120.00\nCart total shows wrong amount",
        "description": "Test verifies cart total equals sum of items",
        "code": "total = driver.find_element(By.ID, 'cart-total').text\nassert float(total) == 120.00",
        "label": "bug"
    },
    {
        "logs": "AssertionError: PDF file size is 0 bytes\nExport generates empty file",
        "description": "Test exports report as PDF and checks file size",
        "code": "driver.find_element(By.ID, 'export-pdf').click()\ntime.sleep(2)\nassert os.path.getsize('report.pdf') > 1000",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 99 == 100\nStock reduced without any purchase",
        "description": "Test verifies stock unchanged when no purchase made",
        "code": "initial = get_stock('ITEM001')\ncurrent = get_stock('ITEM001')\nassert current == initial",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 1 == 0\nEmail sent in test environment when it should not be",
        "description": "Test verifies no emails sent in test environment",
        "code": "trigger_signup('test@example.com')\nassert len(mailbox.messages) == 0",
        "label": "bug"
    },

    # API bugs
    {
        "logs": "HTTPError: 500 Server Error Internal Server Error\nNullPointerException at UserService.java:234",
        "description": "Test updates user email via API",
        "code": "r = requests.post('/api/user/update', json={'email': 'new@test.com'})\nassert r.status_code == 200",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 200 == 401\nAPI returns 200 for unauthenticated request",
        "description": "Test verifies unauthenticated request is rejected",
        "code": "r = requests.get('/api/admin/users')\nassert r.status_code == 401",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 'john@test.com' == 'jane@test.com'\nWrong user data returned",
        "description": "Test gets specific user by ID",
        "code": "r = requests.get('/api/user/2')\nassert r.json()['email'] == 'jane@test.com'",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 201 == 200\nDuplicate record created instead of updating",
        "description": "Test updates existing record via PUT",
        "code": "r = requests.put('/api/item/1', json={'name': 'updated'})\nassert r.status_code == 200",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 0 == 150.50\nPayment processed but balance not deducted",
        "description": "Test verifies account balance deducted after payment",
        "code": "make_payment(amount=150.50)\nbalance = get_balance()\nassert balance == initial_balance - 150.50",
        "label": "bug"
    },

    # DB bugs
    {
        "logs": "AssertionError: assert 1 == 2\nDuplicate records found after insert",
        "description": "Test inserts unique record and checks count",
        "code": "db.insert(User(email='test@test.com'))\ncount = db.query(User).filter_by(email='test@test.com').count()\nassert count == 1",
        "label": "bug"
    },
    {
        "logs": "AssertionError: assert 'updated_name' == 'old_name'\nDatabase not persisting updates",
        "description": "Test updates username and verifies change persisted",
        "code": "user.name = 'updated_name'\ndb.commit()\nfetched = db.query(User).get(user.id)\nassert fetched.name == 'updated_name'",
        "label": "bug"
    },
    {
        "logs": "IntegrityError: UNIQUE constraint failed after cascade delete",
        "description": "Test deletes parent record and checks cascade",
        "code": "db.delete(parent_record)\ndb.commit()\nchildren = db.query(Child).filter_by(parent_id=1).all()\nassert len(children) == 0",
        "label": "bug"
    },

    # More varied examples
    {
        "logs": "AssertionError: assert True == False\nCheckbox remains unchecked after click",
        "description": "Test checks checkbox is selected after clicking it",
        "code": "driver.find_element(By.ID, 'agree-checkbox').click()\nassert driver.find_element(By.ID, 'agree-checkbox').is_selected()",
        "label": "bug"
    },
    {
        "logs": "NoSuchElementException: label[for='username'] not found",
        "description": "Test finds username label on form",
        "code": "driver.find_element(By.CSS_SELECTOR, \"label[for='username']\")",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 403 == 200\nAdmin user getting forbidden on admin page",
        "description": "Test verifies admin user can access admin dashboard",
        "code": "login_as_admin()\nr = requests.get('/api/admin/dashboard')\nassert r.status_code == 200",
        "label": "bug"
    },
    {
        "logs": "TimeoutException: element not clickable after 30 seconds",
        "description": "Test clicks payment button after adding items to cart",
        "code": "WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//button[@id=\"pay\"]')))",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'success' == 'error'\nPassword reset returns error for valid email",
        "description": "Test verifies password reset works for registered email",
        "code": "r = requests.post('/api/reset-password', json={'email': 'valid@test.com'})\nassert r.json()['status'] == 'success'",
        "label": "bug"
    },
    {
        "logs": "ElementNotInteractableException: element not interactable date input",
        "description": "Test enters date in date picker field",
        "code": "driver.find_element(By.ID, 'date-picker').send_keys('2024-01-01')",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'USD' == 'EUR'\nCurrency not converting after country change",
        "description": "Test verifies currency changes when country is updated",
        "code": "select_country('Germany')\ncurrency = driver.find_element(By.ID, 'currency').text\nassert currency == 'EUR'",
        "label": "bug"
    },
    {
        "logs": "AttributeError: 'NoneType' object has no attribute 'text'\nelement returned None",
        "description": "Test reads text from optional element",
        "code": "element = driver.find_element(By.ID, 'optional-msg')\nassert element.text == 'Success'",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 5 == 10\nSearch returns wrong number of results",
        "description": "Test verifies search returns all matching products",
        "code": "search('laptop')\nresults = driver.find_elements(By.CLASS_NAME, 'product-card')\nassert len(results) == 10",
        "label": "bug"
    },
    {
        "logs": "ImproperlyConfigured: settings.DATABASES not configured",
        "description": "Test checks database connection in Django app",
        "code": "from django.db import connection\nconnection.ensure_connection()",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'admin' in roles\nUser role not assigned after registration",
        "description": "Test verifies admin role assigned to first user",
        "code": "register_user('firstuser@test.com')\nroles = get_user_roles('firstuser@test.com')\nassert 'admin' in roles",
        "label": "bug"
    },
    {
        "logs": "XPathEvalError: invalid XPath expression //button[contains(@class,'btn-primary'",
        "description": "Test finds primary button using XPath",
        "code": "driver.find_element(By.XPATH, \"//button[contains(@class,'btn-primary'\")",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 'inactive' == 'active'\nUser still active after account deletion",
        "description": "Test verifies account is deactivated after deletion request",
        "code": "delete_account(user_id=5)\nstatus = get_account_status(user_id=5)\nassert status == 'inactive'",
        "label": "bug"
    },
    {
        "logs": "ModuleNotFoundError: No module named 'conftest'",
        "description": "Test imports shared fixtures from conftest",
        "code": "from conftest import setup_browser\ndriver = setup_browser()",
        "label": "failed_testcase"
    },
    {
        "logs": "AssertionError: assert 2 == 1\nNotification sent twice for single event",
        "description": "Test verifies single notification sent per event",
        "code": "trigger_event('order_placed')\ncount = get_notification_count()\nassert count == 1",
        "label": "bug"
    },
    {
        "logs": "UnicodeDecodeError: codec can't decode byte in test log file",
        "description": "Test reads log file and checks content",
        "code": "with open('test.log', 'r') as f:\n    content = f.read()\nassert 'ERROR' not in content",
        "label": "failed_testcase"
    },
]