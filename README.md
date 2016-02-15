Dalite NG
=========

Dalite NG is a Peer Instruction Tool for online learning platforms such as Open edX. It is implemented in Django as an [LTI](https://en.m.wikipedia.org/wiki/Learning_Tools_Interoperability) tool and should be compatible with most online learning platforms.  Dalite NG is a rewrite of the [Dalite tool][old-dalite] as a cleaner, Django-based LTI tool.

[old-dalite]: https://github.com/open-craft/edu8-dalite/

Setting up the development server
---------------------------------

1. Install the requirements (you probably want to set up a virtualenv first).

        $ pip install -r requirements.txt

2. Set up the database connection.  The default configuration is to use the
   MySQL database `dalite_ng` and the user `dalite`.  To set up the database,
   run these commands as the MySQL superuser:

        mysql> CREATE DATABASE dalite_ng;
        mysql> CREATE USER 'dalite'@'localhost' IDENTIFIED BY 'your password here';
        mysql> GRANT ALL PRIVILEGES ON dalite_ng.* TO dalite;

   The password can be passed in the environment:

        $ export DALITE_DB_PASSWORD='your password here'

3. Generate a secret key, e.g. using `tools/gen_secret_key.py`, an put it in
   `dalite/local_settings.py`.

4. Create the database tables and the superuser.

        $ ./manage.py migrate
        $ ./manage.py createsuperuser

5. Run the Django development server.

        $ ./manage.py runserver


Setting up a development server in an Open edX Devstack
-------------------------------------------------------
**Note:** This section contains security credentials: dalitepassword, alpha, beta, gamma.  Do **not** use these values on a system open to the Internet! Choose new ones.

* Clone dalite-ng into the "src" directory that comes with the edX Developer Stack. This is the one which gets mounted as /edx/src/ within vagrant; you may need to run `sudo chmod 0777 /edx/src` if you notice permissions issues.

* Start up the VM instance, and add the `dalite` Unix user.
```shell
$ vagrant up && vagrant ssh
vagrant@precise64:~$ sudo useradd -d /home/dalite -m -U -s /bin/bash dalite
```

* Set up MySQL for Dalite.  The default configuration is to use the MySQL database `dalite_ng` and the user `dalite`.
```shell
vagrant$ echo "CREATE DATABASE dalite_ng;
GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@localhost IDENTIFIED BY 'dalitepassword';
GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@'%' IDENTIFIED BY 'dalitepassword';" | mysql -u root
```
Check the output of MySQL in case there are any errors.

* Switch to the dalite Unix user and set up the build environment.

```shell
vagrant@precise64:~$ sudo su dalite
dalite$ cd
dalite$ echo "export DALITE_DB_PASSWORD='dalitepassword'" >> ~/.bashrc
dalite$ source ~/.bashrc
dalite$ ln -s /edx/src/dalite-ng dalite-ng
dalite$ virtualenv venv
dalite$ source venv/bin/activate
dalite$ cd dalite-ng
```

* Install the requirements
```shell
dalite$ pip install -r requirements.txt
```

* Generate a secret key using `tools/gen_secret_key.py`, and put it in `dalite/local_settings.py`.
```shell
dalite$ python tools/gen_secret_key.py >> dalite/local_settings.py
```

* Add the other settings.
```shell
dalite$ echo 'LTI_CLIENT_KEY = "alpha"' >> dalite/local_settings.py
dalite$ echo 'LTI_CLIENT_SECRET = "beta"' >> dalite/local_settings.py
dalite$ echo 'PASSWORD_GENERATOR_NONCE = "gamma"' >> dalite/local_settings.py
```

* Create the database tables and the superuser.
```shell
dalite$ ./manage.py migrate
dalite$ ./manage.py createsuperuser
```

* Start up the Django development server.
```shell
dalite$ ./manage.py runserver 0.0.0.0:8321
```

Usage Example: Configuring Dalite in edX Studio
-----------------------------------------------
This is an example of configuring Dalite as an LTI component in edX Studio. See the [official LTI component instructions](http://edx.readthedocs.org/projects/edx-partner-course-staff/en/latest/exercises_tools/lti_component.html) for further information.

* Go to Dalite at [http://192.168.33.10:8321/admin/](http://192.168.33.10:8321/admin/) and login with the superuser login you created. Note that we use the IP address 192.168.33.10 which is automatically setup for devstacks, so we don't have to fiddle around with port forwarding settings.

* Click "Questions" and create a couple of questions.

* Click "Assignments" and create a new assignment with identifier "assign1". Add the questions previously created to "Chosen questions" for the assignment.

* In another terminal, start up Studio.

```shell
vagrant ssh
vagrant@precise64:~$ sudo su edxapp
edxapp@precise64:~/edx-platform$ paver devstack studio
```

* Go to Studio at [http://localhost:8001/](http://localhost:8001/), login as staff@example.com, click "Advanced Settings", and set or add these settings:
  * Advanced Module List: `[ "lti" ]`.
  * LTI Passports: `[ "dalite:alpha:beta" ]`.  The second and third values here correspond to the `LTI_CLIENT_KEY` and `LTI_CLIENT_SECRET` chosen when setting up the Dalite server above.

Click "Save".

![module-list](https://cloud.githubusercontent.com/assets/945577/12212208/8f04b264-b61c-11e5-934b-8540e1d94da7.png)

![lti-passports](https://cloud.githubusercontent.com/assets/945577/12212222/b800b1ae-b61c-11e5-881b-9fa02c04c86a.png)

* Go to content, create a new unit, click `Advanced` → `LTI` to add a new LTI component, then set these settings on the new component:

  * Custom parameters (first): `assignment_id=assign1`
  * Custom parameters (second): `question_id=1`
  * Display Name: `Dalite 1`
  * LTI ID: `dalite`
  * LTI URL: `http://192.168.33.10/lti/`. The trailing `/` is required.

![lti-xblock-1](https://cloud.githubusercontent.com/assets/945577/12212288/8ef605ce-b61d-11e5-8dea-51620079e305.png)

![lti-xblock-2](https://cloud.githubusercontent.com/assets/945577/12212291/95f33af4-b61d-11e5-943b-afcb65c85ce1.png)

Click "Save". At this point, the Dalite question should be visible in Studio.

**Note:** it is important that the Studio and Dalite URL domains are different; here they are deliberately chosen to be "192.168.33.10" and "localhost".  This difference is necessary to prevent cookies clashing.

Running the tests
-----------------

The tests can be run with

```
dalite$ export PASSWORD_GENERATOR_NONCE=some_random_string
dalite$ make test
```

(If you have set `PASSWORD_GENERATOR_NONCE` in your settings you don't need the
export statement above.)

After the tests have finished, you can view the coverage report using:

```
dalite$ make coverage-report
```

Attributions
------------

The thumbs up and down icons were taken from the [Entypo pictograms by Daniel
Bruce][entypo].

[entypo]: http://www.entypo.com/
