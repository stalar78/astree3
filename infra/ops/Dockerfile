FROM postgres:16.4-alpine

COPY common.sh backup.sh restore.sh /usr/local/bin/
RUN chmod 0755 /usr/local/bin/common.sh /usr/local/bin/backup.sh /usr/local/bin/restore.sh
