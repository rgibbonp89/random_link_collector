# Welcome to the Random Link Collector!

Sometimes I find links that I want to read later - this attempts to solve that problem with a little help from ChatGPT

### Setup and help

First, I assume you have a GCP account with `App Engine` and `Firebase` set up. If not, there are tons of guides to help you with this.

You can install all dependencies locally using:

```commandline
pipenv install requirements.txt
```

Create a `.keys` directory in the project root. In a file called `firebase.json` add your project service account info.
Create a `.env` file containing:

```bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
export FS_KEY="local path to firestore.json file"
export OPENAI_KEY="your OPENAI API key"
```

For local Docker tests run:
```commandline
docker build . -t streamlit-app
docker run -p 8080:8080 streamlit-app
```

To build and deploy a new version of the app run:
```commandline
gcloud app deploy app.yaml
```
