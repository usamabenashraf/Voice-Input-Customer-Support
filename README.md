# Follow the instructions below to run the app:
- Click the “Code” drop-down button on this GitHub repository page.
- Click the “Codespaces” tab.
- Click the “+” icon to create a new codespace.
- Go to the codespace page and wait for it to set up.
- Execute the following commands in the terminal (they will take some time to execute):
```
chmod +x run_app.sh
./run_app.sh
source venv/bin/activate
uvicorn api:app --reload
```
- Open another terminal by clicking the "+" icon and execute the following commands:
```
source venv/bin/activate
streamlit run main.py
```
- Click the “Open browser” button in the pop-up that appears. It will take us to a new page.
- Hear, we can click the mic icon to record a message and then wait for the apps response.
