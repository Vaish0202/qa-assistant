from agents.framework_detector import detect_framework

# Selenium test
r1 = detect_framework(
    'NoSuchElementException: submit-btn not found',
    'driver.find_element(By.ID, "submit-btn").click()',
    'Test clicks submit button'
)
print('Test 1:', r1['framework'], r1['test_type'])

# API test
r2 = detect_framework(
    'AssertionError: assert 500 == 200',
    'r = requests.post("/api/users", json=data)\nassert r.status_code == 200',
    'Test creates user via API'
)
print('Test 2:', r2['framework'], r2['test_type'])

# DB test
r3 = detect_framework(
    'IntegrityError: UNIQUE constraint failed',
    'db.add(User(email="test"))\ndb.commit()',
    'Test inserts user into database'
)
print('Test 3:', r3['framework'], r3['test_type'])