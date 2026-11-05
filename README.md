# 🛒 Prezzi Spesa — Italian Grocery Price Comparison

A full-stack web application that compares grocery prices across Italian supermarkets, helping users find the best deals for their shopping list.

## Features

- **Product search** — Full-text search across products, categories, and subcategories (PostgreSQL `tsvector`)
- **Price comparison** — Compare prices for the same product across different supermarkets and cities
- **Smart cart** — Build a shopping list and instantly see which supermarket offers the lowest total cost
- **Side-by-side compare** — Select up to 4 products and compare them in detail
- **Receipt scanning** — Take a photo of a receipt; OCR + LLM extract products and update the database automatically
- **User authentication** — Register/login with JWT tokens and bcrypt password hashing
- **Responsive UI** — Works on desktop and mobile with Quasar's adaptive layout

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Quasar Framework, Pinia, Vue Router, Axios |
| Backend | Python, Flask, Flask-JWT-Extended, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Crawler | asyncio, aiohttp, BeautifulSoup4 |
| OCR/AI | Tesseract OCR, Ollama (LLaMA 3.2) |
| Infrastructure | Docker, Docker Compose, Nginx |

## Project Structure

```
price_comparison/
├── backend/                # Flask REST API
│   ├── app/
│   │   ├── __init__.py     # App factory (create_app)
│   │   ├── config.py       # Dev/Prod/Test configuration
│   │   ├── models.py       # SQLAlchemy models (shared source of truth)
│   │   ├── api/            # Blueprints: auth, products, compare, cart, receipt
│   │   └── utils/          # Decorators, error handlers
│   ├── seed.py             # Database seeder with realistic Italian products
│   ├── run.py              # Entry point
│   └── Dockerfile
├── frontend/               # Quasar (Vue 3) SPA
│   ├── src/
│   │   ├── pages/          # IndexPage, ProductDetail, Compare, Checkout, Auth...
│   │   ├── stores/         # Pinia stores (auth, cart)
│   │   ├── layouts/        # MainLayout with responsive nav
│   │   └── services/       # API wrapper
│   └── Dockerfile
├── crawler/                # Async web scraper
│   ├── fast_crawler.py     # aiohttp + BeautifulSoup crawler
│   ├── category_mapping.py # Italian → English category mapping
│   └── config.py           # Crawler settings
├── docker-compose.yml      # PostgreSQL + Backend + Frontend
└── README.md
```

## Quick Start

### With Docker (recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/price_comparison.git
cd price_comparison

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build

# In another terminal, seed the database
docker compose exec backend python seed.py
```

The app will be available at:
- **Frontend**: http://localhost:9000
- **Backend API**: http://localhost:5000/api

### Manual Setup

#### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
flask --app "app:create_app()" db upgrade

# Seed with sample data
python seed.py

# Run the server
python run.py
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npx quasar dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | List products (search, filter, paginate) |
| `GET` | `/api/products/:id` | Product detail with all prices |
| `GET` | `/api/products/categories` | List categories |
| `GET` | `/api/products/stores` | List stores |
| `GET` | `/api/products/locations` | List locations |
| `GET` | `/api/compare?ids=1,2,3` | Compare up to 4 products |
| `POST` | `/api/cart/calculate` | Calculate cart cost per store |
| `POST` | `/api/auth/register` | User registration |
| `POST` | `/api/auth/login` | User login (returns JWT) |
| `GET` | `/api/auth/me` | Current user profile |
| `POST` | `/api/receipt/scan` | OCR receipt scanning |

## Crawler

The async crawler scrapes product data from Glovo supermarket listings:

```bash
cd crawler

# Scrape all stores in all locations
python fast_crawler.py

# Specific stores and locations
python fast_crawler.py --stores penny conad --locations roma
```

Available stores: `penny`, `conad`, `coop`, `crai`, `deco`, `dodeca`
Available locations: `roma`, `napoli`

## Database Schema

```
stores ──────── product_prices ──────── products
locations ─────┘                         │
                                    sub_categories ── categories
users (separate auth table)
```

- **Products** belong to a subcategory within a category
- **ProductPrice** links a product to a store + location with a price
- **Unique constraint** ensures one price per product/store/location combination

## License

This project was built for educational purposes.
