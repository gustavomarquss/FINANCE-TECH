#!/usr/bin/env python3
import requests
import json
import datetime
import time
import os
import sys
from typing import Dict, List, Any, Optional

# Get the backend URL from the frontend .env file
def get_backend_url():
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.strip().split('=')[1].strip('"\'')
    raise Exception("Could not find REACT_APP_BACKEND_URL in frontend/.env")

# Base URL for API requests
BASE_URL = f"{get_backend_url()}/api"
print(f"Using backend URL: {BASE_URL}")

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "test_details": []
}

# Helper function to run a test and track results
def run_test(test_name: str, test_func, *args, **kwargs):
    test_results["total_tests"] += 1
    print(f"\n{'='*80}\nRunning test: {test_name}\n{'='*80}")
    
    try:
        result = test_func(*args, **kwargs)
        test_results["passed_tests"] += 1
        test_results["test_details"].append({
            "name": test_name,
            "status": "PASSED",
            "details": result
        })
        print(f"✅ Test PASSED: {test_name}")
        return result
    except Exception as e:
        test_results["failed_tests"] += 1
        test_results["test_details"].append({
            "name": test_name,
            "status": "FAILED",
            "details": str(e)
        })
        print(f"❌ Test FAILED: {test_name}")
        print(f"Error: {str(e)}")
        return None

# Helper function to make API requests
def make_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return JSON response if available, otherwise return response object
        try:
            return response.json()
        except:
            return response
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Response error: {error_detail}")
                raise Exception(f"API Error: {error_detail}")
            except:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
                raise Exception(f"API Error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Request failed: {str(e)}")

# Test functions for each API endpoint

def test_get_categories():
    """Test the GET /api/categories endpoint"""
    response = make_request("GET", "/categories")
    
    # Verify the response contains the expected categories
    expected_categories = [
        "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", 
        "Casa", "Roupas", "Tecnologia", "Outros"
    ]
    
    if not isinstance(response, list):
        raise Exception(f"Expected a list of categories, got {type(response)}")
    
    if len(response) != len(expected_categories):
        raise Exception(f"Expected {len(expected_categories)} categories, got {len(response)}")
    
    for category in expected_categories:
        if category not in response:
            raise Exception(f"Expected category '{category}' not found in response")
    
    return {"categories": response}

def test_create_expense():
    """Test the POST /api/expenses endpoint"""
    # Create a valid expense
    expense_data = {
        "description": "Teste de Despesa",
        "amount": 150.75,
        "category": "Alimentação",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    response = make_request("POST", "/expenses", data=expense_data)
    
    # Verify the response contains the expected fields
    required_fields = ["id", "description", "amount", "category", "date", "created_at"]
    for field in required_fields:
        if field not in response:
            raise Exception(f"Required field '{field}' not found in response")
    
    # Verify the data matches what we sent
    if response["description"] != expense_data["description"]:
        raise Exception(f"Description mismatch: expected '{expense_data['description']}', got '{response['description']}'")
    
    if response["amount"] != expense_data["amount"]:
        raise Exception(f"Amount mismatch: expected {expense_data['amount']}, got {response['amount']}")
    
    if response["category"] != expense_data["category"]:
        raise Exception(f"Category mismatch: expected '{expense_data['category']}', got '{response['category']}'")
    
    if response["date"] != expense_data["date"]:
        raise Exception(f"Date mismatch: expected '{expense_data['date']}', got '{response['date']}'")
    
    return {"created_expense": response}

def test_create_expense_validations():
    """Test validations for the POST /api/expenses endpoint"""
    # Test invalid category
    invalid_category_data = {
        "description": "Despesa com Categoria Inválida",
        "amount": 100.0,
        "category": "Categoria Inválida",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        make_request("POST", "/expenses", data=invalid_category_data)
        raise Exception("Expected validation error for invalid category, but request succeeded")
    except Exception as e:
        if "Categoria inválida" not in str(e):
            raise Exception(f"Expected 'Categoria inválida' error, got: {str(e)}")
    
    # Test negative amount
    negative_amount_data = {
        "description": "Despesa com Valor Negativo",
        "amount": -50.0,
        "category": "Alimentação",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        make_request("POST", "/expenses", data=negative_amount_data)
        raise Exception("Expected validation error for negative amount, but request succeeded")
    except Exception as e:
        if "amount" not in str(e).lower() and "valor" not in str(e).lower():
            raise Exception(f"Expected error related to amount/valor, got: {str(e)}")
    
    # Test invalid date format
    invalid_date_data = {
        "description": "Despesa com Data Inválida",
        "amount": 75.0,
        "category": "Alimentação",
        "date": "01/01/2023"  # Wrong format, should be YYYY-MM-DD
    }
    
    try:
        make_request("POST", "/expenses", data=invalid_date_data)
        raise Exception("Expected validation error for invalid date format, but request succeeded")
    except Exception as e:
        if "data" not in str(e).lower() and "date" not in str(e).lower():
            raise Exception(f"Expected error related to date/data, got: {str(e)}")
    
    # Test empty description
    empty_description_data = {
        "description": "",
        "amount": 100.0,
        "category": "Alimentação",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        make_request("POST", "/expenses", data=empty_description_data)
        raise Exception("Expected validation error for empty description, but request succeeded")
    except Exception as e:
        if "description" not in str(e).lower() and "descrição" not in str(e).lower():
            raise Exception(f"Expected error related to description/descrição, got: {str(e)}")
    
    return {"validation_tests": "All validation tests passed"}

def test_get_expenses():
    """Test the GET /api/expenses endpoint with pagination"""
    # Create multiple expenses for testing pagination
    expenses = []
    categories = ["Alimentação", "Transporte", "Lazer"]
    
    for i in range(3):
        expense_data = {
            "description": f"Despesa de Teste {i+1}",
            "amount": 100.0 + (i * 50),
            "category": categories[i % len(categories)],
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        
        response = make_request("POST", "/expenses", data=expense_data)
        expenses.append(response)
    
    # Test default pagination (limit=50, offset=0)
    response = make_request("GET", "/expenses")
    
    if not isinstance(response, list):
        raise Exception(f"Expected a list of expenses, got {type(response)}")
    
    # Verify that our created expenses are in the response
    expense_ids = [expense["id"] for expense in expenses]
    response_ids = [expense["id"] for expense in response]
    
    for expense_id in expense_ids:
        if expense_id not in response_ids:
            raise Exception(f"Created expense with ID {expense_id} not found in response")
    
    # Test pagination with limit
    limit = 2
    response_limited = make_request("GET", "/expenses", params={"limit": limit})
    
    if not isinstance(response_limited, list):
        raise Exception(f"Expected a list of expenses, got {type(response_limited)}")
    
    if len(response_limited) > limit:
        raise Exception(f"Expected at most {limit} expenses, got {len(response_limited)}")
    
    # Test pagination with offset
    offset = 1
    response_offset = make_request("GET", "/expenses", params={"offset": offset, "limit": limit})
    
    if not isinstance(response_offset, list):
        raise Exception(f"Expected a list of expenses, got {type(response_offset)}")
    
    if len(response_offset) > limit:
        raise Exception(f"Expected at most {limit} expenses, got {len(response_offset)}")
    
    # The first item in the offset response should be the second item in the original response
    if len(response) > offset and len(response_offset) > 0:
        if response[offset]["id"] != response_offset[0]["id"]:
            raise Exception(f"Offset pagination not working correctly")
    
    return {
        "created_expenses": expenses,
        "pagination_tests": "All pagination tests passed"
    }

def test_get_expense_by_id():
    """Test the GET /api/expenses/{id} endpoint"""
    # Create an expense first
    expense_data = {
        "description": "Despesa para Busca por ID",
        "amount": 200.0,
        "category": "Saúde",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    created_expense = make_request("POST", "/expenses", data=expense_data)
    expense_id = created_expense["id"]
    
    # Get the expense by ID
    response = make_request("GET", f"/expenses/{expense_id}")
    
    # Verify the response contains the expected fields
    required_fields = ["id", "description", "amount", "category", "date", "created_at"]
    for field in required_fields:
        if field not in response:
            raise Exception(f"Required field '{field}' not found in response")
    
    # Verify the data matches what we created
    if response["id"] != expense_id:
        raise Exception(f"ID mismatch: expected '{expense_id}', got '{response['id']}'")
    
    if response["description"] != expense_data["description"]:
        raise Exception(f"Description mismatch: expected '{expense_data['description']}', got '{response['description']}'")
    
    if response["amount"] != expense_data["amount"]:
        raise Exception(f"Amount mismatch: expected {expense_data['amount']}, got {response['amount']}")
    
    if response["category"] != expense_data["category"]:
        raise Exception(f"Category mismatch: expected '{expense_data['category']}', got '{response['category']}'")
    
    if response["date"] != expense_data["date"]:
        raise Exception(f"Date mismatch: expected '{expense_data['date']}', got '{response['date']}'")
    
    # Test with non-existent ID
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    try:
        make_request("GET", f"/expenses/{non_existent_id}")
        raise Exception(f"Expected 404 error for non-existent ID, but request succeeded")
    except Exception as e:
        if "não encontrada" not in str(e).lower() and "not found" not in str(e).lower():
            raise Exception(f"Expected 'not found' error, got: {str(e)}")
    
    return {"expense_by_id": response}

def test_update_expense():
    """Test the PUT /api/expenses/{id} endpoint"""
    # Create an expense first
    expense_data = {
        "description": "Despesa para Atualização",
        "amount": 300.0,
        "category": "Educação",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    created_expense = make_request("POST", "/expenses", data=expense_data)
    expense_id = created_expense["id"]
    
    # Update the expense
    update_data = {
        "description": "Despesa Atualizada",
        "amount": 350.0,
        "category": "Tecnologia"
    }
    
    response = make_request("PUT", f"/expenses/{expense_id}", data=update_data)
    
    # Verify the response contains the expected fields
    required_fields = ["id", "description", "amount", "category", "date", "created_at"]
    for field in required_fields:
        if field not in response:
            raise Exception(f"Required field '{field}' not found in response")
    
    # Verify the data was updated correctly
    if response["id"] != expense_id:
        raise Exception(f"ID mismatch: expected '{expense_id}', got '{response['id']}'")
    
    if response["description"] != update_data["description"]:
        raise Exception(f"Description not updated: expected '{update_data['description']}', got '{response['description']}'")
    
    if response["amount"] != update_data["amount"]:
        raise Exception(f"Amount not updated: expected {update_data['amount']}, got {response['amount']}")
    
    if response["category"] != update_data["category"]:
        raise Exception(f"Category not updated: expected '{update_data['category']}', got '{response['category']}'")
    
    # Test update with invalid category
    invalid_update = {
        "category": "Categoria Inválida"
    }
    
    try:
        make_request("PUT", f"/expenses/{expense_id}", data=invalid_update)
        raise Exception("Expected validation error for invalid category, but request succeeded")
    except Exception as e:
        if "categoria inválida" not in str(e).lower():
            raise Exception(f"Expected 'Categoria inválida' error, got: {str(e)}")
    
    # Test update with negative amount
    negative_update = {
        "amount": -50.0
    }
    
    try:
        make_request("PUT", f"/expenses/{expense_id}", data=negative_update)
        raise Exception("Expected validation error for negative amount, but request succeeded")
    except Exception as e:
        if "amount" not in str(e).lower() and "valor" not in str(e).lower():
            raise Exception(f"Expected error related to amount/valor, got: {str(e)}")
    
    # Test update with invalid date format
    invalid_date_update = {
        "date": "01/01/2023"  # Wrong format, should be YYYY-MM-DD
    }
    
    try:
        make_request("PUT", f"/expenses/{expense_id}", data=invalid_date_update)
        raise Exception("Expected validation error for invalid date format, but request succeeded")
    except Exception as e:
        if "data" not in str(e).lower() and "date" not in str(e).lower():
            raise Exception(f"Expected error related to date/data, got: {str(e)}")
    
    # Test update with non-existent ID
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    try:
        make_request("PUT", f"/expenses/{non_existent_id}", data=update_data)
        raise Exception(f"Expected 404 error for non-existent ID, but request succeeded")
    except Exception as e:
        if "não encontrada" not in str(e).lower() and "not found" not in str(e).lower():
            raise Exception(f"Expected 'not found' error, got: {str(e)}")
    
    return {"updated_expense": response}

def test_delete_expense():
    """Test the DELETE /api/expenses/{id} endpoint"""
    # Create an expense first
    expense_data = {
        "description": "Despesa para Exclusão",
        "amount": 250.0,
        "category": "Roupas",
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    created_expense = make_request("POST", "/expenses", data=expense_data)
    expense_id = created_expense["id"]
    
    # Delete the expense
    response = make_request("DELETE", f"/expenses/{expense_id}")
    
    # Verify the response contains a success message
    if "message" not in response:
        raise Exception(f"Expected 'message' field in response, got: {response}")
    
    if "sucesso" not in response["message"].lower():
        raise Exception(f"Expected success message, got: {response['message']}")
    
    # Verify the expense was actually deleted
    try:
        make_request("GET", f"/expenses/{expense_id}")
        raise Exception(f"Expected 404 error after deletion, but request succeeded")
    except Exception as e:
        if "não encontrada" not in str(e).lower() and "not found" not in str(e).lower():
            raise Exception(f"Expected 'not found' error, got: {str(e)}")
    
    # Test delete with non-existent ID
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    try:
        make_request("DELETE", f"/expenses/{non_existent_id}")
        raise Exception(f"Expected 404 error for non-existent ID, but request succeeded")
    except Exception as e:
        if "não encontrada" not in str(e).lower() and "not found" not in str(e).lower():
            raise Exception(f"Expected 'not found' error, got: {str(e)}")
    
    return {"delete_result": "Expense successfully deleted"}

def test_dashboard_stats():
    """Test the GET /api/dashboard/stats endpoint"""
    # Create multiple expenses with different categories
    expenses = []
    test_data = [
        {"description": "Despesa de Alimentação", "amount": 150.0, "category": "Alimentação"},
        {"description": "Despesa de Transporte", "amount": 100.0, "category": "Transporte"},
        {"description": "Despesa de Lazer", "amount": 200.0, "category": "Lazer"},
        {"description": "Outra Despesa de Alimentação", "amount": 120.0, "category": "Alimentação"}
    ]
    
    for data in test_data:
        data["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        response = make_request("POST", "/expenses", data=data)
        expenses.append(response)
    
    # Get dashboard stats
    response = make_request("GET", "/dashboard/stats")
    
    # Verify the response contains the expected fields
    required_fields = ["total_expenses", "total_count", "average_expense", "categories_used", "monthly_total"]
    for field in required_fields:
        if field not in response:
            raise Exception(f"Required field '{field}' not found in response")
    
    # Verify the stats are calculated correctly
    # Note: This assumes there are no other expenses in the database from previous tests
    # In a real-world scenario, we would need to account for existing data
    
    # Calculate expected values based on the expenses we just created
    expected_total = sum(expense["amount"] for expense in expenses)
    expected_count = len(expenses)
    expected_average = expected_total / expected_count if expected_count > 0 else 0
    expected_categories = len(set(expense["category"] for expense in expenses))
    
    # The monthly total should be at least the sum of our test expenses
    # (it might be higher if there are other expenses from the current month)
    if response["total_count"] < expected_count:
        raise Exception(f"Expected at least {expected_count} expenses, got {response['total_count']}")
    
    if response["categories_used"] < expected_categories:
        raise Exception(f"Expected at least {expected_categories} categories, got {response['categories_used']}")
    
    if response["monthly_total"] < expected_total:
        raise Exception(f"Expected monthly total to be at least {expected_total}, got {response['monthly_total']}")
    
    return {"dashboard_stats": response}

def test_category_summaries():
    """Test the GET /api/dashboard/categories endpoint"""
    # Get category summaries
    response = make_request("GET", "/dashboard/categories")
    
    if not isinstance(response, list):
        raise Exception(f"Expected a list of category summaries, got {type(response)}")
    
    # Verify each summary has the expected fields
    for summary in response:
        required_fields = ["category", "total", "count", "percentage"]
        for field in required_fields:
            if field not in summary:
                raise Exception(f"Required field '{field}' not found in category summary")
    
    # Verify the percentages sum to approximately 100%
    total_percentage = sum(summary["percentage"] for summary in response)
    if response and abs(total_percentage - 100.0) > 0.1:  # Allow for small floating-point errors
        raise Exception(f"Expected percentages to sum to 100%, got {total_percentage}%")
    
    return {"category_summaries": response}

def run_all_tests():
    """Run all API tests"""
    # Test categories API
    run_test("Get Categories", test_get_categories)
    
    # Test expenses CRUD
    created_expense = run_test("Create Expense", test_create_expense)
    run_test("Create Expense Validations", test_create_expense_validations)
    run_test("Get Expenses with Pagination", test_get_expenses)
    
    if created_expense:
        expense_id = created_expense.get("created_expense", {}).get("id")
        if expense_id:
            run_test("Get Expense by ID", test_get_expense_by_id)
    
    run_test("Update Expense", test_update_expense)
    run_test("Delete Expense", test_delete_expense)
    
    # Test dashboard APIs
    run_test("Dashboard Stats", test_dashboard_stats)
    run_test("Category Summaries", test_category_summaries)
    
    # Print summary
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {test_results['passed_tests']}/{test_results['total_tests']} tests passed")
    print(f"Passed: {test_results['passed_tests']}")
    print(f"Failed: {test_results['failed_tests']}")
    print("="*80)
    
    return test_results

if __name__ == "__main__":
    run_all_tests()