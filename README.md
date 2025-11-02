# Transaction Input App

A full-stack application for inputting transaction details including Date, Amount, Description, and Payment Type from a predefined list of categories.

## Technologies Used

- **Frontend**: React, TypeScript, Vite
- **Backend**: Spring Boot, Spring Data JPA, H2 Database
- **Build Tools**: Maven (for backend), npm (for frontend)

## Prerequisites

- Java 24 (or compatible version)
- Node.js and npm
- Maven (optional, as Maven wrapper is included)

## Installation

### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies (Maven will handle this automatically):
   ```
   mvn clean install
   ```

### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

## Running the Application

### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Run the Spring Boot application:
   ```
   mvn spring-boot:run
   ```
   Or use the Maven wrapper:
   ```
   ./mvnw spring-boot:run
   ```

### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Start the development server:
   ```
   npm run dev
   ```

The application will be accessible at:
- Backend API: http://localhost:8080
- Frontend: http://localhost:5173

## API Endpoints

- `GET /api/categories`: Retrieves the list of payment type categories
- `POST /api/transactions`: Saves a new transaction

## Database

The application uses an H2 in-memory database for data persistence. The H2 console is available at http://localhost:8080/h2-console for database inspection.

## Project Structure

- `backend/`: Spring Boot application
- `frontend/`: React application
- `categories.txt`: List of payment type categories
