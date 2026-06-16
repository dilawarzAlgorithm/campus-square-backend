# 🏛️ Campus Square - Core API (Backend)

The official backend infrastructure for Campus Square, a unified, exclusive ecosystem designed to replace fragmented college communication tools like WhatsApp and Telegram.

Built with performance, scalability, and strict access control in mind, this RESTful API powers the mobile frontend across four primary modules: The Square, The Bazaar, The Vault, and The Profile.

# 🚀 Tech Stack

- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Data Validation**: Pydantic
- **Server**: Uvicorn

# 🛠️ System Architecture & Features

1. **Domain-Locked Authentication**

Strict verification layer restricting platform registration to specific institutional email domains (e.g., `@iiitdwd.ac.in`). Implements role-based access control (RBAC) to elevate trusted users to Community Heads for moderation.

2. **Module APIs**

- **The Square API**: Endpoints for global broadcasting, real-time notice propagation, roommate preference matching, and location-tagged Lost & Found logging.

- **The Bazaar API**: Handles peer-to-peer marketplace logic including combo-listings, countdown timers for urgent sales, and secure WebSockets for the Chat Hub.

- **The Vault API**: Structured data endpoints for department-wise academic resources (PYQs, Notes) paired with a robust upvote/downvote ranking algorithm.

- **The Profile API**: Gamified Karma calculation engine that tracks user trust metrics and platform contributions.

# 💻 Local Development Setup

1. Clone the repository

```bash
git clone https://github.com/dilawarzAlgorithm/campus-square-backend.git
cd campus-square-backend
```

2. Set up the virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run database migrations

```bash
alembic upgrade head
```

5. Start the development server

```bash
uvicorn app.main:app --reload
```

_The interactive API documentation (Swagger UI) will be available at http://localhost:8000/docs._

> Developed for the Campus Square Ecosystem.
