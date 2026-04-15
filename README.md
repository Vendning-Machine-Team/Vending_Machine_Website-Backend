<img width="2184" height="732" alt="full-deployment-diagram" src="https://github.com/user-attachments/assets/c6757436-f6c6-4801-aa67-71f26c044aeb" />

# Vending Machine Team Website Backend  
### By: Adeyemi Akanbi - [Github](https://github.com/AdeyemiAkanbi), [LinkedIn](https://www.linkedin.com/in/adeyemi-akanbi-62a1a1386/) | Prince Patel - [Github](https://github.com/IMPr1nce), [LinkedIn](https://www.linkedin.com/in/ppatel9114/) | Samantha Machado [Github](https://github.com/SamMac55), [LinkedIn](https://www.linkedin.com/in/samantha-machado-b7b5a7329/)
Advisor: [Matthew Thomas Beck](https://github.com/matthewthomasbeck)  

__Special thanks to the robot and pathfinding teams of this project__   
__Please Consider__: If you like it __star it__!

## Tech Stack
**Language**: Python  
**Backend Framework**: Flask + CORS support  
**Database**: SQLite with SQL schema in data/schema.sql    
**Payments**: Stripe Checkout + Stripe Webhooks   
**Security / Auth Utilities**: bcrypt for password hash verification  
**Integrations / Utilities**: requests (Discord webhooks), python-dotenv (environment configuration), TCP sockets + threading (robot bridge)  

## Roles
Samantha Machado:
* Database Designer (*Created Database Schema and populated tables with data*)
* Software Developer (*Added communication between frontend and backend via API requests*)
* Deployment Manager (*Set up EC2 instance, collaborated to separate frontend-backend repos, migrated DNS to AWS*)

Prince Patel:
* Software Developer (*Integrated Stripe payment system*)

[Matthew Beck](https://www.linkedin.com/in/matthewthomasbeck/):
* Software Developer (*Created web socket to deliver messages from the frontend to the robot*)
* Advisor (*Assisted with EC2 instance setup, collaborated to migrate website frontend and backend to separate repos*)

## Basic information
The backend is a Flask application centered in backend.py that serves both API functionality and built frontend assets from ./dist. It exposes REST endpoints under /api/* for customer checkout flows and administrator operations, while also supporting SPA-style fallback routing so frontend page refreshes still resolve correctly. The application is configured through environment variables (.env) for values such as Stripe keys, webhook secrets, base URL redirects, robot listen host/port, and runtime port.

Operationally, the API is organized around three main domains: product/inventory management, admin activity, and checkout fulfillment. Product and admin endpoints read/write directly to data/vm.db using sqlite3, with tables defined in data/schema.sql (products, administrators, actions, action_type, and valid_codes). Admin login verifies stored password hashes with bcrypt, inventory updates are logged to the actions table, and activity heartbeat endpoints support admin "active" status checks based on recent timestamps.

For payment and delivery, the backend creates Stripe Checkout sessions from the cart payload and embeds cart metadata in the Stripe session. After a successful Stripe webhook callback, the server verifies the webhook signature, parses metadata, and runs idempotent fulfillment (fulfill_checkout_session) that atomically decrements inventory and creates a unique 4-digit vending code tied to the Stripe session. The code is later retrieved by session ID through /api/get-code. In parallel, the backend can send audit messages to Discord and maintain a persistent TCP robot bridge to relay commands and report robot connection status.

## Features
- Customer-facing APIs for product listing, checkout session creation, and post-payment code retrieval  
- Stripe integration with signed webhook handling for payment confirmation and fulfillment  
- Idempotent fulfillment flow that updates inventory and generates a unique vending code per Stripe session  
- Admin APIs for login/logout, activity heartbeat, inventory updates, and recent action history  
- SQLite-backed data model for products, admin users, action logs, and valid vending codes  
- TCP robot bridge for command relay and connection-status reporting (/api/robot-command, /api/robot-status)  
- Discord audit logging for frontend reports, inventory changes, and fulfillment-related alerts  

