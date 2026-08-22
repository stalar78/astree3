# Success Metric

Primary delivery success criterion: a production-ready site passes the approved acceptance criteria, including a complete end-to-end candidate application flow.

Candidate flow:
form -> validation -> secure persistence -> admin availability -> email notification

Email is not the source of truth for candidate applications. The database is the source of truth. The application must be persisted before email notification is attempted.
