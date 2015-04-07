Dalite NG
=========

Dalite NG is a rewrite of the [Dalite tool][1] as a cleaner, Django-based LTI
tool.

[1]: https://github.com/open-craft/edu8-dalite/

Setting up the development server
---------------------------------

1. Install the requirements (you probably want to set up a virtualenv first).

        $ pip install -r requirements.txt

2. Set up the database connection.  The default configuration is to use the
   MySQL database `dalite_ng` and the user `dalite`.  To set up the database,
   run these commands as the MySQL superuser:

        mysql> CREATE DATABASE dalite_ng;
        mysql> CREATE USER 'dalite' IDENTIFIED BY 'your password here';
        mysql> GRANT ALL PRIVILEGES ON dalite_ng.* TO dalite;

   The password can be passed in the environment:

        $ export DALITE_DB_PASSWORD='your password here'

3. Create the database tables and the superuser.

        $ ./manage.py migrate
        $ ./manage.py createsuperuser

4. Run the Django development server.

        $ ./manage.py runserver
