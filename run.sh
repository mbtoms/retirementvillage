source ../my-project-env/bin/activate
pip3 freeze > requirements.txt  # Python3
streamlit run --server.runOnSave 1 app.py
