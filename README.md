# Travel Booking Platform (Python Version)

This project is a travel booking platform built entirely in Python. It provides:
- A FastAPI backend with endpoints for flight and hotel search (integrated with Travelpayouts API)
- A Telegram bot for searching flights and hotels
- A web frontend (HTML forms, rendered by FastAPI)

## Features
- Flight and hotel search via Travelpayouts API
- Affiliate booking links with partner ID
- Telegram bot for travel search
- Simple web interface (no JavaScript required)

## Requirements
- Python 3.8+
- pip

## Setup
1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set your Travelpayouts API token and partner ID:**
   - Copy `.env.example` to `.env` and fill in your credentials.
4. **Run both the FastAPI server and Telegram bot together:**
   ```bash
   python start_all.py
   ```
   - Or, run them separately:
     - FastAPI server: `uvicorn app.main:app --reload`
     - Telegram bot: `python bot/bot.py`
5. **Access the web frontend:**
   - Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure
```
travel_booking/
  app/
    main.py           # FastAPI app
    templates/        # HTML templates
    static/           # (optional) static files
  bot/
    bot.py            # Telegram bot
  requirements.txt
  .env.example
  start_all.py
  README.md
```

## Notes
- All API endpoints are documented at `/docs` (FastAPI Swagger UI).
- The Telegram bot supports flight and hotel search commands.
- Booking links include your affiliate partner ID.

## 🌍 Global360World - Travel Booking Platform

A comprehensive travel booking platform that integrates with Travelpayouts.com API, featuring a web interface and Telegram bot for seamless travel planning and booking.

## 🚀 Features

### ✈️ Flight Booking
- Search for flights with multiple trip types (One Way, Return, Multi-city)
- Real-time pricing from multiple airlines
- Advanced filtering options
- Price tracking and notifications

### 🏨 Hotel Booking
- Search hotels by destination
- Filter by amenities, rating, and price
- Real-time availability checking
- Detailed hotel information

### 🎯 Combined Search
- Search flights and hotels simultaneously
- Package deals and recommendations
- Integrated booking experience

### 🤖 Telegram Bot
- Multi-language support (8 languages)
- Interactive conversation flow
- Real-time search and booking
- Price tracking and notifications

### 🚗 Additional Services
- Car & Bike rentals
- Train & Bus tickets
- Airport transfers
- Tours & Activities
- eSIM purchases

## 🛠️ Technology Stack

- **Backend**: Node.js, Express.js
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite
- **API Integration**: Travelpayouts.com
- **Bot Framework**: Telegraf
- **Additional**: Axios, CORS, Rate Limiting

## 📋 Prerequisites

- Node.js (v16.0.0 or higher)
- npm (v8.0.0 or higher)
- Travelpayouts.com API token
- Telegram Bot Token

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travel-api-development
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   PORT=3000
   TRAVELPAYOUTS_TOKEN=your_travelpayouts_token
   BOT_TOKEN=your_telegram_bot_token
   NODE_ENV=development
   ```

4. **Database Setup**
   The SQLite database will be created automatically on first run.

## 🏃‍♂️ Running the Application

### Start the API Server
```bash
npm start
# or for development
npm run dev
```

### Start the Telegram Bot
```bash
npm run bot
# or for development
npm run dev-bot
```

### Start Both Services
```bash
# Terminal 1: API Server
npm start

# Terminal 2: Telegram Bot
npm run bot
```

## 🌐 API Endpoints

### Flight Search
```
POST /api/flights/search
```
**Parameters:**
- `origin` (required): Departure city code
- `destination` (required): Arrival city code
- `departure_date` (required): Departure date (YYYY-MM-DD)
- `return_date` (optional): Return date (YYYY-MM-DD)
- `currency` (optional): Currency code (default: USD)
- `trip_type` (optional): oneway/return/multi

### Hotel Search
```
POST /api/hotels/search
```
**Parameters:**
- `city` (required): Destination city
- `check_in` (required): Check-in date (YYYY-MM-DD)
- `check_out` (required): Check-out date (YYYY-MM-DD)
- `adults` (optional): Number of adults (default: 2)
- `currency` (optional): Currency code (default: USD)

### Combined Search
```
POST /api/search/combined
```
**Parameters:**
- All flight parameters
- All hotel parameters
- Returns both flight and hotel results

### City Suggestions
```
GET /api/cities/search?query=city_name
```

### Additional Services
- `POST /api/cars/search` - Car rentals
- `POST /api/trains/search` - Train tickets
- `POST /api/transfers/search` - Airport transfers
- `POST /api/tours/search` - Tours & activities
- `GET /api/esim/offers` - eSIM offers

## 🤖 Telegram Bot Features

### Supported Languages
- 🇺🇸 English
- 🇪🇸 Spanish
- 🇷🇺 Russian
- 🇺🇦 Ukrainian
- 🇧🇷 Portuguese
- 🇮🇹 Italian
- 🇹🇷 Turkish
- 🇮🇳 Hindi

### Bot Flow
1. **Language Selection** - Choose your preferred language
2. **Country Selection** - Select your country
3. **Currency Selection** - Choose your currency
4. **Main Menu** - Access all services
5. **Service Selection** - Choose specific service
6. **Search Flow** - Guided search process
7. **Results Display** - View and book options

### Bot Commands
- `/start` - Start the bot
- `/help` - Show help information
- `/language` - Change language
- `/currency` - Change currency

## 🎨 Web Interface

### Features
- **Responsive Design** - Works on all devices
- **Tab-based Navigation** - Easy switching between services
- **Real-time Search** - Instant results
- **Modern UI** - Beautiful and intuitive design
- **Error Handling** - User-friendly error messages

### Tabs
1. **Flights** - Search and book flights
2. **Hotels** - Search and book hotels
3. **Combined Search** - Search flights and hotels together

## 🔧 Configuration

### API Configuration
Edit `server.js` to modify:
- Rate limiting settings
- CORS configuration
- API endpoints
- Error handling

### Bot Configuration
Edit `bot.js` to modify:
- Bot commands
- Conversation flow
- Language translations
- Keyboard layouts

### Web Interface
Edit `index.html` to modify:
- UI styling
- Form validation
- API integration
- Result display

## 📊 Database Schema

### User Sessions
- `chat_id` - Telegram chat ID
- `state` - Current conversation state
- `language` - User's language preference
- `currency` - User's currency preference
- `search_data` - Search parameters

### Search History
- `user_id` - User identifier
- `search_type` - Type of search
- `parameters` - Search parameters
- `results` - Search results
- `timestamp` - Search timestamp

## 🔒 Security Features

- **Rate Limiting** - Prevent API abuse
- **Input Validation** - Sanitize user inputs
- **CORS Protection** - Control cross-origin requests
- **Error Handling** - Secure error messages
- **Token Management** - Secure API token handling

## 🧪 Testing

```bash
# Run tests
npm test

# Run linting
npm run lint

# Run with coverage
npm run test:coverage
```

## 📈 Performance Optimization

- **Caching** - Redis integration for fast responses
- **Compression** - Gzip compression for responses
- **Database Indexing** - Optimized queries
- **Rate Limiting** - Prevent server overload
- **Error Handling** - Graceful error recovery

## 🚀 Deployment

### Heroku
```bash
# Add Heroku remote
heroku git:remote -a your-app-name

# Deploy
git push heroku main
```

### Docker
```bash
# Build image
docker build -t global360world .

# Run container
docker run -p 3000:3000 global360world
```

### Environment Variables
Set the following environment variables:
- `PORT` - Server port
- `TRAVELPAYOUTS_TOKEN` - API token
- `BOT_TOKEN` - Telegram bot token
- `NODE_ENV` - Environment (production/development)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

## 🔄 Updates

### Version 1.0.0
- Initial release
- Basic flight and hotel search
- Telegram bot integration
- Web interface

### Planned Features
- Payment integration
- Booking management
- User accounts
- Advanced filtering
- Mobile app

## 📞 Contact

- **Email**: support@global360world.com
- **Website**: https://global360world.com
- **Telegram**: @Global360WorldBot

---

**Made with ❤️ by the Global360World Team** 