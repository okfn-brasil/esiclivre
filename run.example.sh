# Keys for IA: https://archive.org/account/s3.php
export ACCESS_KEY=xxxxxxxxxxxxxxxx
export SECRET_KEY=xxxxxxxxxxxxxxxx

echo "Abrindo monitor fantasma"
Xvfb :10 -ac &
export DISPLAY=:10
echo "Ativando virtualenv"
source env/bin/activate
echo "Rodando script"
python manage.py run
echo "Desativando virtualenv"
deactivate
echo "Matando monitor fantasma"
pkill Xvfb
echo "As vezes temos raposas zumbis... Quem sabe assim não mais"
killall firefox
