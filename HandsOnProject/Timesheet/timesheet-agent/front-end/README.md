# Natural Language SQL Query Interface

A modern, intelligent web interface for querying databases using natural language. This React-based frontend provides an intuitive chat-like experience for business users to interact with their data without writing SQL.

## 🚀 Features

### **Natural Language Processing**

- Ask questions in plain English: _"Show me all employees who worked in May 2025"_
- Supports multiple query variations: _"Display staff hours"_, _"Get employee timesheet data"_
- Intelligent entity extraction for employees, dates, and business terms

### **Smart SQL Generation**

- **3-Tier Hybrid System**: Semantic understanding + Pattern matching + LLM fallback
- **Dynamic Employee Recognition**: Automatically detects new employees from database
- **Flexible Date Handling**: Understands "May 2025", "last month", "January to May 2025"
- **Context-Aware**: Maintains conversation context for follow-up questions

### **User-Friendly Interface**

- Clean, modern chat interface
- Real-time query processing with loading indicators
- SQL query display with syntax highlighting
- Interactive data tables with sorting and filtering
- Query history and favorites
- Error handling with helpful suggestions

### **Business Intelligence Ready**

- Employee timesheet analysis
- Project hours tracking
- Leave request management
- Billable vs non-billable hours reporting
- Client project summaries
- Custom date range analytics

## 🛠 Technology Stack

- **Frontend**: React 18 + Vite
- **Styling**: Modern CSS with responsive design
- **State Management**: React Context/Hooks
- **HTTP Client**: Axios for API communication
- **Data Visualization**: Interactive tables and charts
- **Development**: Hot Module Replacement (HMR) for fast development

## 🏗 Architecture

### **Frontend Components**

```
src/
├── components/
│   ├── ChatInterface/     # Main query interface
│   ├── QueryHistory/      # Previous queries
│   ├── DataTable/         # Results display
│   └── ErrorBoundary/     # Error handling
├── services/
│   ├── api.js            # Backend communication
│   └── queryProcessor.js # Query formatting
└── utils/
    ├── dateHelpers.js    # Date parsing utilities
    └── validators.js     # Input validation
```

### **Backend Integration**

- RESTful API communication with Python backend
- Real-time query processing and results streaming
- Conversation context management
- Error handling and user feedback

## 🎯 Use Cases

### **HR & Management**

- _"How many hours did each employee work last month?"_
- _"Show me pending leave requests"_
- _"Which employees have less than 80% billable hours?"_

### **Project Management**

- _"What projects has John worked on?"_
- _"Show client hours for May 2025"_
- _"List all timesheets from project Alpha"_

### **Financial Reporting**

- _"Calculate billable vs non-billable hours per project"_
- _"Show total revenue by client this quarter"_
- _"Employee utilization rates for the team"_

## 🚀 Getting Started

### **Prerequisites**

- Node.js 16+ and npm/yarn
- Python backend service running on port 8000

### **Installation**

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### **Environment Setup**

```bash
# Create .env file
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=SQL Query Assistant
```

## 🔧 Development

### **Available Scripts**

- `npm run dev` - Start development server with HMR
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint checks

### **Code Quality**

- ESLint configuration for React best practices
- Prettier for consistent code formatting
- Component-based architecture for maintainability

## 📊 Performance

- **Fast Query Processing**: 80% of queries handled without LLM (< 200ms)
- **Intelligent Caching**: Employee data and schema cached for performance
- **Optimized Rendering**: Virtual scrolling for large result sets
- **Responsive Design**: Works seamlessly on desktop and mobile

## 🔒 Security

- Input validation and sanitization
- SQL injection prevention through parameterized queries
- CORS configuration for secure API communication
- Error message sanitization to prevent information leakage

## 🤝 Contributing

This project uses modern React patterns and follows industry best practices:

- Functional components with hooks
- Context API for state management
- Custom hooks for reusable logic
- Component composition over inheritance

## 📈 Future Enhancements

- Real-time collaboration features
- Advanced data visualization charts
- Export functionality (CSV, Excel, PDF)
- Saved query templates
- Role-based access control
- Multi-language support

---

**Built with ❤️ for business users who want to unlock their data without learning SQL**
