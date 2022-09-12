if [ "$GCP" = 'true' ]
then
    echo 'Copying wallet'
    echo $WALLET_TNSNAMES_ORA > /code/Wallet_uwpathparallel/tnsnames.ora
    echo $WALLET_SQLNET_ORA > /code/Wallet_uwpathparallel/sqlnet.ora
fi
python manage.py migrate
python manage.py runserver 0.0.0.0:8000