# VocabTrainer

Application to simulate flash cards for learning vocabulary and other terms.

The Adaptive Mini Quiz feature tracks statistics on every user and tailors a 5 question mini quiz to the individual user with the words they are having the most trouble with.

<img width=600 src="https://github.com/Snackman8/VocabTrainer/raw/main/docs/ChooseQuiz.png">

<img width=600 src="https://github.com/Snackman8/VocabTrainer/raw/main/docs/TakeQuiz.png">

## Install Prerequisites

VocabTrainer depends on pyLinkJS.
Since both projects are evolving quickly, pylinkjs has not been uploaded to pypi.
To install pyLinkJS please perform the following commands to install from source

<pre>
git clone https://github.com/Snackman8/pyLinkJS
cd pyLinkJS
pip3 install .
</pre>

## Download the Code

To download the code, use the following command

`git clone https://github.com/Snackman8/VocabTrainer`

## Run the Application

To run with the application using developer authentication, use the command below (not recommended for live sites on the internet)

`python3 vocabTrainer_app.py --auth_method DevAuth`

The recommended usage for a live site is to use the GoogleOAuth2 authentication method.  The google clientid and secret should be sent to the application through the command line parameters.  For example if your Google OAuth2 Client ID was client123 and your Google OAuth2 Secret is secret123 and your domain name is www.somedomain.com 

`python3 vocabTrainer_app.py -- auth_method GoogleOAuth2 --oauth2_clientid client123 --oauth2_secret secret123 --oauth2_redirect_url https://www.somedomain.com`

## Usage information

<pre>
usage: vocabTrainer_app.py [-h] [--auth_method {GoogleOAuth2,DevAuth}] [--oauth2_clientid OAUTH2_CLIENTID] [--oauth2_redirect_url OAUTH2_REDIRECT_URL] [--oauth2_secret OAUTH2_SECRET] [--verbosity VERBOSITY]

optional arguments:
  -h, --help            show this help message and exit
  --auth_method {GoogleOAuth2,DevAuth}
                        authentication method
  --oauth2_clientid OAUTH2_CLIENTID
                        google oath2 client id
  --oauth2_redirect_url OAUTH2_REDIRECT_URL
                        google oath2 redirect url
  --oauth2_secret OAUTH2_SECRET
                        google oath2 secret
  --verbosity VERBOSITY
                        increase output verbosity
</pre>
