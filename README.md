# ShareSync: The Ultimate Peer-to-Peer and Cloud-Backed File Sharing Platform

<!-- Badges Section -->
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB.svg?logo=react)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-000000.svg?logo=flask)](https://flask.palletsprojects.com/)
[![MinIO](https://img.shields.io/badge/Storage-MinIO%20%7C%20S3-FFC300.svg?logo=minio)](https://min.io/)
[![Socket.IO](https://img.shields.io/badge/Realtime-Socket.IO-010101.svg?logo=socket.io)](https://socket.io/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#[Testing])
[![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen.svg)](#[Testing])
[![Version](https://img.shields.io/badge/Version-2.0.0-informational.svg)](#[Changelog])

---

## 🚀 Project Overview

**ShareSync** is a modern, high-performance file sharing platform designed for both **secure, persistent cloud storage** and **lightning-fast, ephemeral Peer-to-Peer (P2P) transfers**. It is built to offer maximum flexibility, allowing users to choose the best method for their file transfer needs, whether it's a quick, direct transfer to a nearby colleague or a secure, long-term share via a robust cloud backend.

The project's core philosophy is to provide a **seamless, privacy-focused, and developer-friendly** solution for file exchange. It serves as a gold-standard example of a full-stack application leveraging modern asynchronous communication, robust API design, and a modular architecture.

### **Purpose**

*   **For End-Users:** To provide a reliable, fast, and secure way to share files of any size, with options for direct P2P transfer or persistent cloud-backed links.
*   **For Developers:** To serve as a comprehensive, well-structured codebase demonstrating best practices in full-stack development, including Flask API design, React frontend, real-time WebSocket communication, and S3-compatible object storage integration.

### **Target Audience**

*   **General Users:** Individuals and teams needing a simple, secure file sharing utility.
*   **System Administrators:** Those looking for a self-hosted, private file sharing solution with full control over data and infrastructure.
*   **Full-Stack Developers:** Engineers interested in learning about Flask, React, WebRTC signaling, and MinIO/S3 integration.

---

## ✨ Features

ShareSync is packed with features that cater to both casual and power users:

| Category | Feature | Description |
| :--- | :--- | :--- |
| **Core Sharing** | **Hybrid Transfer Modes** | Supports both **Persistent Cloud Storage** (via MinIO/S3) and **Ephemeral P2P Transfer** (via WebRTC signaling). |
| | **Secure Uploads** | Files are uploaded to a private S3-compatible bucket with temporary, signed URLs for secure access. |
| | **Download Tracking** | Comprehensive analytics on file downloads, including timestamps and user information. |
| **Real-Time** | **P2P Signaling** | Uses Socket.IO to facilitate WebRTC connection establishment (ICE, Offer/Answer) for direct, high-speed peer-to-peer file transfer. |
| | **Live Progress** | Real-time progress tracking for uploads and P2P transfers via WebSockets. |
| **User & Security** | **OAuth 2.0 Integration** | Seamless sign-in and registration using Google OAuth (extensible to other providers). |
| | **Role-Based Access** | Supports different user roles (e.g., Admin, Standard) with an Admin Dashboard for platform management. |
| | **Rate Limiting** | Robust API rate limiting implemented with Flask-Limiter and Redis to prevent abuse and ensure service stability. |
| | **Automatic Cleanup** | Scheduled background tasks to automatically clean up expired files and temporary data. |
| **Developer** | **Containerized Setup** | Full Docker and Docker Compose support for easy, reproducible local development and deployment. |
| | **Modern Frontend** | Built with React, Vite, and a component library based on **Shadcn UI** for a modern, accessible, and responsive user interface. |

---

## 🛠️ Tech Stack

ShareSync is a full-stack application built with a modern, asynchronous, and scalable technology stack.

| Component | Technology | Rationale for Choice |
| :--- | :--- | :--- |
| **Backend API** | **Python 3.11+** | Known for its readability, extensive libraries, and strong community support. |
| | **Flask** | A lightweight, flexible micro-framework perfect for building a modular, API-focused backend. |
| | **Flask-SocketIO** | Enables real-time, bidirectional communication (WebSockets) for P2P signaling and live updates. |
| **Database** | **SQLAlchemy 2.0** | A powerful and flexible ORM for Python, providing a consistent way to interact with various SQL databases (SQLite, PostgreSQL, MySQL). |
| | **SQLite (Default)** | Simple, file-based database for local development and testing. |
| **Storage** | **MinIO / AWS S3** | S3-compatible object storage for scalable, durable, and cost-effective file persistence. MinIO is used for local development/self-hosting. |
| | **Boto3** | The official AWS SDK for Python, used to interact with MinIO/S3 for file operations. |
| **Frontend** | **React 18+** | A declarative, component-based library for building fast, interactive user interfaces. |
| | **Vite** | A next-generation frontend tooling that provides a fast development server and optimized build process. |
| | **Tailwind CSS** | A utility-first CSS framework for rapidly building custom designs. |
| | **Shadcn UI** | A collection of re-usable components built with Radix UI and Tailwind CSS, ensuring a beautiful and accessible UI. |
| **Caching/Queue** | **Redis** | Used by Flask-Limiter for distributed rate limiting and potentially for session management or background task queuing. |

---

## 🏗️ Architecture Overview

ShareSync follows a **Microservice-Oriented Monolith** architecture, separating concerns into distinct components while maintaining a unified codebase for simplicity.

### **Component Interaction**

1.  **Client (React/Vite):** The user interface, responsible for user interaction, making API calls, and establishing WebSocket connections.
2.  **API Server (Flask):** The central hub. It handles:
    *   **REST API:** User authentication, file metadata management (SQLAlchemy), analytics, and configuration.
    *   **WebSocket Server (Socket.IO):** Manages P2P signaling (WebRTC Offer/Answer/ICE) and real-time progress updates.
3.  **Database (SQLAlchemy/SQLite):** Stores all persistent application data, including user accounts, file metadata, download logs, and configuration settings.
4.  **Object Storage (MinIO/S3):** Stores the actual file binaries. The API server generates **pre-signed URLs** for the client to securely upload and download files directly to/from the storage layer, bypassing the API server for large data transfers.
5.  **Redis:** Used primarily for storing rate-limiting counters and potentially for session data or task coordination.

### **P2P Transfer Flow**

The P2P feature uses the API server only for **signaling**, not for data transfer:

1.  **Join Room:** Two peers (A and B) connect to the Flask-SocketIO server and join a common "room" (e.g., a unique transfer ID).
2.  **Offer/Answer:** Peer A sends a WebRTC **Offer** to the server, which relays it to Peer B. Peer B responds with an **Answer**, which is relayed back to Peer A.
3.  **ICE Candidates:** Both peers exchange **ICE Candidates** (network information) via the server to discover the best direct connection path.
4.  **Direct Connection:** Once the handshake is complete, a **direct, encrypted P2P connection** is established. File data is then transferred directly between Peer A and Peer B, completely bypassing the Flask server.

### **Directory Structure**

```
FileSharingAPP/
├── backend/
│   ├── instance/              # Local configuration and database files
│   ├── src/
│   │   ├── database/          # Database models and initialization
│   │   ├── routes/            # Flask Blueprints (user, upload, p2p, auth, etc.)
│   │   ├── services/          # Business logic (cleanup, storage, security)
│   │   ├── static/            # Frontend build files (served by Flask)
│   │   └── main.py            # Main Flask application entry point
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Example environment variables
├── frontend/
│   ├── public/                # Static assets
│   ├── src/
│   │   ├── components/        # React components (UI, Pages, Layouts)
│   │   ├── hooks/             # Custom React hooks (useAuth, useP2P)
│   │   ├── lib/               # Utility functions (utils.js)
│   │   └── App.jsx            # Main React application
│   ├── package.json           # Node.js dependencies and scripts
│   └── vite.config.js         # Vite configuration
└── my-minio-storage/          # Local MinIO data volume (for Docker/local setup)
```

---

## ⚙️ Installation & Setup Guide

The recommended way to run ShareSync is using **Docker Compose**, which sets up the entire environment (Backend, Frontend, MinIO, Redis) with a single command.

### **Prerequisites**

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### **Quick Start (Docker Compose)**

1.  **Clone the repository:**
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd FileSharingAPP
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file in the root directory (`FileSharingAPP/`) by copying the example file.
    ```bash
    cp backend/.env.example .env
    # Edit the .env file with your desired settings (especially SECRET_KEY)
    ```

3.  **Build and Run the Stack:**
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    *   Build the Python (Flask) backend image.
    *   Build the Node.js (React) frontend image.
    *   Start the MinIO S3-compatible storage service.
    *   Start the Redis caching/rate-limiting service.
    *   Start the combined Flask/Socket.IO server.

4.  **Access the Application:**
    The application will be available at `http://localhost:5001`.

### **Local Development (Without Docker)**

This method requires local installation of Python and Node.js dependencies.

#### **1. Backend Setup (Python)**

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment and activate it
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file (copy from .env.example)
cp .env.example .env

# Run the Flask application
python src/main.py
# The backend API will run on http://localhost:5001
```

#### **2. Frontend Setup (React)**

```bash
# Navigate to the frontend directory
cd ../frontend

# Install dependencies (using pnpm as specified in package.json)
pnpm install

# Start the development server
pnpm run dev
# The frontend will run on http://localhost:5173 (or similar)
```
*Note: You will need to configure the frontend to proxy API requests to the backend server (`http://localhost:5001`) in your Vite config or environment variables.*

---

## 📖 Usage Instructions

### **Cloud-Backed File Sharing**

This is the default mode for persistent, shareable links.

1.  **Upload:** Navigate to the `/upload` page. Drag and drop your file or select it.
2.  **Secure Link Generation:** Upon successful upload, the server stores the file in MinIO/S3 and generates a unique, time-limited download link.
3.  **Sharing:** Share the generated link with recipients.
4.  **Download:** Recipients can access the `/download/<file_id>` endpoint. The server verifies the link and generates a **pre-signed download URL** from the object storage, allowing the recipient to download the file directly.

### **Peer-to-Peer (P2P) Direct Transfer**

For fast, direct transfers between two users on the same network.

1.  **Initiate P2P:** Navigate to the `/p2p` page. A unique **P2P Room ID** will be generated.
2.  **Connect:** The sender and receiver must both navigate to the `/p2p` page and enter the same **P2P Room ID**.
3.  **Signaling:** The application uses the Socket.IO server to exchange WebRTC signaling data (Offer, Answer, ICE Candidates).
4.  **Transfer:** Once the direct connection is established, the sender can select a file. The file data is streamed directly to the receiver's browser, offering the fastest possible transfer speed.
5.  **Ephemeral:** The connection and transfer are ephemeral. Once the peers disconnect, the transfer session is closed, and no data remains on the server.

### **API Endpoints (Example)**

All API endpoints are prefixed with `/api`.

| Method | Endpoint | Description | Example Request (cURL) |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/google` | Initiates Google OAuth login/registration. | *Redirect via UI* |
| `POST` | `/api/upload` | Uploads a file to the cloud storage. | `curl -X POST -F 'file=@/path/to/file.txt' http://localhost:5001/api/upload` |
| `GET` | `/api/files/<file_id>` | Retrieves file metadata and a pre-signed download URL. | `curl http://localhost:5001/api/files/a1b2c3d4` |
| `GET` | `/api/health` | Checks the health and status of the API and database. | `curl http://localhost:5001/api/health` |
| `GET` | `/api/stats` | Retrieves platform usage statistics (Admin only). | `curl -H "Authorization: Bearer <token>" http://localhost:5001/api/stats` |

---

## 🔒 Configuration & Environment Variables

Configuration is managed via environment variables, loaded from the `.env` file by `python-dotenv`.

| Variable | Default Value | Description | Required |
| :--- | :--- | :--- | :--- |
| `FLASK_ENV` | `development` | Sets the Flask environment. Use `production` for secure cookie settings. | No |
| `PORT` | `5001` | The port the Flask server will run on. | No |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | **CRITICAL:** Used for session management and security. **MUST be changed in production.** | Yes |
| `DATABASE_URL` | `sqlite:///src/database/sharesync.db` | SQLAlchemy connection string. Use `postgresql://user:pass@host/db` for production. | No |
| `MAX_CONTENT_LENGTH` | `500 * 1024 * 1024` (500MB) | Maximum file size allowed for upload. | No |
| `MINIO_ENDPOINT` | `http://minio:9000` | MinIO/S3 service endpoint. | Yes |
| `MINIO_ACCESS_KEY` | `minioadmin` | Access key for MinIO/S3. **Change in production.** | Yes |
| `MINIO_SECRET_KEY` | `minioadmin` | Secret key for MinIO/S3. **Change in production.** | Yes |
| `MINIO_BUCKET_NAME` | `sharesync` | The S3 bucket name for file storage. | No |
| `REDIS_URL` | `memory://` | Connection string for Redis. Used for rate limiting. Use `redis://redis:6379/0` in Docker. | No |
| `GOOGLE_CLIENT_ID` | `PLACEHOLDER_GOOGLE_CLIENT_ID` | Client ID for Google OAuth 2.0. | Yes (for OAuth) |
| `GOOGLE_CLIENT_SECRET` | `PLACEHOLDER_GOOGLE_CLIENT_SECRET` | Client Secret for Google OAuth 2.0. | Yes (for OAuth) |
| `FILE_EXPIRY_DAYS` | `7` | Number of days before an uploaded file is automatically deleted by the cleanup service. | No |

---

## 🧪 Testing

ShareSync uses a combination of unit tests for the backend and end-to-end tests for the frontend.

### **Backend Tests (Python)**

The backend uses `pytest` for testing.

1.  **Install Test Dependencies:**
    ```bash
    # Assuming you are in the 'backend' directory with venv activated
    pip install pytest pytest-cov
    ```

2.  **Run Tests:**
    ```bash
    pytest
    ```

3.  **Run Tests with Coverage Report:**
    ```bash
    pytest --cov=src --cov-report=html
    # Open htmlcov/index.html to view the report
    ```

### **Frontend Tests (React)**

The frontend uses a combination of **Vitest** (for unit tests) and **Cypress** (for E2E tests).

1.  **Install Test Dependencies:**
    ```bash
    # Assuming you are in the 'frontend' directory
    pnpm install
    ```

2.  **Run Unit Tests (Vitest):**
    ```bash
    pnpm test:unit
    ```

3.  **Run E2E Tests (Cypress):**
    ```bash
    # Start the application first (via Docker or local servers)
    pnpm test:e2e
    ```

---

## 🚢 Deployment Guide

### **Staging/Production (Cloud)**

For a production environment, it is highly recommended to use a managed database (PostgreSQL or MySQL) and a dedicated S3-compatible storage provider (AWS S3, DigitalOcean Spaces, etc.).

1.  **Provision Services:**
    *   A managed PostgreSQL database.
    *   A managed Redis instance.
    *   An S3-compatible object storage bucket.

2.  **Update Configuration:**
    Modify the `.env` file with the production values:
    *   Set `FLASK_ENV=production`.
    *   Update `DATABASE_URL` to your PostgreSQL connection string.
    *   Update `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, and `MINIO_SECRET_KEY` to your production S3 credentials.
    *   Update `REDIS_URL` to your managed Redis instance.
    *   **CRITICALLY:** Set a strong, unique `SECRET_KEY`.

3.  **Deployment:**
    Deploy the Docker image to a container orchestration service (e.g., Kubernetes, AWS ECS, Google Cloud Run) or a simple VM running Docker. Ensure the application is exposed via a reverse proxy (like Nginx or Caddy) with **SSL/TLS enabled**.

### **CI/CD Tips**

*   **Build Stage:** Use a multi-stage Dockerfile to build the frontend and backend separately, resulting in a minimal final image.
*   **Testing Stage:** Run `pytest` and `pnpm test:unit` in the CI pipeline before deployment.
*   **Database Migrations:** Use Flask-Migrate (Alembic) for database schema changes. **NEVER** rely on `db.create_all()` in production.
    ```bash
    # Example migration commands
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

---

## 🤝 Contributing

We welcome contributions from the community! By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

### **Contribution Process**

1.  **Fork** the repository.
2.  **Clone** your forked repository.
3.  **Create a new branch** for your feature or fix: `git checkout -b feature/my-new-feature`
4.  **Make your changes** and ensure all tests pass.
5.  **Commit your changes** with a descriptive message: `git commit -m "feat: Add new P2P room generation logic"`
6.  **Push** to your branch: `git push origin feature/my-new-feature`
7.  **Open a Pull Request (PR)** against the `main` branch of the original repository.

### **Code Style & Standards**

*   **Python:** Follow **PEP 8** standards. Use a linter like **Flake8** or **Black** for automatic formatting.
*   **JavaScript/React:** Follow standard React best practices. Use **ESLint** (configured in `frontend/package.json`) for code quality.
*   **Commits:** Use **Conventional Commits** (e.g., `feat:`, `fix:`, `docs:`) for clear history.

### **Branching Model**

We use a simplified **Git Flow** model:
*   `main`: Production-ready, stable code.
*   `develop`: Integration branch for new features.
*   `feature/*`: Branches for new features.
*   `fix/*`: Branches for bug fixes.

---

## ❓ Troubleshooting & FAQ

| Issue | Solution |
| :--- | :--- |
| **"Index.html not found"** | Ensure the frontend build process completed successfully. In Docker, this means the `frontend` service built the assets into `backend/src/static`. Run `pnpm run build` in the `frontend` directory if running locally. |
| **P2P connection fails** | Check firewall settings. WebRTC requires UDP ports to be open for direct connection. If behind a restrictive NAT, you may need to configure a **STUN/TURN server** (not included by default). |
| **Rate Limit Exceeded** | The API is protected by Flask-Limiter. If you see a `429 Too Many Requests` error, wait a few minutes. For development, set `REDIS_URL=memory://` or increase limits in `src/main.py`. |
| **OAuth Login Fails** | Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correctly set in your `.env` file and that the **Authorized Redirect URI** is configured in the Google Cloud Console (e.g., `http://localhost:5001/api/auth/google/callback`). |

---

## 🗺️ Roadmap

The future of ShareSync is focused on enhanced security, performance, and user experience.

| Milestone | Target | Description |
| :--- | :--- | :--- |
| **v2.1 - Security & Performance** | Q4 2025 | Implement end-to-end encryption for P2P transfers. Optimize database queries and introduce basic caching layers. |
| **v2.2 - Advanced Sharing** | Q1 2026 | Add password protection for cloud-backed links. Implement folder sharing capabilities. |
| **v3.0 - Full Decentralization** | Mid 2026 | Explore using a fully decentralized storage layer (e.g., IPFS) as an alternative to S3/MinIO. |
| **v3.1 - Mobile App** | Late 2026 | Develop a native mobile application (React Native or similar) for on-the-go file sharing. |

---

## 📜 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 <YOUR_NAME_OR_ORGANIZATION>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments & Credits

*   **Flask & Python Community:** For the robust and flexible backend ecosystem.
*   **React & Vite:** For providing a modern, fast, and enjoyable frontend development experience.
*   **MinIO:** For providing an excellent open-source S3-compatible object storage solution for self-hosting and development.
*   **Shadcn UI & Radix UI:** For the beautiful, accessible, and high-quality UI components.
*   **WebRTC Community:** For the standards and libraries that make P2P communication possible.
*   *Special thanks to all contributors and early testers!*

---

## 📅 Changelog

### **v2.0.0 - The Hybrid Release (Current)**

*   **Feature:** Introduced hybrid file sharing: persistent cloud-backed and ephemeral P2P.
*   **Feature:** Full migration to Flask-SocketIO for real-time P2P signaling.
*   **Refactor:** Upgraded backend to Python 3.11+ and Flask 3.1+.
*   **Refactor:** Upgraded frontend to React 18+ and Vite 6.
*   **Improvement:** Implemented robust API rate limiting using Redis.
*   **Improvement:** Added Admin Dashboard routes and basic analytics tracking.

### **v1.0.0 - Initial Cloud-Only Release**

*   Initial release with basic user authentication and cloud-backed file uploads (S3/MinIO).
*   Basic file metadata storage with SQLAlchemy.
*   Simple React frontend with basic upload/download functionality.
