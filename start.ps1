Start-Process -FilePath python -ArgumentList "-u", "api.py" -NoNewWindow
Start-Process -FilePath python -ArgumentList "-u", "agent.py" -NoNewWindow
streamlit run app.py --server.address=0.0.0.0 --server.port=7860
