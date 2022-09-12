echo $WALLET_TNSNAMES_ORA > /code/Wallet_uwpathparallel/tnsnames.ora
echo $WALLET_SQLNET_ORA > /code/Wallet_uwpathparallel/sqlnet.ora
echo $WALLET_CWALLET_SSO > /code/Wallet_uwpathparallel/cwallet.sso
python manage.py migrate
python manage.py runserver 0.0.0.0:8000