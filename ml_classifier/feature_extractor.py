import re
import numpy as np

FAILED_TC_KEYWORDS = [
    'nosuchelementexception', 'elementnotfound', 'nosuchelement',
    'timeoutexception', 'staleelementreferenceexception',
    'elementclickinterceptedexception', 'elementnotinteractableexception',
    'invalidselectorexception', 'nosuchwindowexception',
    'movetargetoutofboundsexception', 'xpathevalerror',
    'webdriverexception', 'modulenotfounderror',
    'jsondecodeerror', 'connectionrefusederror',
    'improperlyconfigured', 'unicodedecodeerror',
    'operationalerror: no such table',
    'invalid xpath', 'invalid css selector',
    'no such window', 'chrome not reachable',
    'no such column', 'no such table',
    'session not created', 'no module named',
    'max retries exceeded', 'connection refused'
]

BUG_KEYWORDS = [
    '500 server error', 'internal server error',
    'nullpointerexception', 'nullreferenceexception',
    'integrityerror', 'cascade',
    'wrong amount', 'wrong total', 'wrong user',
    'not persisting', 'not deducted', 'not converting',
    'still active', 'sent twice', 'duplicate record',
    'balance not', 'currency not', 'role not assigned',
    'returns error for valid', 'forbidden on admin',
    '0 bytes', 'empty file',
    'not enforced', 'bypass', 'not updated',
    'not saved', 'not deleted', 'not created'
]

# NEW: Gray area keywords that help disambiguate
TEST_SETUP_KEYWORDS = [
    'already exists', 'duplicate email', 'test data',
    'teardown', 'setup', 'fixture', 'conftest',
    'missing limit', 'missing param', 'wrong param',
    'environment', 'config', 'not running',
    'pagination', 'missing header'
]

def extract_features(logs: str, description: str, code: str) -> np.ndarray:
    logs_lower = logs.lower()
    desc_lower = description.lower()
    code_lower = code.lower()
    combined = f"{logs_lower} {desc_lower} {code_lower}"

    features = []

    # Group 1: Exception type indicators
    features.append(1 if 'nosuchelementexception' in logs_lower else 0)
    features.append(1 if 'timeoutexception' in logs_lower else 0)
    features.append(1 if 'staleelementreferenceexception' in logs_lower else 0)
    features.append(1 if 'elementclickinterceptedexception' in logs_lower else 0)
    features.append(1 if 'elementnotinteractableexception' in logs_lower else 0)
    features.append(1 if 'assertionerror' in logs_lower else 0)
    features.append(1 if '500' in logs_lower or 'internal server error' in logs_lower else 0)
    features.append(1 if 'nullpointerexception' in logs_lower else 0)
    features.append(1 if 'integrityerror' in logs_lower else 0)
    features.append(1 if 'connectionrefusederror' in logs_lower or 'max retries exceeded' in logs_lower else 0)
    features.append(1 if 'jsondecodeerror' in logs_lower else 0)
    features.append(1 if 'modulenotfounderror' in logs_lower else 0)
    features.append(1 if 'operationalerror' in logs_lower else 0)
    features.append(1 if 'webdriverexception' in logs_lower else 0)

    # Group 2: Framework detection
    features.append(1 if 'selenium' in combined or 'webdriver' in combined or 'driver.' in code_lower else 0)
    features.append(1 if 'requests.' in code_lower or 'status_code' in code_lower else 0)
    features.append(1 if 'db.' in code_lower or 'query(' in code_lower else 0)
    features.append(1 if 'by.id' in code_lower or 'by.xpath' in code_lower else 0)
    features.append(1 if 'webdriverwait' in code_lower else 0)
    features.append(1 if 'pytest' in combined or 'def test_' in code_lower else 0)

    # Group 3: Bug indicators
    features.append(1 if any(kw in logs_lower for kw in BUG_KEYWORDS) else 0)
    features.append(1 if 'valid' in desc_lower and ('error' in logs_lower or 'wrong' in logs_lower) else 0)
    features.append(1 if 'redirect' in desc_lower and 'assertionerror' in logs_lower else 0)
    features.append(1 if '0 bytes' in logs_lower or 'empty file' in logs_lower else 0)
    features.append(1 if 'duplicate' in logs_lower or 'twice' in logs_lower else 0)
    features.append(1 if 'not persisting' in logs_lower or 'not deducted' in logs_lower else 0)
    features.append(1 if '403' in logs_lower or 'forbidden' in logs_lower else 0)
    features.append(1 if '401' in logs_lower and '200' in logs_lower else 0)

    # Group 4: Failed testcase indicators
    features.append(1 if any(kw in logs_lower for kw in FAILED_TC_KEYWORDS) else 0)
    features.append(1 if 'invalid' in logs_lower and 'selector' in logs_lower else 0)
    features.append(1 if 'locator' in desc_lower or 'selector' in desc_lower else 0)
    features.append(1 if 'no such table' in logs_lower or 'no such column' in logs_lower else 0)
    features.append(1 if 'chrome not reachable' in logs_lower else 0)

    # Group 5: Code patterns
    features.append(1 if 'find_element' in code_lower else 0)
    features.append(1 if 'assert' in code_lower else 0)
    features.append(len(re.findall(r'assert', code_lower)))
    features.append(1 if 'time.sleep' in code_lower else 0)
    features.append(1 if 'hardcoded' in desc_lower else 0)
    features.append(len(code.split('\n')))

    # Group 6: Description hints
    features.append(1 if 'verif' in desc_lower and 'redirect' in desc_lower else 0)
    features.append(1 if 'verif' in desc_lower and 'total' in desc_lower else 0)
    features.append(1 if 'click' in desc_lower else 0)
    features.append(1 if 'api' in desc_lower or 'endpoint' in desc_lower else 0)
    features.append(1 if 'database' in desc_lower or 'db' in desc_lower else 0)

    # Group 7: NEW gray area features
    features.append(1 if any(kw in combined for kw in TEST_SETUP_KEYWORDS) else 0)
    features.append(1 if 'already exists' in logs_lower else 0)
    features.append(1 if 'connection' in logs_lower and 'refused' in logs_lower else 0)
    features.append(1 if 'missing' in desc_lower or 'wrong param' in desc_lower else 0)
    features.append(1 if 'not running' in desc_lower or 'environment' in desc_lower else 0)
    features.append(1 if 'pagination' in desc_lower or 'limit' in desc_lower else 0)
    features.append(1 if 'teardown' in combined or 'cleanup' in combined else 0)
    features.append(1 if 'existing' in logs_lower and 'email' in logs_lower else 0)

    return np.array(features, dtype=float)

def get_feature_names() -> list:
    return [
        'has_nosuchelement', 'has_timeout', 'has_stale',
        'has_click_intercepted', 'has_not_interactable',
        'has_assertion_error', 'has_500_error', 'has_null_pointer',
        'has_integrity_error', 'has_connection_refused',
        'has_json_decode_error', 'has_module_not_found',
        'has_operational_error', 'has_webdriver_exception',
        'is_selenium_test', 'is_api_test', 'is_db_test',
        'uses_by_locator', 'uses_webdriverwait', 'uses_pytest',
        'has_bug_keywords', 'valid_but_error', 'redirect_assertion',
        'empty_file', 'duplicate_or_twice', 'not_persisting',
        'has_403', 'auth_bypass_bug',
        'has_failed_tc_keywords', 'invalid_locator',
        'locator_in_desc', 'no_such_table', 'driver_not_ready',
        'uses_find_element', 'has_assert', 'assertion_count',
        'uses_sleep', 'has_hardcoded', 'code_length',
        'login_redirect_verify', 'total_verify',
        'has_click_action', 'is_api_desc', 'is_db_desc',
        'has_test_setup_keywords', 'has_already_exists',
        'has_connection_refused_logs', 'has_missing_param',
        'has_env_issue', 'has_pagination', 'has_teardown',
        'has_existing_email'
    ]