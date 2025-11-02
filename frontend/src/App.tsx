import { useState, useEffect } from 'react'
import './App.css'

interface Transaction {
  date: string;
  amount: string;
  description: string;
  paymentType: string;
}

function App() {
  const [categories, setCategories] = useState<string[]>([]);
  const [transaction, setTransaction] = useState<Transaction>({
    date: '',
    amount: '',
    description: '',
    paymentType: ''
  });
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    fetch('http://localhost:8080/api/categories')
      .then(response => response.json())
      .then(data => setCategories(data))
      .catch(error => console.error('Error fetching categories:', error));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setTransaction(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetch('http://localhost:8080/api/transactions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ...transaction,
        amount: parseFloat(transaction.amount)
      })
    })
      .then(response => response.json())
      .then(() => {
        setMessage('Transaction saved successfully!');
        setTransaction({ date: '', amount: '', description: '', paymentType: '' });
      })
      .catch(error => {
        console.error('Error saving transaction:', error);
        setMessage('Error saving transaction.');
      });
  };

  return (
    <div className="App">
      <h1>Transaction Input</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Date:</label>
          <input
            type="date"
            name="date"
            value={transaction.date}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label>Amount:</label>
          <input
            type="number"
            step="0.01"
            name="amount"
            value={transaction.amount}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label>Description:</label>
          <input
            type="text"
            name="description"
            value={transaction.description}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label>Payment Type:</label>
          <select
            name="paymentType"
            value={transaction.paymentType}
            onChange={handleChange}
            required
          >
            <option value="">Select a category</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
        <button type="submit">Submit</button>
      </form>
      {message && (
        <div className={`message ${message.includes('successfully') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
    </div>
  )
}

export default App
