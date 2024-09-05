python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

chmod a+x START.sh

name=`pwd | grep -o '[^/]*$'`

echo "#/bin/sh" > start.sh
echo "screen -S $name ./START.sh" >> start.sh

chmod a+x start.sh

echo "#/bin/sh" > use.sh
echo "screen -r $name" >> use.sh

chmod a+x use.sh
