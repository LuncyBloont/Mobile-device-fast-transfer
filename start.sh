spath="$0"
cd "$(dirname "${spath}")" || ( echo "cd fail" && exit )
echo cd "$(dirname "${spath}")"
python server.py
