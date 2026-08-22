# Requirements

## Planned Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Python
- FastAPI
- PostgreSQL
- Docker Compose
- Nginx
- SSL

## MVP Scope

Public:
- Home
- About / Saint Petersburg lodges
- Goals and principles
- Join / candidate application
- FAQ
- News
- Video
- Contacts
- Privacy/legal pages

Admin:
- Authentication
- Dashboard
- News management
- Video management
- Editable allowed page content
- Candidate application list/details/statuses

Candidate application:
- Form
- Photo upload
- Consent checkboxes
- Server-side validation
- Anti-spam protection
- Database persistence
- Private photo storage
- Structured email notification

## Candidate Flow

candidate
-> fills form
-> client validation
-> server validation
-> upload validation
-> anti-spam
-> database persistence
-> private photo storage
-> notification email

The database save must occur before the email notification attempt.
