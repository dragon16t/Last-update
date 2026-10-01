#!/usr/bin/env python3
"""
Backend API Test Suite for Celesta Glow E-commerce
Tests core storefront public endpoints (no auth required)
"""
import requests
import sys
import json
from typing import Dict, Any, List

# Base URL from frontend/.env
BASE_URL = "https://ecom-preview-16.preview.emergentagent.com/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []

    def add_pass(self):
        self.passed += 1

    def add_fail(self, error: str):
        self.failed += 1
        self.errors.append(error)

    def add_warning(self):
        self.warnings += 1

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  - {error}")
        if self.warnings > 0:
            print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")
        print("="*60)
        return self.failed == 0

results = TestResults()

def test_endpoint(name: str, url: str, expected_status: int = 200, 
                  validate_fn=None, critical: bool = True) -> Dict[str, Any]:
    """Test a single endpoint"""
    print(f"\n{Colors.BLUE}Testing: {name}{Colors.END}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code != expected_status:
            error_msg = f"{name} - Expected {expected_status}, got {response.status_code}"
            print_error(error_msg)
            if critical:
                results.add_fail(error_msg)
            else:
                results.add_warning()
            return {"success": False, "status": response.status_code, "data": None}
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            # For image endpoints, just check if we got content
            if "uploads" in url:
                if response.content:
                    print_success(f"{name} - Image returned successfully ({len(response.content)} bytes)")
                    results.add_pass()
                    return {"success": True, "status": response.status_code, "data": response.content}
                else:
                    error_msg = f"{name} - No content returned"
                    print_error(error_msg)
                    results.add_fail(error_msg)
                    return {"success": False, "status": response.status_code, "data": None}
            else:
                error_msg = f"{name} - Invalid JSON response"
                print_error(error_msg)
                results.add_fail(error_msg)
                return {"success": False, "status": response.status_code, "data": None}
        
        # Run custom validation if provided
        if validate_fn:
            validation_result = validate_fn(data)
            if validation_result["success"]:
                print_success(f"{name} - {validation_result['message']}")
                results.add_pass()
            else:
                error_msg = f"{name} - {validation_result['message']}"
                print_error(error_msg)
                if critical:
                    results.add_fail(error_msg)
                else:
                    results.add_warning()
                return {"success": False, "status": response.status_code, "data": data}
        else:
            print_success(f"{name} - Response OK")
            results.add_pass()
        
        return {"success": True, "status": response.status_code, "data": data}
        
    except requests.exceptions.Timeout:
        error_msg = f"{name} - Request timeout"
        print_error(error_msg)
        results.add_fail(error_msg)
        return {"success": False, "status": None, "data": None}
    except requests.exceptions.RequestException as e:
        error_msg = f"{name} - Request failed: {str(e)}"
        print_error(error_msg)
        results.add_fail(error_msg)
        return {"success": False, "status": None, "data": None}

def validate_products_list(data: Any) -> Dict[str, Any]:
    """Validate products list response"""
    # Check if it's paginated response or plain array
    if isinstance(data, dict) and "items" in data:
        products = data.get("items", [])
        total = data.get("total", 0)
        print_info(f"Paginated response: {len(products)} items, total: {total}")
    elif isinstance(data, list):
        products = data
        print_info(f"Array response: {len(products)} items")
    else:
        return {"success": False, "message": "Invalid response format"}
    
    if not products:
        return {"success": False, "message": "No products returned"}
    
    # Check for expected base products
    product_names = [p.get("name", "") for p in products]
    expected_products = ["Vitamin E", "Vitamin C", "Vitamin A", "Benzoyl Peroxide"]
    found_count = sum(1 for exp in expected_products if any(exp in name for name in product_names))
    
    print_info(f"Found {found_count}/4 expected base products")
    
    # Check product structure
    first_product = products[0]
    required_fields = ["slug", "name", "images", "prepaid_price"]
    missing_fields = [f for f in required_fields if f not in first_product]
    
    if missing_fields:
        return {"success": False, "message": f"Missing fields: {missing_fields}"}
    
    # Check for variation_count
    has_variation_count = any(p.get("variation_count") for p in products)
    if has_variation_count:
        print_info("Products have variation_count field")
    
    return {"success": True, "message": f"Valid products list with {len(products)} items"}

def validate_product_detail(data: Any) -> Dict[str, Any]:
    """Validate single product detail response"""
    if not isinstance(data, dict):
        return {"success": False, "message": "Invalid response format"}
    
    required_fields = ["slug", "name", "images"]
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        return {"success": False, "message": f"Missing fields: {missing_fields}"}
    
    # Check images array
    images = data.get("images", [])
    if not isinstance(images, list):
        return {"success": False, "message": "Images is not an array"}
    
    print_info(f"Product: {data.get('name')}")
    print_info(f"Images: {len(images)}")
    print_info(f"Has test_report_image: {bool(data.get('test_report_image'))}")
    print_info(f"Variation count: {data.get('variation_count', 'N/A')}")
    
    return {"success": True, "message": f"Valid product detail for {data.get('name')}"}

def validate_variations(data: Any) -> Dict[str, Any]:
    """Validate variations response"""
    if isinstance(data, dict) and "items" in data:
        variations = data.get("items", [])
    elif isinstance(data, list):
        variations = data
    else:
        return {"success": False, "message": "Invalid response format"}
    
    if not variations:
        return {"success": False, "message": "No variations returned"}
    
    print_info(f"Found {len(variations)} variations")
    
    # Check if variations have generated_from field
    has_generated_from = any(v.get("generated_from") for v in variations)
    if has_generated_from:
        print_info("Variations have generated_from field")
    
    # Expected: 24 variations (2 genders x 3 skin types x 4 age groups)
    if len(variations) == 24:
        print_info("✓ Expected 24 variations found")
    else:
        print_warning(f"Expected 24 variations, got {len(variations)}")
    
    return {"success": True, "message": f"Valid variations list with {len(variations)} items"}

def validate_certificates(data: Any) -> Dict[str, Any]:
    """Validate certificates response"""
    if not isinstance(data, list):
        return {"success": False, "message": "Invalid response format (expected array)"}
    
    if not data:
        return {"success": False, "message": "No certificates returned"}
    
    # Check that products have test_report_image
    products_with_cert = [p for p in data if p.get("test_report_image")]
    
    print_info(f"Found {len(data)} products with certificates")
    print_info(f"{len(products_with_cert)} have test_report_image")
    
    if len(products_with_cert) == 0:
        return {"success": False, "message": "No products with test_report_image"}
    
    return {"success": True, "message": f"Valid certificates list with {len(products_with_cert)} certified products"}

def validate_concerns(data: Any) -> Dict[str, Any]:
    """Validate concerns response"""
    if not isinstance(data, list):
        return {"success": False, "message": "Invalid response format (expected array)"}
    
    if not data:
        return {"success": False, "message": "No concerns returned"}
    
    print_info(f"Found {len(data)} concerns")
    
    # Check structure
    first_concern = data[0]
    required_fields = ["slug", "name"]
    missing_fields = [f for f in required_fields if f not in first_concern]
    
    if missing_fields:
        return {"success": False, "message": f"Missing fields: {missing_fields}"}
    
    # Expected ~14 concerns
    if len(data) >= 10:
        print_info("✓ Good number of concerns (>=10)")
    else:
        print_warning(f"Expected ~14 concerns, got {len(data)}")
    
    return {"success": True, "message": f"Valid concerns list with {len(data)} items"}

def validate_categories(data: Any) -> Dict[str, Any]:
    """Validate categories response"""
    if not isinstance(data, list):
        return {"success": False, "message": "Invalid response format (expected array)"}
    
    if not data:
        return {"success": False, "message": "No categories returned"}
    
    print_info(f"Found {len(data)} categories")
    
    # Check structure
    first_category = data[0]
    required_fields = ["slug", "name"]
    missing_fields = [f for f in required_fields if f not in first_category]
    
    if missing_fields:
        return {"success": False, "message": f"Missing fields: {missing_fields}"}
    
    # Expected ~38 categories
    if len(data) >= 20:
        print_info("✓ Good number of categories (>=20)")
    else:
        print_warning(f"Expected ~38 categories, got {len(data)}")
    
    return {"success": True, "message": f"Valid categories list with {len(data)} items"}

def validate_combos(data: Any) -> Dict[str, Any]:
    """Validate combos response"""
    if not isinstance(data, list):
        return {"success": False, "message": "Invalid response format (expected array)"}
    
    print_info(f"Found {len(data)} combos")
    
    # Combos may be empty, that's OK per spec
    if len(data) == 0:
        print_info("No combos (this is OK per spec)")
        return {"success": True, "message": "Valid empty combos list"}
    
    # If there are combos, check structure
    first_combo = data[0]
    required_fields = ["combo_id", "name"]
    missing_fields = [f for f in required_fields if f not in first_combo]
    
    if missing_fields:
        return {"success": False, "message": f"Missing fields: {missing_fields}"}
    
    return {"success": True, "message": f"Valid combos list with {len(data)} items"}

def validate_site_settings(data: Any) -> Dict[str, Any]:
    """Validate site settings response"""
    if not isinstance(data, dict):
        return {"success": False, "message": "Invalid response format (expected object)"}
    
    # Check for niche_settings
    has_niche_settings = "niche_settings" in data
    print_info(f"Has niche_settings: {has_niche_settings}")
    
    if has_niche_settings:
        niche_settings = data.get("niche_settings", {})
        print_info(f"Niche settings keys: {list(niche_settings.keys())}")
    
    return {"success": True, "message": "Valid site settings"}

def test_razorpay_order_creation() -> Dict[str, Any]:
    """Test Razorpay order creation (safe - no charge)"""
    print(f"\n{Colors.BLUE}Testing: Razorpay Order Creation{Colors.END}")
    url = f"{BASE_URL}/create-razorpay-order"
    payload = {"amount": 649}
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate response structure
            if "id" in data and data["id"].startswith("order_"):
                print_success(f"Razorpay order created - ID: {data['id']}, Amount: {data.get('amount')} paise, Currency: {data.get('currency')}")
                results.add_pass()
                return {"success": True, "status": response.status_code, "data": data}
            else:
                error_msg = "Razorpay Order Creation - Invalid response structure (missing order id)"
                print_error(error_msg)
                results.add_fail(error_msg)
                return {"success": False, "status": response.status_code, "data": data}
        elif response.status_code == 503:
            error_msg = "Razorpay Order Creation - Payment gateway not configured (keys not loaded)"
            print_error(error_msg)
            results.add_fail(error_msg)
            return {"success": False, "status": response.status_code, "data": None}
        else:
            error_msg = f"Razorpay Order Creation - Unexpected status {response.status_code}"
            print_error(error_msg)
            results.add_fail(error_msg)
            return {"success": False, "status": response.status_code, "data": None}
            
    except Exception as e:
        error_msg = f"Razorpay Order Creation - Exception: {str(e)}"
        print_error(error_msg)
        results.add_fail(error_msg)
        return {"success": False, "status": None, "data": None}

def test_pincode_lookup() -> Dict[str, Any]:
    """Test full pincode lookup"""
    print(f"\n{Colors.BLUE}Testing: Pincode Lookup (Full){Colors.END}")
    pincode = "682001"
    url = f"{BASE_URL}/pincode/{pincode}"
    print(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate Kerala state
            if data.get("state") and "kerala" in data.get("state", "").lower():
                print_success(f"Pincode lookup working - Pincode: {data.get('pincode')}, State: {data.get('state')}, District: {data.get('district')}")
                results.add_pass()
                return {"success": True, "status": response.status_code, "data": data}
            else:
                error_msg = f"Pincode Lookup - Expected Kerala state, got: {data.get('state')}"
                print_error(error_msg)
                results.add_fail(error_msg)
                return {"success": False, "status": response.status_code, "data": data}
        else:
            error_msg = f"Pincode Lookup - Unexpected status {response.status_code}"
            print_error(error_msg)
            results.add_fail(error_msg)
            return {"success": False, "status": response.status_code, "data": None}
            
    except Exception as e:
        error_msg = f"Pincode Lookup - Exception: {str(e)}"
        print_error(error_msg)
        results.add_fail(error_msg)
        return {"success": False, "status": None, "data": None}

def test_pincode_state_only() -> Dict[str, Any]:
    """Test state-only pincode lookup"""
    print(f"\n{Colors.BLUE}Testing: Pincode State Lookup{Colors.END}")
    pincode = "682001"
    url = f"{BASE_URL}/pincode/{pincode}/state"
    print(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate Kerala state
            if data.get("state") and "kerala" in data.get("state", "").lower():
                print_success(f"State lookup working - Pincode: {data.get('pincode')}, State: {data.get('state')}")
                results.add_pass()
                return {"success": True, "status": response.status_code, "data": data}
            else:
                error_msg = f"Pincode State Lookup - Expected Kerala state, got: {data.get('state')}"
                print_error(error_msg)
                results.add_fail(error_msg)
                return {"success": False, "status": response.status_code, "data": data}
        else:
            error_msg = f"Pincode State Lookup - Unexpected status {response.status_code}"
            print_error(error_msg)
            results.add_fail(error_msg)
            return {"success": False, "status": response.status_code, "data": None}
            
    except Exception as e:
        error_msg = f"Pincode State Lookup - Exception: {str(e)}"
        print_error(error_msg)
        results.add_fail(error_msg)
        return {"success": False, "status": None, "data": None}

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("CELESTA GLOW BACKEND API TEST SUITE")
    print("Third-Party Integration Keys Validation + Core Catalog")
    print(f"Base URL: {BASE_URL}")
    print(f"{'='*60}{Colors.END}\n")
    
    # NEW TESTS: Third-Party Integration Keys
    print(f"\n{Colors.BLUE}{'='*60}")
    print("THIRD-PARTY INTEGRATION TESTS")
    print(f"{'='*60}{Colors.END}")
    
    # Test: POST /api/create-razorpay-order
    test_razorpay_order_creation()
    
    # Test: GET /api/pincode/682001
    test_pincode_lookup()
    
    # Test: GET /api/pincode/682001/state
    test_pincode_state_only()
    
    # EXISTING TESTS: Core Catalog Health Check
    print(f"\n{Colors.BLUE}{'='*60}")
    print("CORE CATALOG HEALTH CHECK")
    print(f"{'='*60}{Colors.END}")
    
    # Test 1: GET /api/products?niche=skin-care&page=1&limit=20
    test_endpoint(
        "1. Products List (niche=skin-care)",
        f"{BASE_URL}/products?niche=skin-care&page=1&limit=20",
        validate_fn=validate_products_list
    )
    
    # Test 2: GET /api/site-settings
    test_endpoint(
        "2. Site Settings",
        f"{BASE_URL}/site-settings",
        validate_fn=validate_site_settings
    )
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
