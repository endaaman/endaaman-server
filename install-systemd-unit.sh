base=$HOME/.config/systemd/user/
mkdir -p $base

export DIR=$(realpath $(dirname "$0"))
cat ./files/captainhook.template.service | envsubst > $base/captainhook.service

echo OK
