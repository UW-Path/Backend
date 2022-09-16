echo 'Starting backend'
if [ ! -z $UWPATH_ENVIRONMENT ]
then
    echo 'Copying wallet'
    mkdir -p /code/Wallet_uwpathparallel
    echo $WALLET_CWALLET_SSO | base64 --decode > /code/Wallet_uwpathparallel/cwallet.sso
    echo $WALLET_EWALLET_PEM > /code/Wallet_uwpathparallel/ewallet.pem
    echo $WALLET_TNSNAMES_ORA > /code/Wallet_uwpathparallel/tnsnames.ora
    echo $WALLET_SQLNET_ORA > /code/Wallet_uwpathparallel/sqlnet.ora
fi
python manage.py migrate
python manage.py runserver 0.0.0.0:8000