from ml_classifier.predict import predict_classification

# Should be bug
r1 = predict_classification(
    "500 Server Error NullPointerException at UserService.java:234",
    "Test updates user email via API",
    'r = requests.post("/api/user/update", json={"email": "new@test.com"})'
)

print("Test 1 (expected bug):", r1["classification"])

# Should be failed_testcase
r2 = predict_classification(
    "NoSuchElementException: Unable to locate element submit-btn",
    "Test clicks submit button",
    'driver.find_element(By.ID, "submit-btn").click()'
)

print("Test 2 (expected failed testcase):", r2["classification"])