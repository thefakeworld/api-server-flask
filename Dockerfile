FROM python:3.10

COPY . .

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
# RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
# gunicorn --config gunicorn-cfg.py run:app