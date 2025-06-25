import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { format, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import './App.css';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Category colors for consistent theming
const CATEGORY_COLORS = {
  'Alimentação': '#ef4444',
  'Transporte': '#f97316', 
  'Lazer': '#eab308',
  'Saúde': '#22c55e',
  'Educação': '#3b82f6',
  'Casa': '#8b5cf6',
  'Roupas': '#ec4899',
  'Tecnologia': '#06b6d4',
  'Outros': '#64748b'
};

function App() {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [categorySummaries, setCategorySummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Form states
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    category: '',
    date: new Date().toISOString().split('T')[0]
  });

  // Format currency in Brazilian Real
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(amount);
  };

  // Fetch data functions
  const fetchExpenses = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/expenses?limit=10`);
      setExpenses(response.data);
    } catch (err) {
      setError('Erro ao carregar despesas');
      console.error('Error fetching expenses:', err);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/categories`);
      setCategories(response.data);
    } catch (err) {
      setError('Erro ao carregar categorias');
      console.error('Error fetching categories:', err);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/stats`);
      setDashboardStats(response.data);
    } catch (err) {
      setError('Erro ao carregar estatísticas');
      console.error('Error fetching dashboard stats:', err);
    }
  };

  const fetchCategorySummaries = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/categories`);
      setCategorySummaries(response.data);
    } catch (err) {
      setError('Erro ao carregar resumo por categoria');
      console.error('Error fetching category summaries:', err);
    }
  };

  const loadAllData = async () => {
    setLoading(true);
    await Promise.all([
      fetchExpenses(),
      fetchCategories(), 
      fetchDashboardStats(),
      fetchCategorySummaries()
    ]);
    setLoading(false);
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Form handlers
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.description || !formData.amount || !formData.category) {
      setError('Todos os campos são obrigatórios');
      return;
    }

    try {
      const expenseData = {
        ...formData,
        amount: parseFloat(formData.amount)
      };

      if (editingExpense) {
        await axios.put(`${API_URL}/api/expenses/${editingExpense.id}`, expenseData);
      } else {
        await axios.post(`${API_URL}/api/expenses`, expenseData);
      }

      // Reset form and reload data
      setFormData({
        description: '',
        amount: '',
        category: '',
        date: new Date().toISOString().split('T')[0]
      });
      setShowForm(false);
      setEditingExpense(null);
      setError('');
      await loadAllData();
    } catch (err) {
      setError(editingExpense ? 'Erro ao atualizar despesa' : 'Erro ao criar despesa');
      console.error('Error saving expense:', err);
    }
  };

  const handleEdit = (expense) => {
    setEditingExpense(expense);
    setFormData({
      description: expense.description,
      amount: expense.amount.toString(),
      category: expense.category,
      date: expense.date
    });
    setShowForm(true);
  };

  const handleDelete = async (expenseId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta despesa?')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/expenses/${expenseId}`);
      await loadAllData();
    } catch (err) {
      setError('Erro ao excluir despesa');
      console.error('Error deleting expense:', err);
    }
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditingExpense(null);
    setFormData({
      description: '',
      amount: '',
      category: '',
      date: new Date().toISOString().split('T')[0]
    });
    setError('');
  };

  // Chart data preparation
  const doughnutData = {
    labels: categorySummaries.map(cat => cat.category),
    datasets: [{
      data: categorySummaries.map(cat => cat.total),
      backgroundColor: categorySummaries.map(cat => CATEGORY_COLORS[cat.category] || '#64748b'),
      borderWidth: 0,
      hoverOffset: 8
    }]
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#e2e8f0',
          padding: 20,
          usePointStyle: true,
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#e2e8f0',
        bodyColor: '#e2e8f0',
        borderColor: '#334155',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            const value = formatCurrency(context.raw);
            const percentage = context.dataset.data.reduce((a, b) => a + b, 0);
            const percent = ((context.raw / percentage) * 100).toFixed(1);
            return `${context.label}: ${value} (${percent}%)`;
          }
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-300 text-lg">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-gray-900 to-black border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <img 
                src="https://images.unsplash.com/photo-1655807286510-a49644c29ef9" 
                alt="Gestão Financeira Logo" 
                className="h-12 w-12 rounded-xl shadow-xl logo-hover"
              />
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Saldoo
                </h1>
                <p className="text-sm text-gray-400">Controle suas despesas com inteligência</p>
              </div>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              + Nova Despesa
            </button>
          </div>
        </div>
      </header>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
            {error}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Stats */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Total Gasto</p>
                  <p className="text-2xl font-bold text-red-400">{formatCurrency(dashboardStats.total_expenses)}</p>
                </div>
                <div className="bg-red-500/10 p-3 rounded-lg">
                  <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Despesas</p>
                  <p className="text-2xl font-bold text-blue-400">{dashboardStats.total_count}</p>
                </div>
                <div className="bg-blue-500/10 p-3 rounded-lg">
                  <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Média</p>
                  <p className="text-2xl font-bold text-green-400">{formatCurrency(dashboardStats.average_expense)}</p>
                </div>
                <div className="bg-green-500/10 p-3 rounded-lg">
                  <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Este Mês</p>
                  <p className="text-2xl font-bold text-purple-400">{formatCurrency(dashboardStats.monthly_total)}</p>
                </div>
                <div className="bg-purple-500/10 p-3 rounded-lg">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Charts and Recent Expenses */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Category Chart */}
          <div className="lg:col-span-2 bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
            <h3 className="text-xl font-bold mb-6 text-gray-100">Gastos por Categoria - Este Mês</h3>
            {categorySummaries.length > 0 ? (
              <div className="h-80">
                <Doughnut data={doughnutData} options={doughnutOptions} />
              </div>
            ) : (
              <div className="h-80 flex items-center justify-center">
                <p className="text-gray-400 text-lg">Nenhuma despesa encontrada para este mês</p>
              </div>
            )}
          </div>

          {/* Category Summary */}
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
            <h3 className="text-xl font-bold mb-6 text-gray-100">Resumo por Categoria</h3>
            <div className="space-y-4 max-h-80 overflow-y-auto">
              {categorySummaries.map((cat, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full" 
                      style={{backgroundColor: CATEGORY_COLORS[cat.category] || '#64748b'}}
                    ></div>
                    <div>
                      <p className="font-medium text-gray-200">{cat.category}</p>
                      <p className="text-sm text-gray-400">{cat.count} despesa{cat.count !== 1 ? 's' : ''}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-100">{formatCurrency(cat.total)}</p>
                    <p className="text-sm text-gray-400">{cat.percentage.toFixed(1)}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Expenses */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl">
          <h3 className="text-xl font-bold mb-6 text-gray-100">Despesas Recentes</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Descrição</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Categoria</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Valor</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Data</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense, index) => (
                  <tr key={expense.id} className="border-b border-gray-800 hover:bg-gray-800/30 transition-colors">
                    <td className="py-4 px-4">
                      <p className="font-medium text-gray-100">{expense.description}</p>
                    </td>
                    <td className="py-4 px-4">
                      <span 
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-white"
                        style={{backgroundColor: CATEGORY_COLORS[expense.category] || '#64748b'}}
                      >
                        {expense.category}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <p className="font-bold text-red-400">{formatCurrency(expense.amount)}</p>
                    </td>
                    <td className="py-4 px-4">
                      <p className="text-gray-300">
                        {format(parseISO(expense.date), 'dd/MM/yyyy', { locale: ptBR })}
                      </p>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEdit(expense)}
                          className="text-blue-400 hover:text-blue-300 transition-colors p-1"
                          title="Editar"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(expense.id)}
                          className="text-red-400 hover:text-red-300 transition-colors p-1"
                          title="Excluir"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {expenses.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-400 text-lg">Nenhuma despesa encontrada</p>
                <p className="text-gray-500 text-sm mt-2">Clique em "Nova Despesa" para começar</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gradient-to-r from-gray-900 to-black border-t border-gray-800 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <img 
                src="https://images.unsplash.com/photo-1655807286510-a49644c29ef9" 
                alt="Logo" 
                className="h-8 w-8 rounded-lg shadow-lg"
              />
              <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                Gestão Financeira
              </h3>
            </div>
            
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-xl inline-block">
              <h4 className="text-lg font-semibold text-gray-200 mb-3">Desenvolvido por</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-gray-300">
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg mb-2 footer-avatar">
                    G
                  </div>
                  <span className="text-sm font-medium">Gustavo</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-red-600 rounded-full flex items-center justify-center text-white font-bold text-lg mb-2 footer-avatar">
                    C
                  </div>
                  <span className="text-sm font-medium">Carla</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-600 rounded-full flex items-center justify-center text-white font-bold text-lg mb-2 footer-avatar">
                    JV
                  </div>
                  <span className="text-sm font-medium">João Vitor</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-lg mb-2 footer-avatar">
                    P
                  </div>
                  <span className="text-sm font-medium">Priscila</span>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-700 university-badge rounded-lg p-3">
                <p className="text-sm text-gray-300 font-medium">
                  Alunos do 1° período de Química
                </p>
                <p className="text-sm text-blue-400 font-bold">
                  UTFPR - Universidade Tecnológica Federal do Paraná
                </p>
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-gray-500 text-sm">
                © 2025 Gestão Financeira. Projeto acadêmico desenvolvido com 💙
              </p>
            </div>
          </div>
        </div>
      </footer>

      {/* Expense Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 border border-gray-700 shadow-2xl w-full max-w-md">
            <h3 className="text-2xl font-bold mb-6 text-gray-100">
              {editingExpense ? 'Editar Despesa' : 'Nova Despesa'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">
                  Descrição
                </label>
                <input
                  type="text"
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                  placeholder="Ex: Almoço no restaurante"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="amount" className="block text-sm font-medium text-gray-300 mb-2">
                  Valor (R$)
                </label>
                <input
                  type="number"
                  id="amount"
                  name="amount"
                  value={formData.amount}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                  placeholder="0,00"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="category" className="block text-sm font-medium text-gray-300 mb-2">
                  Categoria
                </label>
                <select
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                  required
                >
                  <option value="">Selecione uma categoria</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label htmlFor="date" className="block text-sm font-medium text-gray-300 mb-2">
                  Data
                </label>
                <input
                  type="date"
                  id="date"
                  name="date"
                  value={formData.date}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                  required
                />
              </div>
              
              <div className="flex space-x-4">
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-medium py-3 px-6 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  {editingExpense ? 'Atualizar' : 'Criar'} Despesa
                </button>
                <button
                  type="button"
                  onClick={cancelForm}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;