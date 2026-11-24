# Blind review sheet

**Rubric** (same as the judge)
- **correctness** 5 = right cause (matches the reference) · 3 = partly right / vague · 1 = wrong cause or wrong side (app vs test)
- **groundedness** 5 = every factual claim about what happened is in the input · 3 = one invented fact stated as true · 1 = several.
  Don't count fixes, improved code, advice, severity, repro steps from the test code, or hedged guesses ("likely").
- **actionability** 5 = concrete next step (exact change / locator / endpoint / repro) · 3 = a direction, but generic · 1 = generic advice
- **hallucination** yes = at least one invented fact stated as true (same rule as groundedness), else no

---
## 1. `gh-jaylfc-taos-4259`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); real case, no further detail known

**Input the assistant saw**
```
DESCRIPTION: 
LOGS:
E       assert 200 == 500
E        +  where 200 = <Response [200 OK]>.status_code
ERROR    tinyagentos.routes.hub:hub.py:729 hub block: contacts-store cascade failed for 9a2db2e23f1504cd056606553ac049c5e718e8f9ce9233876df1a7a1821af885
FAILED tests/test_collab_a2_handshake.py::TestBlockCascade::test_block_cascade_revoke_failure_returns_incomplete
1 failed, 20 passed in 33.13s
CODE:
```

**Output to score**
```
JIRA DRAFT
Summary: Hub block cascade failure returns 200 OK instead of 500
Severity: medium
Description: During a block cascade revoke operation, the contacts-store cascade can fail (e.g., due to a database error or missing record). The current implementation logs the failure but still returns a 200 OK response. The unit test `test_block_cascade_revoke_failure_returns_incomplete` expects a 500 Internal Server Error when the cascade fails, but receives 200, causing the test to fail. This indicates that the error handling in the `hub` route does not propagate the failure to the HTTP response status code.
Steps to reproduce:
  1. 1. Trigger a block cascade revoke that is designed to fail (e.g., by using a non-existent contact ID or simulating a database error).
  2. 2. Observe the HTTP response from the `/hub/block` endpoint.
Expected: The endpoint should return a 500 Internal Server Error when the cascade fails.
Actual: The endpoint returns a 200 OK response even though the cascade failed, as logged by `hub block: contacts-store cascade failed`.
Suggested fix: Update the hub block route to raise an HTTPException with status_code=500 when the cascade fails. Ensure that the exception propagates to the FastAPI response layer. Optionally, add a try/except around the cascade logic and return a JSON error payload with a 500 status code.
```

---
## 2. `syn-db-bug-014`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: not persisted

**Input the assistant saw**
```
DESCRIPTION: Updating a Coupon's code through the service saves it
LOGS:
E       AssertionError: assert 'original-value' == 'updated-81'
FAILED tests/db/test_coupons.py::test_update_coupon_code
File "tests/db/test_coupons.py", line 112
File "app/services/coupons.py", line 113, in update_coupon
CODE:
def test_update_coupon_code(db_session, existing_coupon):
    service.update_coupon(existing_coupon.id, code="updated-81")
    db_session.expire_all()
    assert db_session.get(Coupon, existing_coupon.id).code == "updated-81"
```

**Output to score**
```
JIRA DRAFT
Summary: Coupon code not updated by service.update_coupon
Severity: medium
Description: The unit test test_update_coupon_code fails because the Coupon code remains unchanged after calling service.update_coupon. The service likely performs the update in a separate SQLAlchemy session or does not commit the transaction, so the changes are not visible in the test's db_session. This results in the database still holding the original code value.
Steps to reproduce:
  1. Call service.update_coupon(existing_coupon.id, code="updated-81")
  2. Expire all objects in the test db_session
  3. Retrieve the Coupon by id and check its code
Expected: The Coupon's code should be "updated-81" after the update.
Actual: The Coupon's code remains "original-value".
Suggested fix: Ensure that service.update_coupon uses the same session passed by the test or explicitly commits the transaction. For example, modify the service to accept a session parameter or call session.commit() after updating the Coupon. Verify that the update operation uses session.merge or session.query(...).update(...) followed by session.commit().
```

---
## 3. `syn-playwright-bug-004`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: error redirect

**Input the assistant saw**
```
DESCRIPTION: Opening Cart should keep the user on /cart
LOGS:
AssertionError: Page URL expected to match regex '.*/cart'
Actual value: https://app/error?code=500
Call log:
  - waiting for navigation until "load"
  - navigated to "https://app/error?code=500"
FAILED tests/e2e/test_cart.py::test_open_cart[chromium]
File "tests/e2e/test_cart.py", line 138, in test_open_cart
CODE:
def test_open_cart(page: Page):
    page.goto("https://localhost:8000/cart")
    expect(page).to_have_url(re.compile(".*/cart"))
```

**Output to score**
```
JIRA DRAFT
Summary: Cart route returns 500 error instead of /cart page
Severity: medium
Description: When a user navigates to the /cart endpoint, the server responds with a 500 Internal Server Error and redirects to https://app/error?code=500. The test suite expects the URL to match the /cart pattern, but the application fails to render the cart page. This indicates a server-side issue in the cart route handler, possibly due to missing data, unhandled exceptions, or misconfigured routing. The error prevents users from accessing the cart, impacting core e‑commerce functionality.
Steps to reproduce:
  1. Open a browser and navigate to https://localhost:8000/cart
  2. Observe the page load and URL
Expected: The browser should load the cart page and the URL should match the pattern .*/cart.
Actual: The browser redirects to https://app/error?code=500 and displays a generic error page.
Suggested fix: Inspect the server logs for the 500 error. Verify that the cart route handler correctly fetches cart data, handles missing sessions, and returns the proper template. Add error handling to catch exceptions and return a 404 or 500 with a user‑friendly message. Ensure the route is correctly registered in the routing table and that any middleware (e.g., authentication) does not block access to /cart.
```

---
## 4. `syn-selenium-bug-014`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: wrong value displayed

**Input the assistant saw**
```
DESCRIPTION: Cart total should equal quantity x unit price (5 x 7.25)
LOGS:
E       AssertionError: assert '$29.00' == '$36.25'
FAILED tests/ui/test_cart.py::test_cart_total
File "tests/ui/test_cart.py", line 87, in test_cart_total
CODE:
def test_cart_total(driver, product_page):
    product_page.set_quantity(5)
    product_page.add_to_cart()
    total = driver.find_element(By.ID, "cart-total").text
    assert total == "$36.25"
```

**Output to score**
```
JIRA DRAFT
Summary: Cart total displays incorrect amount ($29.00 instead of $36.25) after adding 5 items
Severity: high
Description: When a user sets the quantity of a product to 5 and adds it to the cart, the cart total displayed in the UI is $29.00. The expected total, based on the unit price of $7.25, should be $36.25 (5 x $7.25). This indicates a calculation or rendering bug in the cart total component. The bug is reproducible on the product page for any product with a unit price of $7.25 and quantity > 1. The UI shows the wrong total in the element with ID "cart-total".
Steps to reproduce:
  1. Navigate to a product page with unit price $7.25.
  2. Set the quantity field to 5 using the quantity selector.
  3. Click the "Add to cart" button.
  4. Observe the cart total displayed in the element with ID "cart-total".
Expected: The cart total should display "$36.25" (5 x $7.25).
Actual: The cart total displays "$29.00".
Suggested fix: Check the JavaScript/React component that calculates and renders the cart total. Verify that the quantity and unit price are correctly retrieved from the product data and that the multiplication uses the correct values. Also ensure that no rounding or integer truncation occurs. Inspect the data passed to the cart-total element and confirm that the unit price is not being overridden by a default or cached value.
```

---
## 5. `syn-unit-bug-011`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: exception in app code

**Input the assistant saw**
```
DESCRIPTION: compute_shipping handles an empty or zero input
LOGS:
E       KeyError: 'currency'
FAILED tests/unit/test_shipping.py::test_compute_shipping_edge_case
Traceback (most recent call last):
  File "tests/unit/test_shipping.py", line 74, in test_compute_shipping_edge_case
    assert compute_shipping(0, 0) == 0
  File "app/shipping.py", line 20, in compute_shipping
KeyError: 'currency'
CODE:
from app.shipping import compute_shipping

def test_compute_shipping_edge_case():
    assert compute_shipping(0, 0) == 0
```

**Output to score**
```
JIRA DRAFT
Summary: compute_shipping raises KeyError 'currency' on zero inputs
Severity: medium
Description: The compute_shipping function in app/shipping.py incorrectly assumes the first argument is a dictionary containing a 'currency' key. When the function is called with numeric values (e.g., compute_shipping(0, 0)), it attempts to access shipping['currency'] and raises a KeyError. This breaks the unit test that expects a zero shipping cost for zero weight and distance. The bug indicates a mismatch between the function signature and its implementation, likely due to a refactor that changed the expected input type without updating the code.
Steps to reproduce:
  1. Import compute_shipping from app.shipping.
  2. Call compute_shipping(0, 0).
Expected: The function should return 0 for zero weight and distance.
Actual: KeyError: 'currency' is raised, causing the test to fail.
Suggested fix: Update compute_shipping to accept numeric weight and distance parameters instead of a dictionary, or add a guard that checks for the presence of 'currency' before accessing it. If the function is meant to work with a dict, modify the test to pass a proper dict or provide a default dict with a 'currency' key. Ensure the function handles zero values gracefully and returns 0 as expected.
```

---
## 6. `syn-api-bug-015`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: validation not enforced

**Input the assistant saw**
```
DESCRIPTION: POST /payments must reject a non-numeric price with 422
LOGS:
E       assert 201 == 422
E        +  where 201 = <Response [201]>.status_code
FAILED tests/api/test_payments.py::test_create_payment_rejects_non_numeric_price
File "tests/api/test_payments.py", line 92
CODE:
def test_create_payment_rejects_non_numeric_price(api_client):
    r = api_client.post("/api/payments", json={"price": "abc"})
    assert r.status_code == 422
```

**Output to score**
```
JIRA DRAFT
Summary: POST /payments accepts non-numeric price, returns 201 instead of 422
Severity: medium
Description: The payments endpoint incorrectly accepts a string value for the `price` field and creates a payment with status code 201. According to the API contract, a non-numeric price should trigger a validation error and return HTTP 422 Unprocessable Entity. The current implementation likely lacks proper type validation or Pydantic model enforcement, allowing the request to pass through and create a payment record with an invalid price.
Steps to reproduce:
  1. Send POST /api/payments with JSON body {"price": "abc"}
Expected: API should return 422 Unprocessable Entity with a validation error message.
Actual: API returns 201 Created, indicating the payment was created with an invalid price.
Suggested fix: Update the request model to enforce numeric type for `price` (e.g., float or Decimal). Add a Pydantic validator or use FastAPI's built-in type validation. Ensure that any conversion errors raise a ValidationError so FastAPI returns 422. Also, add unit tests to cover this scenario.
```

---
## 7. `gh-coombzy-project-car-207`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); real case, no further detail known

**Input the assistant saw**
```
DESCRIPTION: 
LOGS:
FAILED tests/test_tier_patch_null.py::test_explicit_null_is_422_and_leaves_the_tier_unchanged[display_name] - sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: membership_tiers.display_name
FAILED tests/test_tier_patch_null.py::test_explicit_null_is_422_and_leaves_the_tier_unchanged[price] - sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: membership_tiers.price
FAILED tests/test_tier_patch_null.py::test_explicit_null_is_422_and_leaves_the_tier_unchanged[included_tokens] - sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: membership_tiers.included_tokens
FAILED tests/test_tier_patch_null.py::test_explicit_null_is_422_and_leaves_the_tier_unchanged[booking_window_days] - sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: membership_tiers.booking_window_days
FAILED tests/test_tier_patch_null.py::test_explicit_null_is_422_and_leaves_the_tier_unchanged[max_simultaneous_bookings] - sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: membership_tiers.max_simultaneous_bookings
5 failed, 3 passed, 1 warning in 0.40s
CODE:
```

**Output to score**
```
JIRA DRAFT
Summary: PATCH null values cause IntegrityError instead of 422
Severity: high
Description: When a PATCH request is sent to update a membership tier with explicit null values for non‑nullable columns (display_name, price, included_tokens, booking_window_days, max_simultaneous_bookings), the API attempts to write the nulls to the database. Because the membership_tiers table defines these columns as NOT NULL, SQLite raises an IntegrityError. The test suite expects the API to validate the payload and return a 422 Unprocessable Entity, leaving the tier unchanged. Instead, the request results in a 500 error due to the database constraint violation, indicating missing validation logic before the ORM update.
Steps to reproduce:
  1. Create a membership tier with valid values.
  2. Send a PATCH request to the tier endpoint with a null value for one of the non‑nullable fields (e.g., display_name).
  3. Observe the response and database state.
Expected: The API should return a 422 Unprocessable Entity and the tier record should remain unchanged.
Actual: The API attempts the update, SQLite throws a NOT NULL constraint failure, and the request fails with a 500 error.
Suggested fix: Add explicit validation in the request schema or before the ORM update to reject null values for non‑nullable columns. Return a 422 response with a clear error message. Ensure the update operation is wrapped in a transaction that rolls back on validation failure so the tier remains unchanged.
```

---
## 8. `syn-playwright-bug-013`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: error redirect

**Input the assistant saw**
```
DESCRIPTION: Opening Profile should keep the user on /profile
LOGS:
AssertionError: Page URL expected to match regex '.*/profile'
Actual value: https://app/error?code=500
Call log:
  - waiting for navigation until "load"
  - navigated to "https://app/error?code=500"
FAILED tests/e2e/test_profile.py::test_open_profile[chromium]
File "tests/e2e/test_profile.py", line 19, in test_open_profile
CODE:
def test_open_profile(page: Page):
    page.goto("https://qa.app.internal/profile")
    expect(page).to_have_url(re.compile(".*/profile"))
```

**Output to score**
```
JIRA DRAFT
Summary: Profile page returns 500 error on navigation
Severity: medium
Description: When a user navigates to the profile page (https://qa.app.internal/profile), the application redirects to an error page (https://app/error?code=500) instead of staying on the /profile route. The test framework (pytest with Playwright) captures this as an AssertionError because the URL does not match the expected regex '.*/profile'. This indicates a server-side issue where the /profile endpoint is throwing an internal server error, likely due to missing data, misconfigured route, or a bug in the profile controller. The error is reproducible across browsers (chromium, firefox, webkit) and occurs immediately upon navigation, suggesting the problem is not client-side rendering but a backend failure.
Steps to reproduce:
  1. Open a browser and navigate to https://qa.app.internal/profile
  2. Observe the redirection to https://app/error?code=500
Expected: The browser should remain on https://qa.app.internal/profile and display the user's profile information.
Actual: The browser redirects to https://app/error?code=500, indicating a 500 Internal Server Error.
Suggested fix: Investigate the /profile route handler in the backend. Check for missing dependencies, database queries, or authentication middleware that might be throwing an exception. Add proper error handling and return a 200 response with the profile page. Verify that the route is correctly registered and that any required services are available in the test environment.
```

---
## 9. `syn-selenium-bug-005`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: wrong value displayed

**Input the assistant saw**
```
DESCRIPTION: Cart total should equal quantity x unit price (4 x 24.5)
LOGS:
E       AssertionError: assert '$107.80' == '$98.00'
FAILED tests/ui/test_cart.py::test_cart_total
File "tests/ui/test_cart.py", line 47, in test_cart_total
CODE:
def test_cart_total(driver, product_page):
    product_page.set_quantity(4)
    product_page.add_to_cart()
    total = driver.find_element(By.ID, "cart-total").text
    assert total == "$98.00"
```

**Output to score**
```
JIRA DRAFT
Summary: Cart total shows incorrect amount after adding product with quantity 4
Severity: high
Description: When a user sets the quantity of a product to 4 and adds it to the cart, the cart total displayed in the UI is $107.80 instead of the expected $98.00 (4 x $24.50). The unit price shown on the product page is $24.50, but the cart calculation appears to use a different price ($26.95). This indicates a mismatch between the displayed unit price and the price used in the cart total calculation, causing a visual/UI inconsistency that misleads users about the actual cost.
Steps to reproduce:
  1. Open the product page for any item with a unit price of $24.50.
  2. Set the quantity field to 4 using the UI.
  3. Click the "Add to cart" button.
  4. Observe the cart total displayed in the element with ID "cart-total".
Expected: The cart total should display "$98.00" (4 x $24.50).
Actual: The cart total displays "$107.80" (4 x $26.95).
Suggested fix: Verify the price retrieval logic in the cart component. Ensure that the unit price used for the total calculation is the same value displayed on the product page ($24.50). Check the backend service or database query that provides the price to the cart, and confirm that it is not pulling a stale or incorrect price. Update the calculation to multiply the correct unit price by the quantity, and add unit tests to assert the total for various quantities.
```

---
## 10. `syn-unit-bug-008`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: exception in app code

**Input the assistant saw**
```
DESCRIPTION: prorate_refund handles an empty or zero input
LOGS:
E       KeyError: 'currency'
FAILED tests/unit/test_refunds.py::test_prorate_refund_edge_case
Traceback (most recent call last):
  File "tests/unit/test_refunds.py", line 23, in test_prorate_refund_edge_case
    assert prorate_refund(0, 0) == 0
  File "app/refunds.py", line 129, in prorate_refund
KeyError: 'currency'
CODE:
from app.refunds import prorate_refund

def test_prorate_refund_edge_case():
    assert prorate_refund(0, 0) == 0
```

**Output to score**
```
JIRA DRAFT
Summary: prorate_refund throws KeyError on zero inputs
Severity: medium
Description: The prorate_refund function in app/refunds.py expects a dictionary containing a 'currency' key. When called with numeric arguments (e.g., prorate_refund(0, 0)), the function attempts to access the 'currency' key and raises a KeyError. This causes the unit test test_prorate_refund_edge_case to fail. The function should gracefully handle zero or empty inputs by returning 0 without raising an exception.
Steps to reproduce:
  1. Import prorate_refund from app.refunds
  2. Call prorate_refund(0, 0)
Expected: The function should return 0 for zero or empty inputs.
Actual: KeyError: 'currency' is raised.
Suggested fix: Add input validation at the start of prorate_refund to check if the amount or currency is zero or None. If so, return 0 immediately. Alternatively, change the function signature to accept numeric amounts and a separate currency parameter, and provide a default currency when none is supplied. Ensure that any dictionary access is guarded with .get('currency', default) to avoid KeyError.
```

---
## 11. `syn-api-bug-012`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: validation not enforced

**Input the assistant saw**
```
DESCRIPTION: POST /payments must reject a invalid email with 422
LOGS:
E       assert 201 == 422
E        +  where 201 = <Response [201]>.status_code
FAILED tests/api/test_payments.py::test_create_payment_rejects_invalid_email
File "tests/api/test_payments.py", line 107
CODE:
def test_create_payment_rejects_invalid_email(api_client):
    r = api_client.post("/api/payments", json={"email": "not-an-email"})
    assert r.status_code == 422
```

**Output to score**
```
JIRA DRAFT
Summary: Payments endpoint accepts invalid email, returns 201 instead of 422
Severity: medium
Description: The /api/payments POST endpoint is supposed to validate the email field and reject malformed addresses with a 422 Unprocessable Entity response. However, when an invalid email such as "not-an-email" is submitted, the API returns a 201 Created status and creates a payment record. This indicates that the email validation logic is missing or not being enforced in the request handler or the Pydantic/Marshmallow schema. The bug allows potentially corrupt data to enter the system and violates the API contract defined in the test suite.
Steps to reproduce:
  1. Send POST /api/payments with JSON body {"email": "not-an-email"}
Expected: API should respond with HTTP 422 Unprocessable Entity and no payment record created.
Actual: API responds with HTTP 201 Created and creates a payment record with the invalid email.
Suggested fix: Add email validation to the request schema (e.g., Pydantic EmailStr or regex). Ensure the endpoint raises HTTPException(status_code=422) when validation fails. Run unit tests to confirm the change.
```

---
## 12. `syn-db-bug-011`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: not persisted

**Input the assistant saw**
```
DESCRIPTION: Updating a Product's sku through the service saves it
LOGS:
E       AssertionError: assert 'original-value' == 'updated-46'
FAILED tests/db/test_products.py::test_update_product_sku
File "tests/db/test_products.py", line 13
File "app/services/products.py", line 49, in update_product
CODE:
def test_update_product_sku(db_session, existing_product):
    service.update_product(existing_product.id, sku="updated-46")
    db_session.expire_all()
    assert db_session.get(Product, existing_product.id).sku == "updated-46"
```

**Output to score**
```
JIRA DRAFT
Summary: Product SKU not persisted after update_product service call
Severity: medium
Description: The update_product service fails to persist changes to the Product SKU field. When the service is invoked with a new SKU value, the database record remains unchanged. This indicates that the service either does not commit the transaction or updates the wrong session/instance. The unit test confirms the issue by expiring the session and retrieving the product, which still shows the original SKU.
Steps to reproduce:
  1. Call service.update_product(existing_product.id, sku="updated-46")
  2. Expire all objects in the db_session
  3. Retrieve the product via db_session.get(Product, existing_product.id)
Expected: The product's SKU should be updated to "updated-46" in the database.
Actual: The product's SKU remains "original-value" after the service call.
Suggested fix: Ensure that update_product commits the transaction after modifying the SKU. If using SQLAlchemy's session.update, call session.commit() or session.flush() after the update. Alternatively, use session.merge(updated_product) followed by session.commit(). Verify that the session used in the service is the same as the one in the test fixture.
```

---
## 13. `syn-playwright-bug-007`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: error redirect

**Input the assistant saw**
```
DESCRIPTION: Opening Dashboard should keep the user on /dashboard
LOGS:
AssertionError: Page URL expected to match regex '.*/dashboard'
Actual value: https://app/error?code=500
Call log:
  - waiting for navigation until "load"
  - navigated to "https://app/error?code=500"
FAILED tests/e2e/test_dashboard.py::test_open_dashboard[chromium]
File "tests/e2e/test_dashboard.py", line 32, in test_open_dashboard
CODE:
def test_open_dashboard(page: Page):
    page.goto("https://qa.app.internal/dashboard")
    expect(page).to_have_url(re.compile(".*/dashboard"))
```

**Output to score**
```
JIRA DRAFT
Summary: Dashboard route returns 500 error instead of rendering page
Severity: medium
Description: When a user navigates to the dashboard URL (https://qa.app.internal/dashboard), the application responds with a 500 Internal Server Error and redirects to https://app/error?code=500. The test expects the URL to match the pattern ".*/dashboard" but receives the error page URL. This indicates a server-side failure when rendering the dashboard, likely due to missing data, misconfigured route, or a bug in the dashboard controller. The issue occurs consistently across browsers (chromium) and is not a UI rendering problem.
Steps to reproduce:
  1. Open a browser and navigate to https://qa.app.internal/dashboard
  2. Observe the page load and URL change
Expected: The browser should stay on a URL matching ".*/dashboard" and display the dashboard content.
Actual: The browser navigates to https://app/error?code=500 and displays a generic error page.
Suggested fix: Check the server logs for the 500 error details. Verify that the dashboard route handler is correctly configured, that all required services (e.g., database, cache) are available, and that any template rendering or data fetching logic does not throw exceptions. Add proper error handling and return a 200 status with the dashboard view when data is available. If the error is due to missing authentication, ensure the route is protected and the user session is valid.
```

---
## 14. `syn-selenium-bug-008`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); injected fault: wrong value displayed

**Input the assistant saw**
```
DESCRIPTION: Cart total should equal quantity x unit price (3 x 24.5)
LOGS:
E       AssertionError: assert '$49.00' == '$73.50'
FAILED tests/ui/test_cart.py::test_cart_total
File "tests/ui/test_cart.py", line 122, in test_cart_total
CODE:
def test_cart_total(driver, product_page):
    product_page.set_quantity(3)
    product_page.add_to_cart()
    total = driver.find_element(By.ID, "cart-total").text
    assert total == "$73.50"
```

**Output to score**
```
JIRA DRAFT
Summary: Cart total displays incorrect value after adding 3 items ($49.00 instead of $73.50)
Severity: high
Description: When a user sets the quantity of a product to 3 and adds it to the cart, the cart total displayed in the UI is $49.00. The expected total, based on the unit price of $24.50, should be $73.50 (3 x $24.50). The Selenium test fails with an assertion error: assert '$49.00' == '$73.50'. This indicates that the cart total calculation or rendering logic is incorrect, leading to a misleading total for the customer.
Steps to reproduce:
  1. Navigate to a product page with unit price $24.50.
  2. Set the quantity field to 3 using the UI.
  3. Click the 'Add to Cart' button.
  4. Observe the cart total displayed in the element with ID 'cart-total'.
Expected: The cart total should display "$73.50" (3 x $24.50).
Actual: The cart total displays "$49.00".
Suggested fix: Review the JavaScript or backend code that calculates the cart total. Ensure that the quantity is multiplied by the correct unit price and that the result is formatted as a currency string. Check for any hardcoded values or rounding errors that might be causing the incorrect total. Update the calculation logic and re-run the test to confirm the fix.
```

---
## 15. `gh-pechst1-conversationallanguagelearning-813`  (bug)

**Reference:** the APPLICATION is wrong (a real bug); real case, no further detail known

**Input the assistant saw**
```
DESCRIPTION: 
LOGS:
FAILED tests/test_recall_781.py::test_case_swap_is_right - AssertionError: the right words in the right order, only the capital on the other «j'ai», were judged not_yet with correction None
FAILED tests/test_recall_781.py::test_twin_tiles_swap - AssertionError: swapping two «le» tiles was not_yet, correction None
FAILED tests/test_recall_781.py::test_key_matches_grader - AssertionError: the key holds only the one stored id order
FAILED tests/test_recall_781.py::test_miss_shows_answer - AssertionError: «j'ai vingt-cinq ans et J'ai faim !» was «not yet» with no correction
FAILED tests/test_recall_781.py::test_no_key_meaning_decoy - AssertionError: band None: distractor «one» is a meaning of «une» («a, an (f.); one»)
FAILED tests/test_recall_781.py::test_pairs_one_meaning - AssertionError: ['house', 'cat', 'a, an (f.); one', 'one']
FAILED tests/test_recall_781.py::test_no_repair_of_right - AssertionError: «Write this correctly in French.» over «le bureau de poste», which is already a right way to say «la poste»
7 failed, 104 passed
CODE:
```

**Output to score**
```
JIRA DRAFT
Summary: Recall grader incorrectly returns None for correct answers involving swapped words, duplicate tiles, and key matches
Severity: medium
Description: The recall_781 grading logic fails to recognize correct answers when words are swapped, duplicate tiles are present, or key matches rely on stored ID order. As a result, the grader returns a status of "not yet" with no correction, causing multiple unit tests to fail. The issue appears to stem from overly strict tokenization and ordering checks, as well as incomplete handling of key match logic. Fixing this requires revising the token comparison to be order‑agnostic where appropriate, ensuring duplicate tiles are treated as valid, and updating key matching to respect the stored ID sequence.
Steps to reproduce:
  1. Run pytest on tests/test_recall_781.py
  2. Observe failures in test_case_swap_is_right, test_twin_tiles_swap, test_key_matches_grader, test_miss_shows_answer, test_no_key_meaning_decoy, test_pairs_one_meaning, test_no_repair_of_right
Expected: The grader should correctly identify the answer as correct, provide the appropriate correction, and not return None for these cases.
Actual: The grader returns "not yet" with correction None for all the above scenarios.
Suggested fix: Refactor the grading function to: 1) normalize tokens (lowercase, strip punctuation) before comparison; 2) allow word order flexibility for swap tests; 3) treat duplicate tiles as valid by checking token counts; 4) update key matching logic to use the stored ID order rather than the first occurrence; 5) add comprehensive unit tests for these edge cases to prevent regression.
```

---
## 16. `syn-api-failed_testcase-007`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: wrong endpoint in test

**Input the assistant saw**
```
DESCRIPTION: List users
LOGS:
E       assert 404 == 200
E        +  where 404 = <Response [404]>.status_code
Response body: {"detail": "Not Found"}
FAILED tests/api/test_users.py::test_list_users
File "tests/api/test_users.py", line 54, in test_list_users
CODE:
def test_list_users(api_client):
    r = api_client.get("/api/user-list")
    assert r.status_code == 200
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test requests the wrong URL – the API endpoint is not registered at /api/user-list, so the request returns 404.
Suggestions:
  - {'issue': 'Endpoint path mismatch', 'fix': 'Update the test to use the correct route defined in the application (e.g., /api/users or /api/user-list/ if a trailing slash is required).'}
  - {'issue': 'Missing trailing slash', 'fix': 'If the router is defined with a trailing slash, adjust the request to include it: api_client.get("/api/user-list/")'}
Changes made:
  - Replaced incorrect URL '/api/user-list' with correct '/api/users'
  - Added descriptive assertion messages and basic payload validation
Improved code:
def test_list_users(api_client):
    """Verify that the user list endpoint returns a 200 status.

    The original test used the wrong URL (``/api/user-list``) which caused a
    404 response.  The correct endpoint is ``/api/users`` – the plural form
    that is registered in the router.  Using the proper URL ensures the test
    exercises the intended view.
    """
    # Use the correct endpoint for listing users
    response = api_client.get("/api/users")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    # Optionally validate the response payload
    assert isinstance(response.json(), list), "Response should be a JSON list"
    # Ensure each item has the expected keys
    for user in response.json():
        assert "id" in user and "username" in user
```

---
## 17. `syn-db-failed_testcase-009`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: wrong table in test

**Input the assistant saw**
```
DESCRIPTION: Count rows in invoices after seeding
LOGS:
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "invoice" does not exist
LINE 1: SELECT COUNT(*) FROM invoice
FAILED tests/db/test_invoices.py::test_seed_invoices
File "tests/db/test_invoices.py", line 41
CODE:
def test_seed_invoices(db_session, seed_data):
    count = db_session.execute(text("SELECT COUNT(*) FROM invoice")).scalar()
    assert count == 3
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test queries a non‑existent table named "invoice" instead of the actual table name "invoices".
Suggestions:
  - {'issue': 'Wrong table name in raw SQL query', 'fix': 'Replace "invoice" with the correct table name "invoices" (or use the ORM model).'}
  - {'issue': 'Hard‑coded SQL string makes the test fragile', 'fix': 'Use SQLAlchemy’s select() with the Invoice model to count rows, ensuring the query adapts to schema changes.'}
Changes made:
  - Replaced "invoice" with "invoices" in the SQL query
Improved code:
def test_seed_invoices(db_session, seed_data):
    # Use the actual table name "invoices" instead of the non‑existent "invoice"
    count = db_session.execute(text("SELECT COUNT(*) FROM invoices")).scalar()
    assert count == 3
```

---
## 18. `syn-playwright-failed_testcase-003`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: missing await navigation

**Input the assistant saw**
```
DESCRIPTION: After login the user lands on the Search page
LOGS:
E       AssertionError: assert False
E        +  where False = <built-in method endswith of str object>('/search')
E        +    where 'https://app/login' = <Page url='https://app/login'>.url
FAILED tests/e2e/test_auth.py::test_login_redirects_to_search[webkit]
File "tests/e2e/test_auth.py", line 119, in test_login_redirects_to_search
CODE:
def test_login_redirects_to_search(page: Page):
    page.goto("https://qa.app.internal/login")
    page.fill("#email", "qa@example.com")
    page.fill("#password", "Secret123!")
    page.click("#submit-btn")
    assert page.url.endswith("/search")
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test asserts the URL immediately after clicking the login button without waiting for the navigation to complete, causing the assertion to run while still on the login page.
Suggestions:
  - {'issue': 'No wait for navigation after login', 'fix': 'Add a wait for the URL to change to the search page before asserting, e.g., page.wait_for_url("**/search") or page.wait_for_load_state("networkidle") after clicking the submit button.'}
  - {'issue': 'Potential selector mismatch', 'fix': "Verify that '#submit-btn' is the correct selector; if not, update it to the actual button ID used by the application."}
  - {'issue': 'Hard‑coded base URL', 'fix': "Use the same base URL that the application redirects to (e.g., 'https://app/login') or configure the test environment to match the internal domain."}
Changes made:
  - Used page.expect_navigation() to wait for navigation after clicking submit
  - Added descriptive comments and a helpful assertion message
  - Provided optional wait_for_url alternative
Improved code:
def test_login_redirects_to_search(page: Page):
    # Navigate to the login page
    page.goto("https://qa.app.internal/login")

    # Fill in credentials
    page.fill("#email", "qa@example.com")
    page.fill("#password", "Secret123!")

    # Click the submit button and wait for navigation to finish
    with page.expect_navigation():
        page.click("#submit-btn")

    # Alternatively, you can wait for the URL to match the expected pattern
    # page.wait_for_url("**/search")

    # Assert that the final URL ends with /search
    assert page.url.endswith("/search"), f"Unexpected URL: {page.url}"
```

---
## 19. `syn-selenium-failed_testcase-003`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: outdated expected text

**Input the assistant saw**
```
DESCRIPTION: Button label on Sign up page (copy was updated in the last release notes)
LOGS:
E       AssertionError: assert 'Continue' == 'Proceed'
E         - Proceed
E         + Continue
FAILED tests/ui/test_signup.py::test_signup_button_label
File "tests/ui/test_signup.py", line 50, in test_signup_button_label
CODE:
def test_signup_button_label(driver):
    driver.get("https://127.0.0.1:5000/signup")
    label = driver.find_element(By.CSS_SELECTOR, "button.primary").text
    assert label == "Proceed"
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test expects the button text to be "Proceed", but the UI has been updated to display "Continue". The assertion is therefore incorrect and causes the failure.
Suggestions:
  - {'issue': 'Hard‑coded expected label is stale', 'fix': 'Update the expected value to match the current UI text, e.g. assert label == "Continue" or use a more flexible check such as assert "Continue" in label'}
  - {'issue': 'No explicit wait before locating the button', 'fix': 'Add a short explicit wait (e.g., WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button.primary")))) to ensure the element is present before reading its text'}
Changes made:

Improved code:
{"improved_code":"from selenium.webdriver.common.by import By; from selenium.webdriver.support.ui import WebDriverWait; from selenium.webdriver.support import expected_conditions as EC; def test_signup_button_label(driver): driver.get('https://127.0.0.1:5000/signup'); wait=WebDriverWait(driver,10); label=wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,'button.primary'))).text; assert label=='Continue'","changes_made":["Updated expected button text from 'Proceed' to 'Continue'","Implemented explicit wait for button visibility instead of implicit sleep"],"best_practices":["Use explicit waits (WebDriverWait) over time.sleep","Prefer reliable locators (ID > CSS > XPath) and avoid brittle selectors"],"alternative_approaches":[{"name":"Page Object Model (POM)","code":"class SignupPage:\n    def __init__(self, driver):\n        self.driver = driver\n        self.url = 'https://127.0.0.1:5000/signup'\n        self.button_locator = (By.CSS_SELECTOR, 'button.primary')\n\n    def load(self):\n        self.driver.get(self.url)\n\n    def get_button_text(self):\n        wait = WebDriverWait(self.driver, 10)\n        button = wait.until(EC.visibility_of_element_located(self.button_locator))\n        return button.text\n\n# Usage in test\n# def test_signup_button_label(driver):\n#     page = SignupPage(driver)\n#     page.load()\n#     assert page.get_button_text() == 'Continue'","when_to_use":"When test suite grows and you want to separate page interactions from test logic for maintainability"},"resources":["https://selenium.dev/documentation/webdriver/waits/","https://selenium.dev/documentation/webdriver/page_objects/"]}
```

---
## 20. `syn-unit-failed_testcase-003`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: float equality

**Input the assistant saw**
```
DESCRIPTION: apply_coupon result for small values
LOGS:
E       assert 0.30000000000000004 == 0.3
E        +  where 0.30000000000000004 = apply_coupon(0.1, 3)

FAILED tests/unit/test_cart.py::test_apply_coupon_small_values
File "tests/unit/test_cart.py", line 88, in test_apply_coupon_small_values
CODE:
from app.cart import apply_coupon

def test_apply_coupon_small_values():
    assert apply_coupon(0.1, 3) == 0.3
```

**Output to score**
```
FIX SUGGESTION
Root cause: Floating point arithmetic produces a tiny precision error, causing the test to fail on exact equality.
Suggestions:
  - {'issue': 'apply_coupon returns a float that may have rounding errors (e.g., 0.30000000000000004 instead of 0.3).', 'fix': 'Modify the function to round the result to a fixed number of decimal places (e.g., round(total, 2)) or use Decimal for precise arithmetic.'}
  - {'issue': 'The test uses strict equality (==) which is unsuitable for floating point comparisons.', 'fix': 'Change the test to use pytest.approx or round the result before comparison.'}
Changes made:
  - Replaced exact equality with pytest.approx to handle floating point precision
Improved code:
from app.cart import apply_coupon
import pytest

def test_apply_coupon_small_values():
    assert apply_coupon(0.1, 3) == pytest.approx(0.3)
```

---
## 21. `syn-db-failed_testcase-003`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: wrong table in test

**Input the assistant saw**
```
DESCRIPTION: Count rows in products after seeding
LOGS:
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "product" does not exist
LINE 1: SELECT COUNT(*) FROM product
FAILED tests/db/test_products.py::test_seed_products
File "tests/db/test_products.py", line 38
CODE:
def test_seed_products(db_session, seed_data):
    count = db_session.execute(text("SELECT COUNT(*) FROM product")).scalar()
    assert count == 3
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test queries a non‑existent table name "product" instead of the actual table created by the fixture.
Suggestions:
  - {'issue': 'Hardcoded wrong table name in SQL query', 'fix': 'Replace "product" with the correct table name (likely "products") or use the ORM/Table metadata to reference the table.'}
  - {'issue': 'Test relies on a literal table name', 'fix': 'Use the fixture or SQLAlchemy metadata to obtain the table name dynamically, e.g., `db_session.execute(text(f"SELECT COUNT(*) FROM {Product.__tablename__}"))`.'}
Changes made:
  - Corrected table name from 'product' to 'products'
  - Replaced raw SQL with a clearer query using the correct table
Improved code:
from sqlalchemy import text


def test_seed_products(db_session, seed_data):
    # Use the correct table name that the fixture creates.
    # Prefer an ORM query if a Product model is available.
    count = db_session.execute(text("SELECT COUNT(*) FROM products")).scalar()
    assert count == 3
```

---
## 22. `syn-playwright-failed_testcase-015`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: missing await navigation

**Input the assistant saw**
```
DESCRIPTION: After login the user lands on the Cart page
LOGS:
E       AssertionError: assert False
E        +  where False = <built-in method endswith of str object>('/cart')
E        +    where 'https://app/login' = <Page url='https://app/login'>.url
FAILED tests/e2e/test_auth.py::test_login_redirects_to_cart[webkit]
File "tests/e2e/test_auth.py", line 126, in test_login_redirects_to_cart
CODE:
def test_login_redirects_to_cart(page: Page):
    page.goto("https://qa.app.internal/login")
    page.fill("#email", "qa@example.com")
    page.fill("#password", "Secret123!")
    page.click("#submit-btn")
    assert page.url.endswith("/cart")
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test asserts the URL immediately after clicking submit, without waiting for the navigation to complete, so it checks the pre‑redirect URL.
Suggestions:
  - {'issue': 'No wait for navigation after form submission', 'fix': 'Use Playwright’s navigation helpers (e.g., page.wait_for_url or page.expect_navigation) before asserting the URL.'}
  - {'issue': 'Hard‑coded URL may not match the actual environment', 'fix': 'Verify that the base URL used in page.goto matches the test environment; if not, update it to the correct domain.'}
Changes made:
  - Added explicit wait for navigation using page.wait_for_url
  - Removed immediate assertion that could run before navigation completes
Improved code:
def test_login_redirects_to_cart(page: Page):
    # Navigate to the login page
    page.goto("https://qa.app.internal/login")

    # Fill in credentials
    page.fill("#email", "qa@example.com")
    page.fill("#password", "Secret123!")

    # Click submit and wait for the navigation to finish
    page.click("#submit-btn")
    # Explicitly wait for the URL to contain the cart path
    page.wait_for_url("**/cart")

    # Assert that we are on the cart page
    assert page.url.endswith("/cart")
```

---
## 23. `syn-selenium-failed_testcase-009`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: outdated expected text

**Input the assistant saw**
```
DESCRIPTION: Button label on Orders page (copy was updated in the last release notes)
LOGS:
E       AssertionError: assert 'Save' == 'Submit'
E         - Submit
E         + Save
FAILED tests/ui/test_orders.py::test_orders_button_label
File "tests/ui/test_orders.py", line 45, in test_orders_button_label
CODE:
def test_orders_button_label(driver):
    driver.get("https://staging.shop.local/orders")
    label = driver.find_element(By.CSS_SELECTOR, "button.primary").text
    assert label == "Submit"
```

**Output to score**
```
FIX SUGGESTION
Root cause: Test expectation is stale – the button label was updated to "Save" in the latest release, but the test still asserts "Submit".
Suggestions:
  - {'issue': 'Hard‑coded expected label is out of sync with UI', 'fix': 'Update the assertion to match the new label or use a data‑driven approach that pulls the expected text from a config or translation file'}
  - {'issue': 'No explicit wait – could fail on slow page load', 'fix': 'Add a WebDriverWait for the button to be visible before reading its text'}
Changes made:
  - Updated expected button label from 'Submit' to 'Save' to match current UI
  - Replaced implicit wait with explicit WebDriverWait for element visibility
  - Used reliable CSS selector and added timeout handling
Improved code:
def test_orders_button_label(driver): from selenium.webdriver.common.by import By; from selenium.webdriver.support.ui import WebDriverWait; from selenium.webdriver.support import expected_conditions as EC; driver.get("https://staging.shop.local/orders"); wait=WebDriverWait(driver,10); button=wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,"button.primary"))); assert button.text=="Save"
```

---
## 24. `syn-unit-failed_testcase-012`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: float equality

**Input the assistant saw**
```
DESCRIPTION: apply_coupon result for small values
LOGS:
E       assert 0.7000000000000001 == 0.7
E        +  where 0.7000000000000001 = apply_coupon(0.1, 3)

FAILED tests/unit/test_cart.py::test_apply_coupon_small_values
File "tests/unit/test_cart.py", line 24, in test_apply_coupon_small_values
CODE:
from app.cart import apply_coupon

def test_apply_coupon_small_values():
    assert apply_coupon(0.1, 3) == 0.7
```

**Output to score**
```
FIX SUGGESTION
Root cause: Floating‑point arithmetic returns 0.7000000000000001 instead of 0.7, causing a strict equality check to fail.
Suggestions:
  - {'issue': 'apply_coupon uses raw float math without rounding, leading to precision errors.', 'fix': 'Modify apply_coupon to round the result to two decimal places (e.g., return round(price * (1 - discount), 2)) or use Decimal for exact arithmetic.'}
Changes made:
  - Replaced strict equality with pytest.approx for floating‑point comparison
  - Imported pytest to access approx
Improved code:
from app.cart import apply_coupon
import pytest

def test_apply_coupon_small_values():
    result = apply_coupon(0.1, 3)
    assert result == pytest.approx(0.7, rel=1e-9)
```

---
## 25. `syn-api-failed_testcase-001`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: wrong endpoint in test

**Input the assistant saw**
```
DESCRIPTION: List invoices
LOGS:
E       assert 404 == 200
E        +  where 404 = <Response [404]>.status_code
Response body: {"detail": "Not Found"}
FAILED tests/api/test_invoices.py::test_list_invoices
File "tests/api/test_invoices.py", line 104, in test_list_invoices
CODE:
def test_list_invoices(api_client):
    r = api_client.get("/api/invoice-list")
    assert r.status_code == 200
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test requests an endpoint that does not exist in the application, causing a 404 response.
Suggestions:
  - {'issue': "Endpoint path mismatch – the test uses '/api/invoice-list' while the actual route is likely '/api/invoices' (or '/api/invoice-list/')", 'fix': 'Update the test to call the correct URL that matches the route defined in the FastAPI router.'}
  - {'issue': 'Router may not be included in the main FastAPI app used by the test client', 'fix': "Ensure the invoices router is imported and included in the main app with the correct prefix, e.g., app.include_router(invoice_router, prefix='/api')"}
Changes made:
  - Replaced incorrect endpoint '/api/invoice-list' with correct '/api/invoices',
Added descriptive docstring, used ``response.ok`` for readability,
Parsed JSON and asserted it is a list.
Improved code:
def test_list_invoices(api_client):
    """Verify that the invoice list endpoint returns a successful response.

    The original test used the non‑existent ``/api/invoice-list`` path which
    caused a 404.  The correct RESTful path is ``/api/invoices``.
    """
    response = api_client.get("/api/invoices")
    # ``response.ok`` is a shortcut for status_code == 200
    assert response.ok, f"Unexpected status code: {response.status_code}"
    # Optionally validate that the response contains a JSON array
    data = response.json()
    assert isinstance(data, list), "Expected a list of invoices"
    # If the API guarantees at least one invoice, you can add a further check
    # assert len(data) > 0, "Invoice list should not be empty"
```

---
## 26. `syn-db-failed_testcase-012`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: wrong table in test

**Input the assistant saw**
```
DESCRIPTION: Count rows in users after seeding
LOGS:
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "user" does not exist
LINE 1: SELECT COUNT(*) FROM user
FAILED tests/db/test_users.py::test_seed_users
File "tests/db/test_users.py", line 79
CODE:
def test_seed_users(db_session, seed_data):
    count = db_session.execute(text("SELECT COUNT(*) FROM user")).scalar()
    assert count == 3
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test queries a non‑existent table named "user" instead of the actual table "users" created by the ORM.
Suggestions:
  - {'issue': 'Incorrect table name in raw SQL query', 'fix': 'Replace the raw SQL with the correct table name: SELECT COUNT(*) FROM users'}
  - {'issue': 'Hard‑coded SQL string makes the test fragile', 'fix': 'Use SQLAlchemy ORM to count rows: db_session.query(User).count()'}
Changes made:
  - Replaced raw SQL query against non‑existent table with ORM query using User model
  - Added descriptive docstring and assertion message
Improved code:
def test_seed_users(db_session, seed_data):
    """Verify that the seed data inserted the expected number of users.

    The original test used a raw SQL query against a table named ``user`` which
    does not exist in the database.  The ORM model is called ``User`` and the
    underlying table is ``users``.  Using the ORM keeps the test database‑agnostic
    and avoids hard‑coding table names.
    """
    # Count rows via the ORM instead of raw SQL
    count = db_session.query(User).count()
    assert count == 3, f"Expected 3 users, found {count}"
```

---
## 27. `syn-playwright-failed_testcase-006`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: missing await navigation

**Input the assistant saw**
```
DESCRIPTION: After login the user lands on the Profile page
LOGS:
E       AssertionError: assert False
E        +  where False = <built-in method endswith of str object>('/profile')
E        +    where 'https://app/login' = <Page url='https://app/login'>.url
FAILED tests/e2e/test_auth.py::test_login_redirects_to_profile[webkit]
File "tests/e2e/test_auth.py", line 13, in test_login_redirects_to_profile
CODE:
def test_login_redirects_to_profile(page: Page):
    page.goto("https://qa.app.internal/login")
    page.fill("#email", "qa@example.com")
    page.fill("#password", "Secret123!")
    page.click("#submit-btn")
    assert page.url.endswith("/profile")
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test does not wait for the navigation to complete after clicking the submit button, so the assertion checks the URL before the redirect occurs.
Suggestions:
  - {'issue': 'Missing wait for navigation after form submission', 'fix': 'Add a wait for the URL to match the profile page before asserting, e.g. `page.wait_for_url("**/profile")` or `page.wait_for_load_state("networkidle")` after the click.'}
  - {'issue': 'Hard‑coded URL in assertion may fail if the domain changes', 'fix': 'Keep the assertion simple (`endswith("/profile")`) but ensure the base URL is correct; consider using a fixture for the base URL.'}
  - {'issue': 'Potential race condition if the page loads slowly', 'fix': 'Specify a reasonable timeout in the wait call, e.g. `page.wait_for_url("**/profile", timeout=5000)`.'}
Changes made:
  - Added explicit navigation wait using page.expect_navigation
  - Used parametrize to run test across browsers
  - Added descriptive assertion message
Improved code:
import pytest
from playwright.sync_api import Page

@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
def test_login_redirects_to_profile(page: Page, browser_name: str):
    """Verify that a successful login redirects to the profile page.

    The test now waits for the navigation to complete after clicking the submit
    button, ensuring the URL assertion is performed on the final page.
    """
    # Navigate to the login page
    page.goto("https://qa.app.internal/login")

    # Fill in credentials
    page.fill("#email", "qa@example.com")
    page.fill("#password", "Secret123!")

    # Click the submit button and wait for navigation to finish
    with page.expect_navigation(url="**/profile"):
        page.click("#submit-btn")

    # Assert that the current URL ends with /profile
    assert page.url.endswith("/profile"), f"Unexpected URL: {page.url}"
```

---
## 28. `syn-selenium-failed_testcase-006`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: outdated expected text

**Input the assistant saw**
```
DESCRIPTION: Button label on Sign up page (copy was updated in the last release notes)
LOGS:
E       AssertionError: assert 'Log in' == 'Sign In'
E         - Sign In
E         + Log in
FAILED tests/ui/test_signup.py::test_signup_button_label
File "tests/ui/test_signup.py", line 34, in test_signup_button_label
CODE:
def test_signup_button_label(driver):
    driver.get("https://localhost:8000/signup")
    label = driver.find_element(By.CSS_SELECTOR, "button.primary").text
    assert label == "Sign In"
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test expects the button label to be "Sign In" while the actual UI displays "Log in". This mismatch indicates that the test was written against an older copy of the page and has not been updated to reflect the recent UI change.
Suggestions:
  - {'issue': 'Hard‑coded expected text that is out of sync with the UI', 'fix': 'Update the assertion to match the current button label, e.g. assert label == "Log in"'}
  - {'issue': 'No explicit wait – the test may run before the button is fully rendered', 'fix': 'Wrap the element lookup in a WebDriverWait that waits for the button to be visible and enabled before reading its text'}
Changes made:
  - Updated expected label to match UI
  - Added explicit wait for button visibility
  - Used CSS selector with WebDriverWait instead of find_element directly
Improved code:
def test_signup_button_label(driver): from selenium.webdriver.common.by import By; from selenium.webdriver.support.ui import WebDriverWait; from selenium.webdriver.support import expected_conditions as EC; driver.get('https://localhost:8000/signup'); wait=WebDriverWait(driver,10); button=wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,'button.primary'))); assert button.text=='Log in'
```

---
## 29. `syn-unit-failed_testcase-009`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: float equality

**Input the assistant saw**
```
DESCRIPTION: compute_shipping result for small values
LOGS:
E       assert 0.30000000000000004 == 0.3
E        +  where 0.30000000000000004 = compute_shipping(0.1, 3)

FAILED tests/unit/test_shipping.py::test_compute_shipping_small_values
File "tests/unit/test_shipping.py", line 70, in test_compute_shipping_small_values
CODE:
from app.shipping import compute_shipping

def test_compute_shipping_small_values():
    assert compute_shipping(0.1, 3) == 0.3
```

**Output to score**
```
FIX SUGGESTION
Root cause: Floating‑point arithmetic produces a tiny rounding error, causing the test to compare 0.30000000000000004 with 0.3.
Suggestions:
  - {'issue': 'Using == for floating‑point comparison', 'fix': 'Replace the equality assertion with pytest.approx or round the result to a fixed precision'}
  - {'issue': 'Test is too strict for floating‑point values', 'fix': 'Adjust the test to allow a small tolerance, e.g., assert compute_shipping(0.1, 3) == pytest.approx(0.3)'}
Changes made:
  - Replaced direct equality with pytest.approx for floating‑point comparison
  - Imported pytest to access approx
Improved code:
import pytest
from app.shipping import compute_shipping


def test_compute_shipping_small_values():
    # Use pytest.approx to allow for floating‑point rounding errors
    assert compute_shipping(0.1, 3) == pytest.approx(0.3)
```

---
## 30. `syn-api-failed_testcase-013`  (failed_testcase)

**Reference:** the TEST is wrong (test code, test data or test environment); injected fault: wrong endpoint in test

**Input the assistant saw**
```
DESCRIPTION: List users
LOGS:
E       assert 404 == 200
E        +  where 404 = <Response [404]>.status_code
Response body: {"detail": "Not Found"}
FAILED tests/api/test_users.py::test_list_users
File "tests/api/test_users.py", line 81, in test_list_users
CODE:
def test_list_users(api_client):
    r = api_client.get("/api/user")
    assert r.status_code == 200
```

**Output to score**
```
FIX SUGGESTION
Root cause: The test requests the wrong endpoint path, causing a 404 response.
Suggestions:
  - {'issue': 'Endpoint path mismatch – the API defines the users list at /api/users (or similar), not /api/user.', 'fix': 'Update the test to call the correct path, e.g., /api/users or /api/users/ depending on the actual route definition.'}
  - {'issue': 'If the API requires authentication, the test should include the necessary auth headers; however, a 404 indicates the route itself is missing rather than an auth issue.', 'fix': 'Verify the route exists in the application code and adjust the test accordingly.'}
Changes made:
  - Changed endpoint from '/api/user' to '/api/users'
  - Added descriptive assertion message and optional JSON type check
Improved code:
def test_list_users(api_client):
    """Verify that the user list endpoint returns a 200 status code.

    The original test used the wrong URL (``/api/user``) which resulted in a
    404 response.  The correct endpoint is ``/api/users``.
    """
    response = api_client.get("/api/users")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    # Optional: verify that the response contains a list of users
    assert isinstance(response.json(), list), "Response body is not a list"
```
