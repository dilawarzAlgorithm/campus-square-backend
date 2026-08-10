# 🏛️ Campus Square - Core API (Backend)

The official backend infrastructure for Campus Square, a unified, exclusive ecosystem designed to replace fragmented college communication tools like WhatsApp and Telegram.

Built with performance, scalability, and strict access control in mind, this RESTful API powers the mobile frontend across four primary modules: The Square, The Bazaar, The Vault, and The Profile.

# 🚀 Tech Stack

- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Data Validation**: Pydantic
- **Server**: Uvicorn
- **Cloud Storage**: Supabase
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Authentication**: JWT (JSON Web Tokens) with Short-lived Access & Long-lived Refresh Tokens
- **Real-time Engine**: WebSockets

# 🛠️ System Architecture & Features

1. **Domain-Locked Authentication**
   Strict verification layer restricting platform registration to specific institutional email domains (e.g., `@mit.edu`). Implements role-based access control (RBAC) to elevate trusted users to Community Heads for moderation. Secure email-based OTP verification.

2. **Module APIs**

- **The Square API**: Endpoints for global broadcasting, real-time notice propagation, roommate preference matching, and location-tagged Lost & Found logging. Includes dynamic sorting by 'Most Voted' or 'Recent' and a dedicated 'Discussions' tab for peer interaction.
- **The Bazaar API**: Handles peer-to-peer marketplace logic including saving/bookmarking items, and secure routing to the DM hub.
- **The Vault API**: Structured data endpoints for department-wise academic resources (PYQs, Notes, Syllabus) paired with a robust upvote/downvote ranking algorithm and deduplication logic via SHA256 hashing.
- **The Profile API**: Gamified Karma calculation engine that tracks user trust metrics, platform contributions, and configurable storage quotas.

3. **Real-Time Communication (WebSocket Hub)**
   A scalable multi-connection WebSocket architecture supporting real-time Direct Messages (DMs) and Group/Departmental chats. Includes typing indicators, delivered/read receipts, active presence tracking (online/last seen), and live editing/deleting.

4. **Global Campaign & Theme Engine**
   Dynamic configuration endpoints allowing Global Administrators and Community Heads to instantly push UI updates (Lottie animations, persistent banners) and completely reskin the app (hex color overrides) without requiring App Store/Play Store updates.

5. **Admin & Moderation Tools**
   Role-based endpoints enabling administrators to block rogue users, enforce storage limits, trigger auto-roll number assignments, and broadcast urgent emergency push notifications.

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
