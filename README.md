# Solio - Crowdfunding on Solana

![Solio Banner](app/static/images/solio-main.png)

**Solio** is a decentralized crowdfunding platform built on the Solana blockchain. Create projects, receive donations in SOL, and enjoy instant payouts with minimal fees.

🌐 **Live Demo:** [https://solio.fun](https://solio.fun)

## Features

### For Project Creators
- **Create Campaigns** - Set funding goals, deadlines, and descriptions
- **Milestone Tracking** - Define funding milestones with automatic notifications
- **Reward Tiers** - Offer rewards to supporters at different donation levels
- **Project Updates** - Post updates to keep your backers informed
- **Instant Payouts** - Receive 97.5% of funds directly to your wallet when campaign ends
- **Analytics Dashboard** - Track donations, supporters, and progress

### For Supporters
- **Wallet Login** - Connect with Phantom, Solflare, or Backpack
- **Direct Donations** - Send SOL directly, no intermediaries
- **Comments & Discussion** - Engage with project creators
- **Donation History** - Track all your contributions
- **Notifications** - Get updates on projects you support

### Platform Features
- **2.5% Platform Fee** - One of the lowest in crypto crowdfunding
- **Token Holder Benefits** - Hold $SOLIO for reduced fees (down to 0.5%)
- **Multiple Auth Options** - Email, Google, Twitter/X, or Solana wallet
- **Categories** - Gaming, Art, Technology, Music, Film, Design, Community
- **Search & Filters** - Find projects by category, popularity, or deadline
- **Admin Panel** - Moderate projects and manage users

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Database:** PostgreSQL (production) / SQLite (development)
- **Blockchain:** Solana (mainnet/devnet)
- **Frontend:** Jinja2 templates, vanilla JavaScript
- **Wallet Integration:** Phantom, Solflare, Backpack
- **Authentication:** Flask-Login, Authlib (OAuth)
- **File Storage:** Local / Cloudinary (optional)

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (for production) or SQLite (for development)
- Solana wallet (for platform operations)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/solio.git
   cd solio
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration (see [Environment Variables](#environment-variables) below).

5. **Initialize the database**
   ```bash
   flask db upgrade
   flask seed-categories  # Optional: seed default categories
   ```

6. **Run the development server**
   ```bash
   python run.py
   ```

   Visit `http://localhost:5000` in your browser.

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required

```env
# Flask
SECRET_KEY=your-secret-key-generate-a-random-string
FLASK_ENV=development

# Database (use SQLite for development)
DATABASE_URL=sqlite:///solio.db

# For PostgreSQL (production):
# DATABASE_URL=postgresql://user:password@localhost:5432/solio

# Solana Configuration
USE_DEVNET=true  # Set to 'false' for mainnet
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_DEVNET_RPC_URL=https://api.devnet.solana.com

# Platform Wallet (REQUIRED for receiving donations)
# Create a new wallet and add the public address and secret key
PLATFORM_WALLET_ADDRESS=YourSolanaWalletPublicAddress
PLATFORM_WALLET_SECRET=YourWalletSecretKeyInBase58
```

### Optional - OAuth (Social Login)

```env
# Google OAuth
# Get credentials at: https://console.cloud.google.com/
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Twitter/X OAuth
# Get credentials at: https://developer.twitter.com/
TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret
```

### Optional - Email (SMTP)

```env
# Email notifications
MAIL_SERVER=smtp.yourprovider.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=Solio <noreply@solio.fun>
SUPPORT_EMAIL=support@solio.fun
```

### Optional - Other Services

```env
# Cloudinary (for image uploads)
# Get credentials at: https://cloudinary.com/
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Redis (for rate limiting in production)
REDIS_URL=redis://localhost:6379/0

# Platform fee percentage (default: 2.5)
PLATFORM_FEE_PERCENT=2.5
```

## Generating Secret Key

Generate a secure secret key for your `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Creating a Platform Wallet

The platform wallet receives all donations. To set it up:

1. **Create a new Solana wallet** using [Phantom](https://phantom.app/), [Solflare](https://solflare.com/), or any Solana wallet
2. **Export the private key** (in base58 format)
3. **Add to `.env`:**
   ```env
   PLATFORM_WALLET_ADDRESS=YourPublicAddress
   PLATFORM_WALLET_SECRET=YourPrivateKeyBase58
   ```

> ⚠️ **Security Warning:** Never commit your `.env` file or expose your private keys. Use a dedicated wallet for the platform, not your personal wallet.

## Project Structure

```
solio/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration
│   ├── extensions.py         # Flask extensions
│   ├── models/               # Database models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── donation.py
│   │   ├── milestone.py
│   │   ├── reward_tier.py
│   │   ├── comment.py
│   │   ├── notification.py
│   │   └── ...
│   ├── routes/               # Route handlers
│   │   ├── main.py           # Homepage, static pages
│   │   ├── auth.py           # Authentication
│   │   ├── projects.py       # Project CRUD
│   │   ├── donations.py      # Donation processing
│   │   ├── profile.py        # User profiles
│   │   ├── notifications.py  # Notifications
│   │   └── admin.py          # Admin panel
│   ├── services/             # Business logic
│   │   ├── solana_service.py # Blockchain interactions
│   │   ├── payout_service.py # Automatic payouts
│   │   ├── notification_service.py
│   │   └── ...
│   ├── templates/            # Jinja2 templates
│   ├── static/               # CSS, JS, images
│   └── utils/                # Helpers, validators
├── migrations/               # Database migrations
├── scripts/                  # Utility scripts
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── run.py                    # Development server
└── README.md
```

## Deployment

### Using Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name solio.fun;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/solio/app/static;
        expires 30d;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/solio.service`:

```ini
[Unit]
Description=Solio Crowdfunding Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/solio
Environment="PATH=/path/to/solio/venv/bin"
EnvironmentFile=/path/to/solio/.env
ExecStart=/path/to/solio/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable solio
sudo systemctl start solio
```

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/` | List all projects |
| GET | `/projects/<slug>` | Project detail |
| GET | `/projects/api/list` | Projects API (JSON) |
| GET | `/donations/stats` | Platform statistics |

### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/create` | Create new project |
| POST | `/donations/verify` | Verify donation transaction |
| GET | `/profile/dashboard` | User dashboard |
| GET | `/notifications/` | User notifications |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/` | Admin dashboard |
| POST | `/admin/projects/<id>/ban` | Ban project |
| POST | `/admin/users/<id>/toggle-admin` | Toggle admin status |

## $SOLIO Token

Hold $SOLIO tokens to unlock platform benefits:

| Tokens Held | Platform Fee |
|-------------|-------------|
| 0 | 2.5% |
| 3M+ | 2.0% |
| 5M+ | 1.5% |
| 10M+ | 1.0% |
| 15M+ | 0.5% |

**Contract Address:** `AppUx1Y2ceZbeRbx81peSUAwowSbacDSJhJPyiJupump`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

If you discover a security vulnerability, please send an email to security@solio.fun instead of using the issue tracker.

## License

This project is open source and available under the [MIT License](LICENSE).

## Links

- **Website:** [https://solio.fun](https://solio.fun)
- **Twitter/X:** [@SolioSol](https://x.com/SolioSol)
- **Telegram:** [t.me/solioapp](https://t.me/solioapp)
- **Token:** [Pump.fun](https://pump.fun/coin/AppUx1Y2ceZbeRbx81peSUAwowSbacDSJhJPyiJupump)

---

Built with ❤️ on Solana
