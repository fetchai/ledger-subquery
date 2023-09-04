set -e

if [ ! -f /root/.fetchd/config/genesis.json ]; then
  echo "Genesis not found, configuring new setup"
  fetchd init node --chain-id test
  fetchd config keyring-backend test
  fetchd config chain-id test
  fetchd keys add validator
  fetchd add-genesis-account $(fetchd keys show validator -a) 1152997575000000000000000000stake
  fetchd gentx validator 100000000000000000000stake --keyring-backend test --chain-id test
  fetchd collect-gentxs
fi

fetchd start --rpc.laddr tcp://0.0.0.0:26657