# fdb-post-reservation

## Prerequisites

- Create a pip virtual environment (e.g. called `venv`)
    ```
    python -m venv venv
    ```
- Activate it
    
    (linux)
    ```
    source venv/bin/activate
    ```
    (windows cmd)
    ```
    .\venv\Scripts\activate
    ```
- Install requirements
    ```
    pip install -r requirements.txt
    ```

## Run

```
python3 app.py
```

## NEXT STEP:

[] Google login
[] Whatsapp login / status

## How Google login works

This app retrieve information from Google sheet using `pygsheet` (to get
the data) or the

- `pygsheet`

    The instruction `client = pygsheets.authorize()` will
