# SkyGuard AI — Starter Repo

Read `CONTRACT.md` first — it's the agreement between all three parts of this project.

## Folder structure

```
skyguard-ai/
├── CONTRACT.md      <- the API/DB contract everyone follows
├── backend/         <- Sarika: FastAPI + PostgreSQL
├── ml/              <- Arpit: anomaly detection + synthetic data
└── frontend/        <- Nishita: React dashboard
```

## 1. Backend setup (Sarika)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r ../ml/requirements.txt   # backend imports the ml/ folder directly
```

Create the database once (with PostgreSQL running locally):
```bash
psql -U postgres -c "CREATE DATABASE skyguard;"
```

If your local Postgres user/password differs from `postgres`/`postgres`, set an environment
variable before running the server:
```bash
export DATABASE_URL="postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/skyguard"
```

Run the server:
```bash
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` to see and test the API interactively — this is the
fastest way to check your endpoints without waiting for the frontend to be ready.

## 2. ML setup (Arpit)

```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python data_simulator.py          # preview 10 sample readings
python train_model.py             # trains model.joblib
python detect.py                  # quick manual test of detect_anomaly()
```

Once the backend is running, start the live feed to send continuous data:
```bash
pip install requests
python data_simulator.py --live
```

## 3. Frontend setup (Nishita)

Requires Node.js installed.

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. It polls the backend every 3 seconds — make sure the
backend is running on port 8000 first (see above).

The dashboard has three "Simulate a fault" buttons at the top — use these to trigger
an anomaly live during your demo without waiting for the random simulator timing.

## Suggested build order 

1. Backend: get `/api/ingest` saving to the DB (fake ML result is fine at first).
2. Frontend: get the dashboard rendering `/api/stations/live`, even with fake data.
3. ML: get `detect_anomaly()` working standalone (test with `python detect.py`).
4. Plug ML into backend (already wired in `main.py` — just make sure `model.joblib` exists).
5. Start the live simulator and confirm the full loop end-to-end.
6. Then, and only then, add polish (map view, styling, extra endpoints).
