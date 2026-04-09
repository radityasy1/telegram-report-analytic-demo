# Rajawali Intelligence Demo Bot

Demo version of the Rajawali Intelligence Telegram bot for Telkomsel Area 3 field operations.

**Bot:** [@demo_portfolio_bot](https://t.me/demo_portfolio_bot)

---

## Quick Start

### Prerequisites
- Python 3.10+
- No database required (uses synthetic data)
- No proxy required (runs outside corporate network)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/rajawali-intelligence-demo.git
cd rajawali-intelligence-demo

# Install dependencies
pip install -r requirements.txt

# Run the bot
python demo_bot.py
```

### Running Tests

```bash
# Run the demo harness to verify all functions
python demo_harness.py
```

---

## Features

This bot runs entirely on **synthetic data** - no connection to:
- Corporate MySQL database
- Corporate proxy
- LDAP/Domain services
- Real ODP/STO data

All data is generated in `.demo_runtime/` directory.

---

## Available Commands

### User Registration & Authentication

| Command | Description | Demo Behavior |
|---------|-------------|---------------|
| `/start` | Start bot & registration | New users can self-register and self-approve |
| `/about` | Bot information | Works normally |
| `/register` | Register new account | Auto-approve enabled |
| `/unreg` | Unregister account | Works normally |
| `/admin` | Admin menu | Works normally |

### Sales & Performance Reports

| Command | Description | Demo Data |
|---------|-------------|-----------|
| `/a3` | Area 3 summary | 5 days of synthetic sales data |
| `/nas` | National summary | 3 regions with mock data |
| `/wok` | WOK summary | Branch-level performance |
| `/agency` | Agency summary | SF performance by agency |
| `/c3mr` | C3MR report | Collection metrics |
| `/pranpc` | PRAN PC report | Payment metrics |
| `/summarize` | Sales driver summary | Territory analysis |

### Order & Ticket Tracking

| Command | Description | Test IDs |
|---------|-------------|----------|
| `/id` | Order history by ID | `AO16670001`, `WO77889901` |
| `/ticket` | Ticket history | `152612345678`, `INC27512345` |

### ODP & Network Tools

| Command | Description | Demo Data |
|---------|-------------|-----------|
| `/odpmap` | ODP map generator | Auto-generated ODP points (10+ per area) |
| `/odpterdekat` | Nearest ODP finder | Auto-generated ODPs near coordinates |
| `/cekodp` | Check ODP history | `ODP-SBY-RAJ/001`, `ODP-SDA-DMO/010` |
| `/churn` | Churn risk analysis | Auto-generated 20+ points per STO |
| `/cvm` | Ten Segment CVM | Customer value metrics |

### Utility Commands

| Command | Description | Demo Behavior |
|---------|-------------|-----------|
| `/daterange` | Set date range | Works normally |
| `/info` | User info | Works normally |
| `/lapor` | Report issue | Saves to local file |
| `/calcpdd` | PDD Calculator | CSI check disabled |

### Admin Commands

| Command | Description | Demo Behavior |
|---------|-------------|-----------|
| `/approve` | Approve pending users | Self-approval enabled |
| `/reject` | Reject pending users | Works normally |
| `/delete` | Delete user | Works normally |
| `/refresh_cache` | Refresh user cache | Works normally |
| `/registered` | List registered users | Works normally |
| `/sendmessage` | Send message to user | Works normally |

---

## Test Data

### Order IDs
```
/id AO16670001     # Completed order
/id WO77889901     # Work order number
```

### BB IDs (Customer IDs)
```
/ticket 152612345678     # Customer with 3 tickets
/ticket INC27512345      # Specific ticket
/ticket INC27511111      # Resolved ticket
/ticket INC27510002      # Closed ticket
```

### ODP Names
```
/cekodp ODP-SBY-RAJ/001   # Surabaya
/cekodp ODP-SDA-DMO/010   # Sidoarjo
/cekodp ODP-MLG-KOT/020   # Malang
/cekodp ODP-SMG-PON/030   # Semarang
/cekodp ODP-DPS-REN/040   # Denpasar
```

### Branches & STOs for ODP Map & Churn

**Branches:** SURABAYA, SIDOARJO, MALANG, SEMARANG, DENPASAR

**STOs:**
| Branch | STOs |
|--------|------|
| SURABAYA | RKT, SBY, SBYUT |
| SIDOARJO | SDA, GEM, PRN |
| MALANG | MLG, LMG, KDR |
| SEMARANG | SMG, SMGUT, KDS |
| DENPASAR | DPS, DPSUT |

**ODP Statuses:** GREEN, YELLOW, ORANGE, RED

---

## Demo Users

Pre-configured users in `.demo_runtime/users/user_data.csv`:

| User ID | Username | NIK | Level | Employer | Status |
|---------|----------|-----|-------|----------|--------|
| 700000001 | @demo_tsel | 94211 | user | tsel | Approved |
| 700000002 | @demo_admin | ADM001 | admin | admin | Approved |
| 700000003 | @demo_sf | UID_SF_001 | user | sf | Approved |
| 700000004 | @demo_pending | 95555 | user | tsel | Pending |

---

## File Structure

```
telegram_bot_demo/
├── demo_bot.py           # Main bot application
├── demo_backend.py       # Synthetic data generators
├── demo_harness.py      # Test harness
├── enhanced_queue_system.py
├── intelligence/
│   └── app.py
├── .demo_runtime/        # Runtime data (auto-created)
│   ├── users/
│   │   └── user_data.csv
│   ├── storage/
│   │   ├── odp_route/
│   │   └── mapping/
│   └── feedback/
└── README.md
```

---

## Environment Variables

Optional configuration:

```bash
BOT_TOKEN=your_token_here      # Default: built-in demo token
DEMO_BOT_TOKEN=your_token_here # Alternative token
BOT_BASE_DIR=/path/to/data    # Default: .demo_runtime/
```

---

## Architecture

This demo bot runs entirely on synthetic data. No database connection required.

All data functions in `demo_backend.py` return realistic fake data matching production structures.

### Auto-Generated Data

The demo automatically generates sufficient synthetic data when static data is insufficient:

- **Churn Analysis:** Minimum 20 points per STO (10 HIGH + 10 LOWMID)
- **ODP Maps:** Minimum 10-15 ODP points per area
- **CVM Heatmaps:** Minimum 10 points per segment per STO
- **Competitor Sites:** Minimum 5 sites per search area

This ensures all map visualizations and clustering analyses work reliably.

### Map Tiles

Maps use **CartoDB Positron** tiles for reliable rendering without API keys or authentication issues.

---

## Self-Approval Flow

New users can **self-approve** their registration:

1. User sends `/start`
2. User completes registration form
3. User receives approval notification (with `[DEMO]` prefix)
4. User runs `/approve <NIK>` to approve themselves
5. User can now use all features

---

## Troubleshooting

### "Database connection failed" error
This bot uses synthetic data only and should never attempt database connections. If you see this:
- Verify you're running `demo_bot.py`
- Check that `demo_backend.py` is properly configured

### "User not found" for demo commands
- Ensure you've registered with `/start`
- Wait for approval notification
- Use `/approve <NIK>` if not auto-approved

### No data returned for commands
- Use the test IDs provided above
- Check that `.demo_runtime/` directory exists and has write permissions

### Maps not loading / 403 errors
- Maps use CartoDB Positron tiles (no API key required)
- Ensure internet connectivity is available
- If behind corporate firewall, check if `*.cartocdn.com` domains are accessible

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Contact

For issues and feature requests, please open an issue on GitHub or contact the repository maintainer.
