# Campus Drive Submission Checklist

## Completed Items

### A. GitHub Repository
- [x] Full project code organized
- [x] Clean folder structure
- [x] Proper .gitignore file
- [ ] Commit messages (to be done during git push)

### B. README File
- [x] Project overview
- [x] Steps to run the code
- [x] Environment setup instructions
- [x] Libraries used with justification
- [x] Sample data explanation
- [x] Usage guide
- [x] Troubleshooting section

### C. Demo Video (To Do)
- [ ] Record 5-10 minute walkthrough
- [ ] Show project setup
- [ ] Demo main features
- [ ] Explain approach
- [ ] Upload to YouTube/Drive

### D. Design Document
- [x] Problem statement
- [x] Architecture/flow diagrams
- [x] Tools & libraries explanation
- [x] Key logic explanation
- [x] Database schema
- [x] Security considerations

### E. Unit Tests
- [x] test_core.py - Core functionality tests
- [x] test_crawler.py - Crawler tests
- [x] test_storage.py - Storage tests
- [x] Test initialization (__init__.py)
- [x] pytest configuration

## Project Structure

```
website-scraper/
├── README.md              Comprehensive documentation
├── DESIGN.md              Design document
├── requirements.txt       Dependencies
├── .gitignore            Git ignore
├── app.py                Main application
├── config.py             Configuration
├── tests/                Unit tests
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_crawler.py
│   └── test_storage.py
├── scraper/              Core logic
│   ├── __init__.py
│   ├── core.py
│   ├── crawler.py
│   ├── storage.py
│   ├── scheduler.py
│   ├── notifier.py
│   ├── digest.py
│   └── dom_diff.py
├── web/                   Web interface         
│   ├── __init__.py
│   └── routes.py
└── templates/             HTML templates
    ├── base.html
    ├── index.html
    ├── dashboard.html
    ├── changes.html
    ├── domain_profile.html
    ├── page_profile.html
    └── edit_domain.html
```

## Demo Video Script

### Introduction (1 min)
- Project name and objective
- Key features overview
- Technologies used

### Setup & Configuration (2 min)
- Clone repository
- Install dependencies
- Configure email settings
- Run application

### Feature Demonstration (5 min)
1. **Add Website** (1 min)
   - Fill form
   - Configure settings
   - Start monitoring

2. **View Dashboard** (1 min)
   - Show statistics
   - Explain charts
   - Navigate sections

3. **Check Changes** (1 min)
   - Show detected changes
   - Explain change types
   - View similarity scores

4. **Domain Profile** (1 min)
   - Show domain analytics
   - Link classification
   - Change history

5. **Email Notifications** (1 min)
   - Show email alert
   - Explain digest system

### Technical Explanation (2 min)
- BFS crawling algorithm
- Change detection logic
- Scheduling system
- Data storage approach

### Conclusion (30 sec)
- Summary of features
- Future enhancements
- Thank you

## Git Commands for Submission

```bash
# Initialize repository
git init

# Add all files
git add .

# Commit with meaningful message
git commit -m "Initial commit: Daily Website Scraper with full-domain crawling and change detection"

# Add remote repository
git remote add origin https://github.com/yourusername/website-scraper.git

# Push to GitHub
git push -u origin main
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=scraper tests/

# Generate coverage report
pytest --cov=scraper --cov-report=html tests/
```

## Email Configuration

**Important**: Before demo, configure email in `config.py`:

```python
EMAIL_FROM = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Not regular password!
EMAIL_TO = "recipient@gmail.com"
```

**Get Gmail App Password**:
1. Google Account → Security
2. Enable 2-Step Verification
3. App passwords → Generate
4. Use generated password in config

## Evaluation Criteria Checklist

### Code Quality
- [x] Clean, readable code
- [x] Proper function/variable naming
- [x] Comments where necessary
- [x] Modular structure
- [x] Error handling

### Documentation Clarity
- [x] Comprehensive README
- [x] Design document
- [x] Code comments
- [x] Usage examples
- [x] API documentation (in code)

### Working Demo
- [x] Application runs successfully
- [x] All features functional
- [x] No critical bugs
- [ ] Demo video (to be recorded)

### Practical Understanding
- [x] Problem-solving approach documented
- [x] Design decisions explained
- [x] Trade-offs discussed
- [x] Best practices followed

### Testing Standards
- [x] Unit tests written
- [x] Test coverage
- [x] Edge cases considered
- [x] Mock testing for external dependencies

## Pre-Submission Checklist

- [x] README.md complete
- [x] DESIGN.md complete
- [x] Unit tests written
- [x] requirements.txt updated
- [x] .gitignore configured
- [x] Unnecessary files removed
- [ ] Demo video recorded
- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] Repository made public
- [ ] README links verified

## Files to Submit

1. **GitHub Repository Link**
   - https://github.com/yourusername/website-scraper

2. **Demo Video Link**
   - YouTube: [To be uploaded]
   - Google Drive: [Alternative]

3. **Documentation**
   - README.md (in repo)
   - DESIGN.md (in repo)

## Tips for Demo

1. **Prepare test websites**:
   - Use your own blog/website
   - Or use: https://example.com
   - Have 2-3 domains ready

2. **Show real changes**:
   - Modify a test page
   - Run scrape
   - Show detection

3. **Explain clearly**:
   - Speak slowly
   - Show code snippets
   - Explain logic

4. **Handle questions**:
   - Be ready to explain any part
   - Know your code well
   - Understand design decisions

## Key Points to Emphasize

1. **Full-stack skills**: Backend (Python) + Frontend (HTML/CSS/JS)
2. **System design**: Modular architecture, scalability considerations
3. **Best practices**: Testing, documentation, git workflow
4. **Problem-solving**: BFS algorithm, change detection, scheduling
5. **Production-ready**: Error handling, logging, configuration


