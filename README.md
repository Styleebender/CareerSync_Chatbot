# CareerSync_Chatbot
Your AI-Powered LinkedIn and Career Strategist!!

AI-powered chatbot that helps users optimize their LinkedIn profiles, analyze job fit,  including personalized cover letters and career guidance.

# Documentation:
Architecture and approach overview
<https://github.com/Styleebender/LearnTube_CareerSync/blob/main/Documentation.pdf>

# Prerequisites
Python 3.11 (preferred Python version)

# Setup Instructions
**1. Clone the Repository**
```git clone https://github.com/Styleebender/LearnTube_CareerSync.git```

**2. Create a Virtual Environment**
```
python -m venv venv
venv\Scripts\activate
```

**3. Configure Environment Variables**
Create a .env file in the root directory of your project
to store API keys.
```
GEMINI_API_KEY=your_gemini_api_key_here
SCRAPIN_API_KEY=your_scrapin_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

**4. Install Dependencies**
Install the required Python packages using the requirements.txt file:
```
pip install -r requirements.txt
```

**5. Running the Application**
To run the langGraph script manually
```
python graph.py
```
**Streamlit Application:**
```
streamlit run streamlit_app.py
```
