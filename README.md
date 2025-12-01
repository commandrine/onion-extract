Latest version (v1.2) displays download progress. If you need help setting up Python, refer to my Python set up script in the Ubuntu set up repo.

Download "onion-extract" into your desired folder (e.g. "onion-extract"). Set up Python virtual environment (e.g. env).
```
python3 -m venv env
```
Activate virtual enviornment.
```
source env/bin/activate
```
Install required modules.
```
pip3 install -r requirements.txt
```
Sample "onion-extract" command.
```
python3 onion-extract.py -o [download folder name] [onion url]
```

