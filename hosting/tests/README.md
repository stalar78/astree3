# HOSTING tests

HOSTING-specific contract and security checks are added incrementally.

H1 CI verifies the hosting frontend build and required package skeleton.

H2 adds `public_content_contract.php`, executed against a real MySQL service in `Hosting CI`. It verifies:

- only published predefined pages are public;
- draft news do not leak through list/detail APIs;
- unified material publication and type filtering;
- safe RuTube mapping for the legacy `/videos` public contract;
- published-only event/date filtering;
- bounded/validated query inputs;
- no write endpoints in the H2 public API;
- no seeded Lite Editor credential;
- candidate submission remains unavailable.

H3 will extend this area with authentication, CSRF, write-contract and upload tests.
