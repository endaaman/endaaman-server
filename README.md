## MEMO
- update SSL certs
  ```
  $ letsencrypt-auto certonly -a standalone --standalone-supported-challenges http-01 -d endaaman.me
  ```
- mariadb
  - set `bind-interface` to `0.0.0.0` in mariadb conf
  - allow external login to root

