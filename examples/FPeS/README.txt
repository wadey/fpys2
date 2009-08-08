FPeS - Foto Purchase example Sytem 

This project exercises and demonstrates the FPyS library for accessing
the Amazon Flexible Payment System from Python applications.  It provides
users with the ability to select photos and purchase the ability to see 
and download full sized versions of those photos.  

The shopping cart and invoice system are weak, and users are created
on the fly with each new HTTP session.  This application is not meant 
as a full fledged e-commerce example, but rather as an example specifically
for the FPyS library. 

This is a TurboGears (http://www.turbogears.org) project. It was built
with TurboGears version 1.0.4b2.  It can be started by running the
start-fpes.py script.

The application is configured to use SQLite by default, but any
supported database may be configured in dev.cfg.

Three configuration properties must be configured in dev.cfg before
the application will run:
  aws_access_key_id: your Amazon Web Services access key
  secret_access_key:  the secret component of your AWS key
  default_caller_token:  a FPS token.  Install your own, or use the 
    create_caller_token.py script to generate this value.

