#Base Image to use
FROM python:3.8.16

#Expose port 8080
EXPOSE 8080

#Optional - install git to fetch packages directly from github
RUN apt-get update && apt-get install -y git

#Copy Requirements.txt file into app directory
COPY requirements.txt random_link_collector/requirements.txt

#install all requirements in requirements.txt
RUN pip install -r random_link_collector/requirements.txt

#Copy all files in current directory into app directory
COPY . /random_link_collector

#Change Working Directory to app directory
WORKDIR /random_link_collector

#Run the application on port 8080
ENTRYPOINT ["streamlit", "run", "app/Submit.py", "--server.port=8080", "--server.address=0.0.0.0"]
