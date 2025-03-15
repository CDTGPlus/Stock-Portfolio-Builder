FROM python:3

ENV PYTHONUNBUFFERED True
#Copy local code o he container image
ENV APP_HOME /app 
WORKDIR $APP_HOME
COPY . ./
#Install production dependencies
RUN pip install -r requirements.txt
RUN pip install gunicorn
#run web service
CMD exec gunicorn --bind $PORT --workers 1 --threads 8 --timeout 0 pf_app:app