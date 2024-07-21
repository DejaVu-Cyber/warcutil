# warcutil

<b>warcutil</b> is a python command-line application that translates WARC files. Simply call:
    
    python warcutil file.warc

and it will output the translated WARC file.

To setup the python environment, run:

    python -m venv pyenv
    .\pyenv\Scripts\activate.ps1
    pip install warcio
    pip install beautifulsoup4
    pip install google-cloud-translate

To setup google cloud authentication, install the gcloud CLI, then run:

    gcloud auth application-default login

You may have to run

    gcloud init

first, but I'm not sure.