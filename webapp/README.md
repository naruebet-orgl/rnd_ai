# RND AI - Supplement Management System

A full-stack web application built with Next.js 15, React 19, tRPC, and MongoDB for managing supplement orders, inventory, and shipping.

## Tech Stack

**Frontend:**
- Next.js 15 (App Router)
- React 19
- TypeScript 5.9.3
- Tailwind CSS
- shadcn/ui components
- TanStack Query (React Query)

**Backend:**
- tRPC 11.x (Type-safe API)
- MongoDB 6.20+ (Database)
- Zod (Schema validation)
- bcryptjs (Password hashing)

**Additional:**
- jsPDF (PDF generation)
- Lucide React (Icons)

## Quick Start

### Prerequisites
- Node.js 18+
- npm 9+
- MongoDB (installed via Homebrew)

### Installation

```bash
# Clone and install dependencies
cd /Users/naruebet.orgl/Workspace/Labs/rnd_ai/webapp
make install

# Or manually
npm install
```

### Development

```bash
# Start MongoDB + Next.js dev server
make dev

# Or start individually
make mongodb-start
npm run dev
```

The application will be available at:
- **Local:** http://localhost:3000 (or http://localhost:3004 if port 3000 is in use)

### Available Make Commands

```bash
make help            # Show all available commands
make dev             # Start MongoDB and Next.js dev server
make start           # Alias for 'make dev'
make stop            # Stop all services
make mongodb-start   # Start MongoDB only
make mongodb-stop    # Stop MongoDB only
make mongodb-status  # Check MongoDB status
make install         # Install dependencies
make clean           # Clean and reinstall dependencies
make seed            # Seed admin account
make build           # Build for production
make lint            # Run ESLint
```

## Project Structure

```
webapp/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   ├── auth/         # Authentication endpoints
│   │   └── trpc/         # tRPC handler
│   ├── admin/            # Admin pages
│   ├── dashboard/        # Dashboard
│   ├── login/            # Login page
│   ├── signup/           # Signup page
│   ├── shipping/         # Shipping management
│   └── order/            # Order page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   └── ...               # Custom components
├── lib/                  # Utilities & configurations
│   ├── mongodb.ts        # MongoDB client
│   ├── types.ts          # TypeScript types & Zod schemas
│   ├── auth-context.tsx  # Auth context
│   └── trpc-client.ts    # tRPC client
├── server/               # tRPC server
│   ├── routers/          # API routers
│   │   ├── auth.ts
│   │   ├── orders.ts
│   │   ├── products.ts
│   │   └── users.ts
│   ├── index.ts          # Main router
│   └── trpc.ts           # tRPC config
├── scripts/              # Utility scripts
├── docs/                 # Documentation
└── references/           # Reference code
```

## Environment Configuration

Create a `.env.local` file:

```env
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017/rnd_ai

# For MongoDB Atlas (optional)
# MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/rnd_ai
```

## Features

- **Authentication:** Email/password with session management
- **Multi-role System:** Admin, Shipper, Shopper
- **Order Management:** Create and track orders from multiple channels
  - Line
  - Shopee
  - Lazada
  - Other
- **Product/Inventory Management:** Track stock levels and movements
- **Credit System:** Organization-based credit management
- **Shipping Calculator:** Calculate shipping costs with multiple components
- **Activity Logging:** Track user and product activities
- **PDF Export:** Export orders and reports to PDF

## Pages & Routes

- `/` - Home (Order Form)
- `/login` - Login page
- `/signup` - Signup page
- `/dashboard` - Dashboard (view & manage orders)
- `/shipping` - Shipping management
- `/order` - Order page
- `/admin/credits` - Credit management (admin only)
- `/admin/orders` - Order management (admin only)
- `/admin/products` - Product management (admin only)

## Database

**MongoDB Database:** `rnd_ai`

**Collections:**
- `accounts` - User authentication
- `users` - User profiles
- `organizations` - Organization data
- `orders` - Order records
- `products` - Product inventory
- `sessions` - User sessions
- `creditTransactions` - Credit history
- `userLogs` - User activity logs
- `productLogs` - Product activity logs

## Development Workflow

1. **Start services:** `make dev`
2. **Create account:** Visit http://localhost:3000/signup
3. **Login:** Visit http://localhost:3000/login
4. **Create orders:** Use the home page order form
5. **View dashboard:** Track orders and statistics
6. **Stop services:** `make stop`

## Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run seed-admin   # Seed admin account (when script exists)
```

## MongoDB Management

```bash
# Start MongoDB
make mongodb-start

# Stop MongoDB
make mongodb-stop

# Check status
make mongodb-status

# Access MongoDB shell
mongosh
```

## Building for Production

```bash
# Build the application
make build

# Or
npm run build

# Start production server
npm start
```

## Troubleshooting

### Port Already in Use
If port 3000 is in use, Next.js will automatically use the next available port (e.g., 3004).

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
make mongodb-status

# Restart MongoDB
make mongodb-stop
make mongodb-start
```

### Clean Install
```bash
# Remove node_modules and reinstall
make clean
```

## Documentation

For more detailed documentation, see the `docs/` directory:
- `getting-started.md` - Setup guide
- `features.md` - Feature documentation
- `database-schema.md` - Database schema
- `api-documentation.md` - API reference
- `deployment.md` - Deployment guide

## License

Private project for RND AI

## Support

For issues or questions, refer to the documentation in the `docs/` directory.
