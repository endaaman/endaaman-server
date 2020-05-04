cd $(realpath $(dirname "$0"))
$HOME/go/bin/captainhook -configdir ./captainhook -listen-addr '0.0.0.0:45454' -echo
