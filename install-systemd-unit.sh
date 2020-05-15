set -eu

DEST_DIR=$HOME/.config/systemd/user
DEST_PATH=$DEST_DIR/webhook.service
mkdir -p $DEST_DIR

export DIR=$(realpath $(dirname "$0"))
cat ./files/webhook.template.service | envsubst > $DEST_PATH

echo Wrote "$DEST_PATH"
