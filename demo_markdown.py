#!/usr/bin/env python3
"""
Test script to demonstrate markdown formatting in the chat window.

This script creates a simple demo showing how markdown from different LLM providers
(OpenAI, Gemini, Anthropic) is rendered in the chat interface.
"""

import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt

# Add src to path for imports
sys.path.insert(0, "src")

from src.controllers.main_window import MainWindowController


class MarkdownDemo(QWidget):
    """Demo window showing markdown formatting capabilities."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Formatting Demo")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Create main window controller but extract just the chat display
        self.main_controller = MainWindowController()
        self.chat_display = self.main_controller.chat_display

        # Demo buttons
        openai_btn = QPushButton("Demo OpenAI Response")
        openai_btn.clicked.connect(self.demo_openai)

        gemini_btn = QPushButton("Demo Gemini Response")
        gemini_btn.clicked.connect(self.demo_gemini)

        anthropic_btn = QPushButton("Demo Anthropic Response")
        anthropic_btn.clicked.connect(self.demo_anthropic)

        clear_btn = QPushButton("Clear Chat")
        clear_btn.clicked.connect(self.chat_display.clear)

        layout.addWidget(openai_btn)
        layout.addWidget(gemini_btn)
        layout.addWidget(anthropic_btn)
        layout.addWidget(clear_btn)
        layout.addWidget(self.chat_display)

        self.setLayout(layout)

    def demo_openai(self):
        """Demo typical OpenAI response with formatting."""
        # Simulate user message
        self.main_controller._send_message_demo(
            "How do I use Python for data analysis?"
        )

        # Simulate OpenAI streaming response
        openai_response = """Here's how to get started with **Python for data analysis**:

## Essential Libraries

1. **Pandas** - Data manipulation and analysis
2. **NumPy** - Numerical computing
3. **Matplotlib** - Data visualization
4. **Seaborn** - Statistical visualization

## Basic Example

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Basic analysis
print(df.describe())
print(df.head())

# Simple plot
df['column'].plot(kind='hist')
plt.show()
```

## Key Steps

1. **Data Loading**: Use `pd.read_csv()` or `pd.read_excel()`
2. **Data Cleaning**: Handle missing values with `df.dropna()` or `df.fillna()`
3. **Analysis**: Use `.describe()`, `.value_counts()`, `.groupby()`
4. **Visualization**: Create plots with matplotlib or seaborn

> **Tip**: Start with exploring your data using `df.info()` and `df.head()` to understand its structure.

This approach will help you build strong data analysis skills!"""

        self.simulate_streaming("OpenAI GPT-4", openai_response)

    def demo_gemini(self):
        """Demo typical Gemini response with formatting."""
        self.main_controller._send_message_demo("Explain machine learning concepts")

        gemini_response = """# Machine Learning Fundamentals

Machine learning is a subset of **artificial intelligence** that enables systems to learn from data.

## Core Concepts

### Supervised Learning
- Uses *labeled training data*
- Examples: classification, regression
- Algorithms: Random Forest, SVM, Neural Networks

### Unsupervised Learning  
- Works with *unlabeled data*
- Examples: clustering, dimensionality reduction
- Algorithms: K-means, PCA, DBSCAN

### Key Terms

| Term | Definition |
|------|------------|
| **Feature** | Input variable used for predictions |
| **Label** | Target variable (supervised learning) |
| **Model** | Algorithm trained on data |
| **Training** | Process of learning from data |

## Simple Example

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
```

The key is to start simple and gradually build complexity!"""

        self.simulate_streaming("Gemini Pro", gemini_response)

    def demo_anthropic(self):
        """Demo typical Anthropic response with formatting."""
        self.main_controller._send_message_demo("Best practices for web development")

        anthropic_response = """# Web Development Best Practices

Here are **essential best practices** for modern web development:

## Frontend Development

### HTML Best Practices
- Use semantic HTML elements (`<header>`, `<nav>`, `<main>`, `<footer>`)
- Ensure proper *accessibility* with ARIA labels
- Validate HTML markup

### CSS Organization
```css
/* Use BEM methodology for naming */
.header__navigation--active {
    display: block;
}

/* Mobile-first responsive design */
@media (min-width: 768px) {
    .container {
        max-width: 1200px;
    }
}
```

### JavaScript Guidelines
- Use `const` and `let` instead of `var`
- Implement error handling with try/catch
- **Always** validate user inputs

## Backend Essentials

1. **Security First**
   - Sanitize all inputs
   - Use HTTPS everywhere
   - Implement proper authentication

2. **Performance**
   - Database query optimization
   - Caching strategies
   - Image optimization

3. **Code Quality**
   - Write unit tests
   - Use version control (Git)
   - Follow consistent coding standards

## Development Workflow

```bash
# Example Git workflow
git checkout -b feature/new-component
git add .
git commit -m "Add responsive navigation component"
git push origin feature/new-component
# Create pull request for review
```

### Testing Strategy
- **Unit tests** for individual functions
- **Integration tests** for API endpoints  
- **E2E tests** for user workflows

> **Remember**: Write code as if the person maintaining it is a violent psychopath who knows where you live! 😄

Focus on *maintainability*, *performance*, and *user experience* for successful web applications."""

        self.simulate_streaming("Claude 3.5 Sonnet", anthropic_response)

    def simulate_streaming(self, model_name: str, content: str):
        """Simulate the streaming response from an LLM."""
        # Start message
        self.main_controller._current_message_id = "demo-123"
        self.main_controller._is_streaming = True
        self.main_controller._streaming_content = ""

        # Add model header
        from PySide6.QtGui import QTextCursor

        header_html = f"<br><strong>🤖 {model_name}:</strong><br>"
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(header_html)
        self.main_controller._current_message_start = (
            self.chat_display.textCursor().position()
        )

        # Simulate streaming by processing content in chunks
        words = content.split()
        for i, word in enumerate(words):
            self.main_controller._streaming_content += word + " "

            # Update display every few words (like real streaming)
            if (i + 1) % 5 == 0 or i == len(words) - 1:
                self.main_controller._update_streaming_display()
                QApplication.processEvents()  # Allow UI to update

        # Complete message
        self.main_controller._on_message_completed("demo-123", content)


# Monkey patch a demo method for sending messages without websocket
def _send_message_demo(self, message: str):
    """Demo version of send message that doesn't require websocket."""
    from PySide6.QtGui import QTextCursor

    user_html = f"<br><strong>👤 You:</strong> {message}<br>"
    cursor = self.chat_display.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.insertHtml(user_html)


# Add the demo method to MainWindowController
MainWindowController._send_message_demo = _send_message_demo


def main():
    app = QApplication(sys.argv)

    demo = MarkdownDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
