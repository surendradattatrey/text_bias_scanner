FROM dtr.midev.xxxx.com/rhel-ubi8/python-36

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3","main.py"]
