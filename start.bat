@echo off
start /B python -u api.py
start /B python -u agent.py
streamlit run app.py --server.address=0.0.0.0 --server.port=7860
