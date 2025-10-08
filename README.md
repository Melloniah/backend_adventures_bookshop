### Adventurers Books Backend

Adventurers Books is an e-commerce backend built with FastAPI, SQLAlchemy, and PostgreSQL, designed for users who want to order online without signing up. Users can track their orders using the email they provide during checkout.

The platform supports delivery per estates in Nairobi (or not, depending on your setup), and orders can be completed via WhatsApp or M-Pesa. Admins can manage products, orders, delivery routes, and categories.

# Tech Stack & Features

Tech Stack: FastAPI | PostgreSQL | SQLAlchemy | JWT Auth | Pydantic | Uvicorn

# Features:

No user registration required – track orders via email

Admin CRUD for products, orders, delivery routes

Products organized by categories:

Books

Stationery

Toys

Art

Technology (e.g., laptops for students)

Users can post orders, track them, see products by category

Delivery coverage per estates in Nairobi

Order completion via WhatsApp or M-Pesa

# Quick Start

Clone & Install

git clone git@github.com:Melloniah/backend_adventures_bookshop.git
cd backend_adventures_bookshop
pipenv install
pipenv shell


# Set Environment Variables (.env)

JWT_SECRET=your_secret_key
DATABASE_URL=postgresql://username:password@host:port/dbname?sslmode=require

#  Email for admin notifications
ADMIN_EMAIL=admin@example.com
FROM_EMAIL=no-reply@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password


# Setup Database

alembic upgrade head
python seed_data.py  # optional seed data


Run Server

uvicorn main:app --reload


API: http://127.0.0.1:8000

Docs: http://127.0.0.1:8000/docs

### Video Demo

[Insert your demo video here]

### API Highlights

Orders: /orders – Create, view, track orders by email

Products: /products – CRUD via admin; browse by category

Categories: /categories – Admin can manage product categories

Delivery Routes: /delivery-routes – Admin CRUD for coverage areas

Users do not need to register. Protected admin routes require Authorization: Bearer <token>

### Production

Host backend + database (DigitalOcean)

Keep .env secrets secure

Use Uvicorn + Gunicorn in production


### License

This project is licensed under the MIT License 