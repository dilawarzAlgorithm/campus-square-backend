# 🏛️ Campus Square - Core API (Backend)

The official backend infrastructure for Campus Square, a unified, exclusive ecosystem designed to replace fragmented college communication tools like WhatsApp and Telegram.

Built with performance, scalability, and strict access control in mind, this RESTful API powers the mobile frontend across four primary modules: The Square, The Bazaar, The Vault, and The Profile.

## 🚀 Tech Stack

- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Data Validation**: Pydantic
- **Server**: Uvicorn
- **Cloud Storage**: Supabase
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Authentication**: JWT (JSON Web Tokens) with Short-lived Access & Long-lived Refresh Tokens
- **Real-time Engine**: WebSockets

## 🛠️ System Architecture & Features

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

## 🔌 API Endpoints Reference

The Flutter app communicates with the FastAPI server via JWT-authenticated REST routes and WebSockets:

### 🔑 Authentication (`/api/auth`)

| Endpoint                         | Method  | Description                                                     | Access Level  |
| :------------------------------- | :------ | :-------------------------------------------------------------- | :------------ |
| `/api/auth/register`             | `POST`  | Register a new student linked to a verified institution domain. | Public        |
| `/api/auth/verify-otp`           | `POST`  | Verify the 6-digit registration code sent via email.            | Public        |
| `/api/auth/resend-otp`           | `POST`  | Trigger a new verification code email.                          | Public        |
| `/api/auth/login`                | `POST`  | Authenticate students & issue JWT Access/Refresh tokens.        | Public        |
| `/api/auth/login-staff`          | `POST`  | Portal login for Community Heads and Global Admins.             | Staff         |
| `/api/auth/refresh`              | `POST`  | Rotate expired Access Token using a valid Refresh Token.        | Public        |
| `/api/auth/change-password`      | `POST`  | Update temporary or existing account passwords.                 | Authenticated |
| `/api/auth/fcm-token`            | `PATCH` | Register or clear Firebase Cloud Messaging push tokens.         | Authenticated |
| `/api/auth/departments-by-email` | `GET`   | Fetch institution departments based on email domain.            | Public        |
| `/api/auth/me`                   | `GET`   | Retrieve authenticated user profile and Karma tier info.        | Authenticated |
| `/api/auth/name`                 | `PATCH` | Update account first and last name.                             | Authenticated |
| `/api/auth/profile`              | `PATCH` | Update lifestyle preferences (Diet, Sleep, Study habits).       | Authenticated |

---

### 🗄️ Academic Vault (`/api/vault`)

| Endpoint                                  | Method             | Description                                                     | Access Level          |
| :---------------------------------------- | :----------------- | :-------------------------------------------------------------- | :-------------------- |
| `/api/vault/departments`                  | `GET` / `POST`     | Fetch all departments or provision a new department.            | Authenticated / Staff |
| `/api/vault/upload-file`                  | `POST`             | Upload and SHA256-deduplicate learning assets in cloud storage. | Authenticated         |
| `/api/vault/resources`                    | `GET` / `POST`     | Search study material (Notes, PYQs) or publish a new asset.     | Authenticated         |
| `/api/vault/resources/{resource_id}`      | `PATCH` / `DELETE` | Update metadata or permanently delete a Vault asset.            | Owner / Staff         |
| `/api/vault/resources/{resource_id}/vote` | `POST`             | Upvote/downvote an asset (updates author Karma).                | Authenticated         |
| `/api/vault/resources/{resource_id}/save` | `POST`             | Toggle bookmark status for a resource.                          | Authenticated         |
| `/api/vault/saved-resource-ids`           | `GET`              | Fetch IDs of saved academic assets.                             | Authenticated         |
| `/api/vault/saved-resources`              | `GET`              | Retrieve full objects for all bookmarked Vault items.           | Authenticated         |

---

### 📢 The Square Feed (`/api/square`)

| Endpoint                                   | Method         | Description                                                 | Access Level  |
| :----------------------------------------- | :------------- | :---------------------------------------------------------- | :------------ |
| `/api/square/notices`                      | `GET` / `POST` | Retrieve category/sort-filtered feed or publish a new post. | Authenticated |
| `/api/square/notices/{notice_id}`          | `DELETE`       | Delete a notice/post and clean up cloud attachments.        | Owner / Staff |
| `/api/square/notices/{notice_id}/vote`     | `POST`         | Upvote or downvote a post/complaint.                        | Authenticated |
| `/api/square/notices/{notice_id}/comments` | `POST`         | Post a top-level comment or reply to an existing comment.   | Authenticated |
| `/api/square/comments/{comment_id}`        | `DELETE`       | Remove a comment and its nested replies.                    | Owner / Staff |

---

### 🛒 The Bazaar Marketplace (`/api/bazaar`)

| Endpoint                                 | Method             | Description                                           | Access Level  |
| :--------------------------------------- | :----------------- | :---------------------------------------------------- | :------------ |
| `/api/bazaar/products`                   | `GET` / `POST`     | Search active items for sale or create a new listing. | Authenticated |
| `/api/bazaar/my-products`                | `GET`              | Retrieve all items listed by the authenticated user.  | Authenticated |
| `/api/bazaar/products/{product_id}`      | `PATCH` / `DELETE` | Mark item as `SOLD` or remove listing.                | Owner / Staff |
| `/api/bazaar/products/{product_id}/save` | `POST`             | Toggle bookmark status for a marketplace item.        | Authenticated |

---

### 💬 Chat & Real-Time Messaging (`/api/chat`)

| Endpoint                                                    | Method         | Description                                                   | Access Level     |
| :---------------------------------------------------------- | :------------- | :------------------------------------------------------------ | :--------------- |
| `/api/chat/dm/{target_user_id}`                             | `POST`         | Find or initiate a 1-on-1 direct conversation with a peer.    | Authenticated    |
| `/api/chat/conversations`                                   | `GET`          | Fetch all DMs and group conversations sorted by activity.     | Authenticated    |
| `/api/chat/conversations/{id}/messages`                     | `GET` / `POST` | Load historical messages or forward messages to a chat.       | Participants     |
| `/api/chat/conversations/{id}/participants/{user_id}/block` | `PATCH`        | Block or unblock a participant in a chat room.                | Staff            |
| `/api/chat/messages/{message_id}`                           | `DELETE`       | Soft-delete a message or purge associated files.              | Sender           |
| `/api/chat/unread-count`                                    | `GET`          | Get total unread message counter across all chats.            | Authenticated    |
| `/api/chat/ws/{conversation_id}`                            | `WebSocket`    | Live room socket: messages, typing, read receipts, presence.  | Room Participant |
| `/api/chat/ws/hub`                                          | `WebSocket`    | Global user socket for background conversation notifications. | Authenticated    |

---

### ⚙️ Community Management (`/api/community`)

| Endpoint                                         | Method  | Description                                                | Access Level   |
| :----------------------------------------------- | :------ | :--------------------------------------------------------- | :------------- |
| `/api/community/members`                         | `GET`   | List all verified users in the institution.                | Community Head |
| `/api/community/members/{user_id}/role`          | `PATCH` | Promote/demote members (e.g., `STUDENT` to `CAPTAIN`).     | Community Head |
| `/api/community/members/{user_id}/block`         | `PATCH` | Block/unblock a student from campus interactions.          | Community Head |
| `/api/community/members/{user_id}/roll-number`   | `PATCH` | Manually assign or correct a student ID/roll number.       | Community Head |
| `/api/community/members/{user_id}/storage-limit` | `PATCH` | Override custom cloud storage limit (in MB).               | Community Head |
| `/api/community/settings/auto-roll-numbers`      | `POST`  | Toggle auto-extraction of roll numbers from email handles. | Community Head |
| `/api/community/settings/campaign`               | `PATCH` | Configure campus-specific banners, popups, and themes.     | Community Head |

---

### 🌍 Global Administration (`/api/admin`)

| Endpoint                                     | Method          | Description                                                    | Access Level |
| :------------------------------------------- | :-------------- | :------------------------------------------------------------- | :----------- |
| `/api/admin/metrics`                         | `GET`           | Retrieve platform-wide metrics (Total users, campuses, files). | Global Admin |
| `/api/admin/institutions`                    | `GET` / `POST`  | List all registered campuses or provision a new institution.   | Global Admin |
| `/api/admin/institutions/{id}/storage-limit` | `PATCH`         | Update default student storage quota for an entire campus.     | Global Admin |
| `/api/admin/institutions/{id}/campaign`      | `GET` / `PATCH` | Fetch or override campaign settings for a specific campus.     | Global Admin |
| `/api/admin/campaign/global`                 | `PATCH`         | Force an application theme or campaign across ALL campuses.    | Global Admin |
| `/api/admin/users`                           | `GET`           | Global user directory search.                                  | Global Admin |
| `/api/admin/users/{user_id}/block`           | `PATCH`         | Suspend or reactivate user accounts platform-wide.             | Global Admin |

---

### 🔔 Push Notifications & System Utilities

| Endpoint                       | Method | Description                                                  | Access Level  |
| :----------------------------- | :----- | :----------------------------------------------------------- | :------------ |
| `/api/notifications/send`      | `POST` | Dispatch a targeted notification payload to a topic/token.   | Authenticated |
| `/api/notifications/broadcast` | `POST` | Trigger an urgent push notification broadcast to ALL users.  | Global Admin  |
| `/api/utils/app-campaign`      | `GET`  | Fetch dynamic theme colors, launch popups, and banners.      | Authenticated |
| `/api/utils/get-enums`         | `GET`  | Retrieve enumerated system types (Semester, Resource Types). | Public        |
| `/`                            | `GET`  | API root check and system status.                            | Public        |

---

## 💻 Local Development Setup

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

5. Run the test suite

   ```bash
   pytest -v
   ```

6. Start the development server
   ```bash
   uvicorn app.main:app --reload
   ```

_The interactive API documentation (Swagger UI) will be available at http://localhost:8000/docs._

> Developed for the Campus Square Ecosystem.
