import requests

def test_salary_logic():
    session = requests.Session()
    
    # 1. Login
    login_data = {"email": "demo@finguard.com", "password": "demo123"}
    session.post("http://localhost:5000/api/auth/login", json=login_data)
    
    # 2. Get salary initial (should be 0)
    res = session.get("http://localhost:5000/api/user/salary")
    print(f"Initial salary: {res.json()}")
    
    # 3. Add transaction when salary is 0 (should work, but analysis fails or returns error inside JSON if I didn't change add_transaction)
    txn_data = {"date": "2023-10-10", "amount": 100, "category": "Food"}
    add_res = session.post("http://localhost:5000/api/add_transaction", json=txn_data)
    print(f"Add txn (salary=0) response: {add_res.json()}")
    
    # 4. Get analysis (should fail with Configuration required)
    anal_res = session.get("http://localhost:5000/api/analysis")
    print(f"Analysis (salary=0) response: {anal_res.json()}")
    
    # 5. Set salary
    sal_res = session.post("http://localhost:5000/api/user/salary", json={"salary": 60000})
    print(f"Set salary response: {sal_res.json()}")
    
    # 6. Get analysis again (should succeed)
    anal_res2 = session.get("http://localhost:5000/api/analysis")
    print(f"Analysis (salary=60000) keys: {anal_res2.json().keys()}")
    
if __name__ == '__main__':
    test_salary_logic()
