# University Assistant - Quiz Helper

Welcome to the University Assistant Quiz Helper repository! This project is a proof-of-concept (POC) application designed to assist university students with class quizzes using the power of large language models (LLMs). The app leverages Langchain, Streamlit, and GPT-4 to provide a seamless and interactive experience for students.

## Features

- **Interactive Quiz Assistance**: Students can get instant help with quiz questions.
- **GPT-4 Powered**: Utilizes OpenAI's GPT-4 for generating accurate and contextual responses.
- **Easy to Use Interface**: Built with Streamlit for a user-friendly and responsive UI.
- **Flexible Integration**: Employs Langchain for managing language model interactions and integrating various data sources.

## Tech Stack

- **Langchain**: For orchestrating and managing language model operations.
- **Streamlit**: Provides a simple and efficient way to create an interactive web interface.
- **GPT-4**: The core engine for natural language understanding and response generation.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- An OpenAI API key for accessing GPT-4

### Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/yourusername/university-assistant-quiz-helper.git
    cd university-assistant-quiz-helper
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up your OpenAI API key:
    ```bash
    export OPENAI_API_KEY='your-api-key-here'
    ```

### Running the App

Start the Streamlit app by running:
```bash
streamlit run app.py
