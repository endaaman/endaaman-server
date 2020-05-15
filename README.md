## debug in local

```
$ SSL=0 docker-compose up --scale nginx-proxy-le-companion=0 -d --build
```

## make user service persistent
```
$ bash ./install-systemd-unit.sh
$ systemctl --user enable webhook.service
$ systemctl --user restart webhook.service
```

## make user service persistent

```
$ sudo loginctl enable-linger <USER NAME>
```
