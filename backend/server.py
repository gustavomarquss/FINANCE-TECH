from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import os
import uuid
from collections import defaultdict

# Initialize FastAPI app
app = FastAPI(title="Gestão Financeira API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'finance_app')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
expenses_collection = db.expenses

# Pydantic models
class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    date: str = Field(...)  # Format: YYYY-MM-DD

class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1)
    date: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: str
    description: str
    amount: float
    category: str
    date: str
    created_at: str

class DashboardStats(BaseModel):
    total_expenses: float
    total_count: int
    average_expense: float
    categories_used: int
    monthly_total: float

class CategorySummary(BaseModel):
    category: str
    total: float
    count: int
    percentage: float

# Predefined categories
CATEGORIES = [
    "Alimentação",
    "Transporte", 
    "Lazer",
    "Saúde",
    "Educação",
    "Casa",
    "Roupas",
    "Tecnologia",
    "Outros"
]

# Helper functions
def format_expense_response(expense_doc) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense_doc["id"],
        description=expense_doc["description"],
        amount=expense_doc["amount"],
        category=expense_doc["category"],
        date=expense_doc["date"],
        created_at=expense_doc["created_at"]
    )

def get_current_month_filter():
    now = datetime.now()
    start_of_month = f"{now.year}-{now.month:02d}-01"
    if now.month == 12:
        end_of_month = f"{now.year + 1}-01-01"
    else:
        end_of_month = f"{now.year}-{now.month + 1:02d}-01"
    return {"date": {"$gte": start_of_month, "$lt": end_of_month}}

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Gestão Financeira API - Sistema de controle de despesas"}

@app.get("/api/categories", response_model=List[str])
async def get_categories():
    """Get all available expense categories"""
    return CATEGORIES

@app.post("/api/expenses", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate):
    """Create a new expense"""
    try:
        # Validate category
        if expense.category not in CATEGORIES:
            raise HTTPException(status_code=400, detail="Categoria inválida")
        
        # Validate date format
        try:
            datetime.strptime(expense.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
        
        expense_doc = {
            "id": str(uuid.uuid4()),
            "description": expense.description,
            "amount": expense.amount,
            "category": expense.category,
            "date": expense.date,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = expenses_collection.insert_one(expense_doc)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Erro ao criar despesa")
        
        return format_expense_response(expense_doc)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/expenses", response_model=List[ExpenseResponse])
async def get_expenses(limit: int = 50, offset: int = 0):
    """Get all expenses with pagination"""
    try:
        cursor = expenses_collection.find().sort("created_at", -1).skip(offset).limit(limit)
        expenses = []
        for expense_doc in cursor:
            expenses.append(format_expense_response(expense_doc))
        return expenses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar despesas: {str(e)}")

@app.get("/api/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str):
    """Get a specific expense by ID"""
    try:
        expense_doc = expenses_collection.find_one({"id": expense_id})
        if not expense_doc:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")
        return format_expense_response(expense_doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar despesa: {str(e)}")

@app.put("/api/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: str, expense_update: ExpenseUpdate):
    """Update an existing expense"""
    try:
        # Check if expense exists
        existing = expenses_collection.find_one({"id": expense_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")
        
        # Prepare update data
        update_data = {}
        if expense_update.description is not None:
            update_data["description"] = expense_update.description
        if expense_update.amount is not None:
            update_data["amount"] = expense_update.amount
        if expense_update.category is not None:
            if expense_update.category not in CATEGORIES:
                raise HTTPException(status_code=400, detail="Categoria inválida")
            update_data["category"] = expense_update.category
        if expense_update.date is not None:
            try:
                datetime.strptime(expense_update.date, "%Y-%m-%d")
                update_data["date"] = expense_update.date
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")
        
        # Update the expense
        result = expenses_collection.update_one(
            {"id": expense_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Erro ao atualizar despesa")
        
        # Return updated expense
        updated_expense = expenses_collection.find_one({"id": expense_id})
        return format_expense_response(updated_expense)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    """Delete an expense"""
    try:
        result = expenses_collection.delete_one({"id": expense_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Despesa não encontrada")
        return {"message": "Despesa excluída com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir despesa: {str(e)}")

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get all expenses
        all_expenses = list(expenses_collection.find())
        
        if not all_expenses:
            return DashboardStats(
                total_expenses=0.0,
                total_count=0,
                average_expense=0.0,
                categories_used=0,
                monthly_total=0.0
            )
        
        # Calculate totals
        total_expenses = sum(exp["amount"] for exp in all_expenses)
        total_count = len(all_expenses)
        average_expense = total_expenses / total_count if total_count > 0 else 0.0
        
        # Get unique categories
        categories_used = len(set(exp["category"] for exp in all_expenses))
        
        # Calculate monthly total (current month)
        current_month_filter = get_current_month_filter()
        monthly_expenses = list(expenses_collection.find(current_month_filter))
        monthly_total = sum(exp["amount"] for exp in monthly_expenses)
        
        return DashboardStats(
            total_expenses=total_expenses,
            total_count=total_count,
            average_expense=average_expense,
            categories_used=categories_used,
            monthly_total=monthly_total
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")

@app.get("/api/dashboard/categories", response_model=List[CategorySummary])
async def get_category_summaries():
    """Get expense summaries by category for current month"""
    try:
        current_month_filter = get_current_month_filter()
        monthly_expenses = list(expenses_collection.find(current_month_filter))
        
        if not monthly_expenses:
            return []
        
        # Group by category
        category_totals = defaultdict(lambda: {"total": 0.0, "count": 0})
        total_amount = 0.0
        
        for expense in monthly_expenses:
            category = expense["category"]
            amount = expense["amount"]
            category_totals[category]["total"] += amount
            category_totals[category]["count"] += 1
            total_amount += amount
        
        # Create summaries
        summaries = []
        for category, data in category_totals.items():
            percentage = (data["total"] / total_amount * 100) if total_amount > 0 else 0
            summaries.append(CategorySummary(
                category=category,
                total=data["total"],
                count=data["count"],
                percentage=percentage
            ))
        
        # Sort by total descending
        summaries.sort(key=lambda x: x.total, reverse=True)
        return summaries
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular resumo por categoria: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)