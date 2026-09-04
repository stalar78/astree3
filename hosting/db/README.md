# HOSTING database layer

H2 provides `001_initial.sql` for the shared-hosting MySQL edition.

The schema contains:

- predefined pages;
- news;
- unified materials (`book`, `video`, `audio`, `article`);
- events/calendar dates;
- Lite Editor account storage reserved for H3;
- an explicit HOSTING schema-version marker.

The migration is intentionally idempotent for initial installation/re-application: tables are created only if absent and predefined page rows use `INSERT IGNORE`, so administrator-owned content is not overwritten.

No editor credential is seeded. H3 will add an explicit one-time bootstrap path using `password_hash` rather than repository credentials.

Candidate tables are explicitly excluded until the separately approved future Candidate Lite slice.
