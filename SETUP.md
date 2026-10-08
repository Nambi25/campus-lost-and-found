CampusFind — Campus Lost & Found

CampusFind is a full-stack campus Lost & Found application that helps students report lost/found items, search listings, discover possible matches from images, and securely handle ownership claims.

✨ Features

🔐 User registration and login

👤 User profile and authenticated actions

🔎 Search and filter lost/found items

📷 Upload an image when reporting an item

🧠 Image-based matching using perceptual hash and color similarity

📝 Text/category similarity for matching

🤝 Claim workflow for found items

🔑 Secret verification question for ownership verification

🔢 6-digit handover code after a claim is approved

📦 Lost/found item status management

⚡ React + Vite frontend

🚀 FastAPI backend

🗄️ SQLAlchemy database layer

🐘 PostgreSQL/Supabase support through DATABASE_URL

💻 SQLite fallback for local development

🏗️ Project Structure

campusfind/
│
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI backend
│   ├── models/
│   │   ├── user.py
│   │   ├── item.py
│   │   └── claim.py
│   ├── routes/
│   │   ├── users.py
│   │   ├── items.py
│   │   └── claims.py
│   ├── services/
│   │   └── item_service.py
│   ├── database.py
│   ├── main.py
│   ├── requirements.txt
│   └── uploads/
│
├── ai/                        # AI / matching functionality
│
└── README.md

The existing frontend/, backend/, and ai/ folders are kept as separate application layers.

🚀 Getting Started

1. Requirements

Install:

Python 3.10+

Node.js 18+

npm

Git

Optional for production:

Supabase/PostgreSQL

Vercel

Render/Railway or another Python hosting service

🔧 Backend Setup

Open a terminal:

cd backend

Create a virtual environment:

Windows

python -m venv venv
venv\Scripts\activate

macOS/Linux

python3 -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start FastAPI:

uvicorn main:app --reload

Backend:

http://localhost:8000

Swagger API documentation:

http://localhost:8000/docs

🌐 Frontend Setup

Open a second terminal:

cd frontend

Install dependencies:

npm install

Create:

frontend/.env

Add:

VITE_API_URL=http://localhost:8000

Start the frontend:

npm run dev

The frontend will normally be available at:

http://localhost:5173

🗄️ Database Configuration

The backend supports SQLite for simple local development and PostgreSQL for production.

Local Development

No database setup is required.

The default configuration uses:

SQLite
└── backend/lostfound.db

PostgreSQL / Supabase

For production, set:

DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DATABASE

For example:

DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres

The backend reads DATABASE_URL from the environment.

When the application starts, SQLAlchemy creates the required tables:

users
items
claims

Important

Never commit a real database password, API key, or service-role key to GitHub.

Use environment variables instead.

📷 Image Uploads

During local development, uploaded images are stored under:

backend/uploads/

The API returns image paths such as:

/uploads/example.jpg

The frontend combines the returned path with:

VITE_API_URL

to display the image.

Production Storage

For production deployment, persistent object storage such as Supabase Storage should be used instead of relying on the backend server's local filesystem.

Recommended architecture:

User
 │
 ▼
React / Vercel
 │
 ▼
FastAPI
 │
 ├──────────────► PostgreSQL / Supabase
 │
 └──────────────► Supabase Storage
                         │
                         ▼
                    Permanent photo

Do not rely on backend/uploads/ as permanent production storage when the backend is hosted on an ephemeral/serverless/container platform.

🔐 Authentication

The current application uses the backend authentication API.

Register

POST /users/register

Example request:

{
  "name": "Student Name",
  "email": "student@example.com",
  "password": "your-password",
  "roll_no": "22CS001",
  "phone": "9876543210"
}

Login

POST /users/login

Example:

{
  "email": "student@example.com",
  "password": "your-password"
}

The API returns an authentication token.

Authenticated requests use:

Authorization: Bearer <token>

📡 API Endpoints

Authentication

Method

Endpoint

Purpose

POST

/users/register

Create account

POST

/users/login

Login

GET

/users/me

Get current user

Items

Method

Endpoint

Purpose

GET

/items

List/search items

GET

/items/categories

Get categories

POST

/items

Report lost/found item

GET

/items/mine

Get current user's items

GET

/items/{id}

Get item details

GET

/items/{id}/matches

Get possible matches

POST

/items/search-by-image

Search using an image

PATCH

/items/{id}/status

Update item status

DELETE

/items/{id}

Delete item

Claims

Method

Endpoint

Purpose

POST

/claims

Submit claim

GET

/claims/mine

View user's claims

GET

/claims/item/{item_id}

View claims for an item

POST

/claims/{id}/approve

Approve claim

POST

/claims/{id}/reject

Reject claim

POST

/claims/{id}/complete

Complete handover

🧠 Image Matching

CampusFind uses lightweight image matching that does not require a GPU.

The matching pipeline combines:

Image
 │
 ├── Perceptual Hash
 │
 ├── Color Similarity
 │
 └── Text / Category Similarity
 │
 ▼
Combined Match Score

The system can use this score to rank possible opposite-type items.

For example:

Lost:
Black Casio calculator

        ↓ image search

Found:
Black Casio calculator
Location: AB1
        ↓

High similarity score

The ai/ directory contains the project's AI/matching functionality and should be deployed according to the requirements of the specific AI components being used.

🤝 Claim & Handover Flow

CampusFind uses a verification workflow to reduce false claims.

Step 1 — Finder reports an item

The finder can provide a secret verification question.

Example:

What sticker is on the back of the calculator?

Step 2 — Student submits a claim

The claimant provides:

Answer to the verification question

Proof/details

Step 3 — Finder reviews the claim

The finder can:

Approve
Reject

Step 4 — Handover code

After approval, the system generates a 6-digit handover code.

Step 5 — Pickup

The finder verifies the code before completing the handover.

Claim submitted
      ↓
Finder reviews
      ↓
Approved
      ↓
6-digit code
      ↓
Physical handover
      ↓
Item marked returned

🧪 Testing

Start the backend:

cd backend
uvicorn main:app --reload

Run the backend tests if available:

pytest -q

For API testing, open:

http://localhost:8000/docs

For frontend testing:

cd frontend
npm run dev

☁️ Deployment

Frontend — Vercel

Deploy only the frontend/ directory as the Vercel project root.

Recommended settings:

Framework:
Vite

Build Command:
npm run build

Output Directory:
dist

Set:

VITE_API_URL=https://YOUR-BACKEND-DOMAIN

Do not put private backend secrets in frontend environment variables.

Backend — Render / Railway

Deploy the backend/ directory as a Python web service.

Build command:

pip install -r requirements.txt

Start command:

uvicorn main:app --host 0.0.0.0 --port $PORT

Set:

DATABASE_URL=YOUR_POSTGRES_CONNECTION_STRING

Also configure CORS to allow the deployed Vercel frontend.

Example:

https://your-campusfind.vercel.app

Database — Supabase

Use Supabase PostgreSQL as the production database.

Recommended:

Vercel
   │
   │ HTTPS
   ▼
FastAPI
   │
   ├── PostgreSQL
   │
   └── Storage
        │
        ▼
      Images

🔑 Environment Variables

Frontend

VITE_API_URL=http://localhost:8000

Production:

VITE_API_URL=https://YOUR-BACKEND-DOMAIN

Backend

DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DATABASE

If cloud image storage is enabled, configure the storage credentials required by the storage provider.

Security

Never commit:

.env
.env.local
database passwords
API keys
service-role keys
private tokens

to GitHub.

🔄 Production Data Flow

                    CAMPUSFIND
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
       React / Vite             AI Layer
            │                       │
            │ API                   │
            ▼                       │
       FastAPI Backend ◄────────────┘
            │
       ┌────┴─────┐
       │          │
       ▼          ▼
 PostgreSQL    Image Storage
       │          │
       └────┬─────┘
            ▼
       Persistent Data

🛠️ Development Notes

Keep frontend and backend API contracts synchronized.

Keep AI dependencies isolated from the frontend.

Use environment variables for deployment configuration.

Use PostgreSQL/Supabase for persistent production data.

Use object storage for production images.

Do not commit generated databases or uploaded images.

Do not commit node_modules or Python __pycache__ directories.

📁 Files That Should Not Be Committed

Add these to .gitignore if they are not already present:

.env
.env.*
!.env.example

__pycache__/
*.pyc

venv/
.venv/

node_modules/

*.db
*.sqlite
*.sqlite3

backend/uploads/*
!backend/uploads/.gitkeep

dist/
build/

👥 Team Development

Recommended workflow:

main
 │
 ├── feature/frontend
 ├── feature/backend
 ├── feature/database
 └── feature/ai

Create a branch for each feature and merge through pull requests.

📜 License

Add your team's chosen license here before public release.

CampusFind

A smarter campus Lost & Found platform built to connect lost items with their owners.
