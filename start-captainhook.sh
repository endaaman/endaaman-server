cd $(realpath $(dirname "$0"))
$HOME/go/bin/captainhook -configdir . -listen-addr '0.0.0.0:45454' -echo
