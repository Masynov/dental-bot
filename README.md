
Telegram Appointment Booking Bot (Dentistry)
A production-ready commercial solution for local medical clinics and private practitioners. The bot automates patient intake, eliminating the need for manual messaging and paper logbooks.

🚀 Core Features
Interactive Questionnaire (FSM): Step-by-step patient data collection (name, verified phone number, preferred time, and case description) directly inside Telegram.

Instant Notifications: The administrator or doctor immediately receives a structured lead card in a private workspace chat, complete with a clickable link to the patient's profile for quick contact.

Google Sheets as a Database: All completed forms are logged into a cloud-based Google Sheet in real-time. This allows the doctor to track appointments, update statuses, and view analytics from any device.

🔒 Security & Architecture
Privacy Protection: All sensitive data (bot token, chat IDs, API credentials) is fully isolated within environment variables (.env) to prevent leaks.

Fault Tolerance (Anti-Flood / Injection Protection): User input is automatically escaped. The bot is protected from crashes caused by special characters or attempts to break message formatting.

Cloud Hosting Optimization: Features a built-in, lightweight asynchronous web server (aiohttp) to integrate with uptime monitoring services (UptimeRobot), guaranteeing 24/7 availability even on free hosting tiers (Render).

🛠 Tech Stack
Language: Python 3.11+

Framework: Aiogram 3 (asynchronous framework for Telegram bots)

Integrations: Google Sheets API (gspread), aiohttp (web server), python-dotenv (configuration management).
