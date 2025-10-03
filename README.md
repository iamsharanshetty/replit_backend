# 🚀 Coding Challenge Platform

A modern, interactive coding challenge platform built with FastAPI and vanilla JavaScript. Users can solve Python coding problems, get instant feedback, and compete on a live leaderboard.

## ✨ Features

- **🎯 Interactive Problem Selection**: Choose from multiple coding challenges via dropdown
- **💻 Python Code Editor**: Clean, syntax-highlighted code editor
- **⚡ Real-time Grading**: Instant feedback with detailed test results
- **🏆 Live Leaderboard**: Track progress and compete with other users
- **🌙 Dark/Light Mode**: Beautiful themes with smooth transitions
- **📱 Responsive Design**: Works great on desktop and mobile
- **🎉 Animated UI**: Engaging animations and confetti for achievements

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS with animations and gradients
- **Code Execution**: Secure subprocess execution with timeout protection
- **Data Storage**: JSON file-based storage

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn
```

### 2. Start the Backend Server

```bash
uvicorn server:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### 3. Open the Frontend

Open `frontend/challenge.html` in your web browser, or serve it using a local server:

```bash
# Using Python's built-in server
cd frontend
python -m http.server 8080
```

Then visit `http://localhost:8080/challenge.html`

### 4. Start Coding!

1. Enter your username
2. Select a problem from the dropdown
3. Write your Python solution in the editor
4. Click "Submit Solution" to get instant feedback
5. Check the leaderboard to see your ranking

## 📁 Project Structure

```
├── server.py              # FastAPI backend server
├── grader.py              # Code execution and grading logic
├── leaderboard.json       # Persistent leaderboard storage
├── frontend/
│   ├── challenge.html     # Main coding interface
│   ├── challenge.css      # Styling for challenge page
│   ├── challenge.js       # Interactive functionality
│   ├── index.html         # Landing page with leaderboard
│   ├── style.css          # Landing page styles
│   └── script.js          # Landing page logic
└── test_cases/            # Problem definitions and test cases
    ├── power-of-two.json
    ├── three_sum.json
    └── ... (more problems)
```

## 🎯 Adding New Problems

Create a new JSON file in the `test_cases/` directory:

```json
{
  "problem_id": "your-problem-name",
  "public_tests": [
    {
      "input": "5\n",
      "expected_output": "120\n"
    }
  ],
  "hidden_tests": [
    {
      "input": "0\n", 
      "expected_output": "1\n"
    }
  ]
}
```

The system will automatically detect and load the new problem.

## 💡 Solution Format

All solutions must implement a `solve()` function that reads from stdin and prints to stdout:

```python
def solve():
    # Read input
    n = int(input().strip())
    
    # Process and calculate result
    result = your_logic_here(n)
    
    # Print output
    print(result)
```

## 🏆 Scoring System

- **Full Credit**: All test cases pass
- **Partial Credit**: Some test cases pass
- **No Credit**: No test cases pass
- **Leaderboard**: Shows best score per user per problem

## 🔧 API Endpoints

- `GET /problems` - List all available problems
- `POST /submit` - Submit a solution for grading
- `GET /leaderboard` - Get current leaderboard standings

## 🎨 UI Features

### Challenge Interface
- Problem selection dropdown with formatted names
- Syntax-highlighted Python code editor
- Real-time form validation
- Animated submission feedback
- Modal success dialogs with confetti

### Leaderboard
- Live updates after each submission
- Ranking with medal indicators (🥇🥈🥉)
- Responsive table design
- Dark/light theme support

## 🧪 Testing

Run the included test script to verify everything works:

```bash
python tmp_rovodev_test_backend.py
```

This will test:
- Problem loading
- Correct solution submission
- Incorrect solution handling
- Leaderboard functionality

## 🔒 Security Features

- **Timeout Protection**: Code execution limited to 5 seconds
- **Sandboxed Execution**: Each submission runs in isolation
- **File Cleanup**: Temporary files are automatically removed
- **Error Handling**: Graceful handling of runtime errors

## 🎯 Example Problems Included

1. **Power of Two**: Check if a number is a power of 2
2. **Three Sum**: Find triplets that sum to zero
3. **Binary Search Insert Position**: Find insertion point in sorted array
4. **Elimination Game**: Array elimination simulation
5. **Find Town Judge**: Graph theory problem
6. And many more...

## 🚀 Future Enhancements

- [ ] User authentication and profiles
- [ ] Problem difficulty levels
- [ ] Detailed test case feedback
- [ ] Code sharing and solutions
- [ ] Contest mode with time limits
- [ ] Multi-language support
- [ ] Database integration

## 📝 Contributing

1. Add new problems in `test_cases/`
2. Enhance the UI with additional features
3. Improve the grading system
4. Add new themes and animations

## 🐛 Troubleshooting

**Backend won't start:**
- Ensure FastAPI and uvicorn are installed
- Check that port 8000 is available

**Frontend not loading problems:**
- Verify the backend is running
- Check browser console for CORS errors
- Ensure test_cases directory has JSON files

**Submissions failing:**
- Check that your `solve()` function is implemented
- Verify input/output format matches test cases
- Test with simple print statements first

---

Built with ❤️ for coding enthusiasts everywhere!