## debug in local

```
$ SSL=0 docker-compose up --scale nginx-proxy-le-companion=0 -d --build
```

## captainhook

```
$ ~/go/bin/captainhook -configdir . -listen-addr '0.0.0.0:45454'
```
